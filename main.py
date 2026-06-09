"""
VA Creator — AI-Powered Tutorial Video Generator
Main pipeline entrypoint with CLI interface.
Run with: python main.py (CLI) or streamlit run app.py (UI)
"""

import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import typer
from crewai import Crew, Process

from agents import make_chunk_structurer_agent, make_visual_designer_agent
from tasks import make_chunking_task, make_visual_task
from tools import generate_audio_direct, save_html_direct
from chunker import split_script_into_chunks
from llm_runner import run_crew_with_retry
from project import set_active_project, get_active_project, get_project_dir, get_index_path
from slide_template import parse_content, build_and_save_slide
from utils import (
    extract_json_object,
    extract_html,
    save_sections_json,
    load_sections_json,
    is_completed,
    has_chunk_changed,
    mark_completed,
    generate_master_index,
    load_progress,
    is_clean_hindi_audio,
    has_devanagari,
    devanagari_ratio,
)
from config import MAX_PARALLEL_SECTIONS

logger = logging.getLogger("va_creator.main")
app = typer.Typer(help="VA Creator — AI-Powered Tutorial Video Generator")


def _active_project_name() -> str:
    """Human-readable project name for footers/index (uses the active slug)."""
    return get_active_project() or ""


def print_progress(current: int, total: int, label: str = "") -> None:
    """Display a progress bar in the terminal."""
    bar_len = 40
    filled = int(bar_len * current / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    sys.stdout.write(f"\r[{bar}] {current}/{total} {label}")
    sys.stdout.flush()
    if current == total:
        print()


def validate_audio_text(audio_text: str, chunk: dict) -> str:
    """Ensure audio_text is clean Hindi (Devanagari). Fall back to Hindi source narration if needed."""
    if is_clean_hindi_audio(audio_text):
        return audio_text
    spoken = chunk.get("spoken_text", "")
    if spoken and has_devanagari(spoken) and devanagari_ratio(spoken) >= devanagari_ratio(audio_text):
        logger.warning("audio_text not clean Hindi; using Hindi source narration")
        return spoken
    logger.warning(
        f"audio_text may not be fully Hindi (devanagari ratio={devanagari_ratio(audio_text):.2f}); keeping LLM output"
    )
    return audio_text


def structure_chunks_into_sections(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run chunk_structurer agent on each chunk to produce final sections.
    Uses content hashing to skip unchanged chunks.
    """
    cached = load_sections_json()
    progress = load_progress()

    # If cache exists and matches chunk count, check for changes
    if cached and len(cached) == len(chunks):
        all_same = all(
            not has_chunk_changed(f"section_{i+1:02d}", chunks[i].get("hash", ""))
            for i in range(len(chunks))
        )
        if all_same:
            logger.info(f"✅ All {len(cached)} sections unchanged (using cache)")
            print(f"✅ Loaded {len(cached)} cached sections from sections.json")
            return cached

    sections: list[dict[str, Any]] = []
    print(f"\n📋 Structuring {len(chunks)} chunks into sections...")

    for i, chunk in enumerate(chunks):
        section_id = f"section_{i+1:02d}"
        chunk_hash = chunk.get("hash", "")

        # Skip if this specific chunk hasn't changed and we have cached data
        if cached and i < len(cached) and not has_chunk_changed(section_id, chunk_hash):
            sections.append(cached[i])
            print_progress(i + 1, len(chunks), f"chunk {i+1} (cached)")
            continue

        result, _task = run_crew_with_retry(
            make_chunk_structurer_agent,
            lambda agent: make_chunking_task(agent, chunk, section_id),
        )
        try:
            section = extract_json_object(str(result))
            section["section_id"] = section_id

            # Validate and fix audio_text
            section["audio_text"] = validate_audio_text(section.get("audio_text", ""), chunk)

            # Backfill code fields from the chunk if the LLM omitted them
            code_blocks = chunk.get("code_blocks", [])
            if code_blocks:
                if not section.get("code"):
                    section["code"] = code_blocks[0].get("code", "")
                if not section.get("code_language"):
                    section["code_language"] = code_blocks[0].get("language", "")
                section["category"] = "code"

            sections.append(section)
        except Exception as e:
            logger.warning(f"Failed to parse chunk {i+1}: {e}")
            spoken = chunk.get("spoken_text", chunk["content"][:500])
            code_blocks = chunk.get("code_blocks", [])
            sections.append({
                "section_id": section_id,
                "title": chunk["heading"],
                "audio_text": spoken,
                "visual": chunk["heading"],
                "code": code_blocks[0].get("code", "") if code_blocks else "",
                "code_language": code_blocks[0].get("language", "") if code_blocks else "",
                "category": "code" if code_blocks else "concept",
            })
        print_progress(i + 1, len(chunks), f"chunk {i+1}")

    save_sections_json(sections)
    print(f"💾 Saved sections.json ({len(sections)} sections)")
    return sections


def process_section(section: dict[str, Any], next_section_id: str, chunk_hash: str = "") -> bool:
    """Generate visual + audio for a single section, then save.
    Audio and HTML saving are done directly (no LLM needed).
    Visual design still uses the LLM agent.
    Returns True on success, False on failure.
    """
    sid = section["section_id"]

    if is_completed(sid) and not has_chunk_changed(sid, chunk_hash):
        logger.info(f"⏭️  {sid} already done, skipping")
        return True

    def gen_visual() -> dict:
        """Generate slide content JSON via LLM agent."""
        _result, task = run_crew_with_retry(
            make_visual_designer_agent,
            lambda agent: make_visual_task(agent, section),
        )
        content = parse_content(str(task.output.raw))
        if not content or ("slide_html" not in content and "visual_html" not in content):
            raise ValueError("LLM Visual Designer returned empty or invalid slide content.")
        
        # Save generated slide content back to the section dict
        section["slide_html"] = content.get("slide_html") or content.get("visual_html") or ""
        section["custom_css"] = content.get("custom_css") or ""
        return content

    def gen_audio() -> str:
        """Generate audio directly (no LLM needed)."""
        return generate_audio_direct(
            text=section["audio_text"],
            filename=section["section_id"],
        )

    # Parallel: visual (LLM) + audio (direct API call)
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_visual = ex.submit(gen_visual)
        f_audio = ex.submit(gen_audio)
        content = f_visual.result()
        audio_result = f_audio.result()

    if "Error" in audio_result:
        logger.error(f"Audio failed for {sid}: {audio_result}")

    # Render + save slide deterministically from the structured content
    build_and_save_slide(section, content, next_section_id, _active_project_name())

    mark_completed(sid, chunk_hash)
    return True


def run_pipeline(script_path: str, project: str) -> None:
    """Execute the full generation pipeline for a named project."""
    set_active_project(project)
    logger.info(f"Project '{project}' → {get_project_dir()}")

    if not os.path.exists(script_path):
        logger.error(f"❌ Script file not found: {script_path}")
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        raw_script = f.read()

    if len(raw_script.strip()) < 50:
        logger.error("❌ Script file is too short or empty")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🚀 TUTORIAL GENERATOR — Advanced Pipeline")
    print("=" * 60)

    # STEP 1: Chunk
    print("\n[1/3] Pre-splitting script into chunks...")
    chunks = split_script_into_chunks(raw_script)
    print(f"   ✓ Created {len(chunks)} chunks")

    # STEP 2: Structure
    print("\n[2/3] Structuring chunks into sections...")
    sections = structure_chunks_into_sections(chunks)

    # STEP 3: Generate visuals + audio (parallel across sections)
    print(f"\n[3/3] Generating {len(sections)} slides (max {MAX_PARALLEL_SECTIONS} parallel)...")

    def process_with_index(args: tuple) -> tuple[int, bool]:
        idx, section, next_id, chunk_hash = args
        try:
            success = process_section(section, next_id, chunk_hash)
            return idx, success
        except Exception as e:
            logger.error(f"❌ Error processing {section['section_id']}: {e}")
            return idx, False

    tasks = []
    for idx, section in enumerate(sections):
        next_id = sections[idx + 1]["section_id"] if idx + 1 < len(sections) else ""
        chunk_hash = chunks[idx].get("hash", "") if idx < len(chunks) else ""
        tasks.append((idx, section, next_id, chunk_hash))

    completed_count = 0
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_SECTIONS) as executor:
        futures = {executor.submit(process_with_index, t): t for t in tasks}
        for future in as_completed(futures):
            idx, success = future.result()
            completed_count += 1
            section = sections[idx]
            status = "✅" if success else "❌"
            print(f"  {status} [{completed_count}/{len(sections)}] {section['section_id']}: {section['title']}")

    # Save the updated sections list containing generated slide_html/custom_css
    save_sections_json(sections)

    # STEP 4: Master index
    index_path = generate_master_index(sections, project)
    print(f"\n🏠 Master index: {index_path}")

    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETE!")
    print(f"📂 Open: {os.path.abspath(index_path)}")
    print("=" * 60)


@app.command()
def main(
    script: str = typer.Option(
        "script.md",
        "--script", "-s",
        help="Path to the markdown tutorial script file",
    ),
    project: str = typer.Option(
        None,
        "--project", "-n",
        help="Project name. Output is saved in output/<project>/. Prompts if not given.",
    ),
    parallel: int = typer.Option(
        None,
        "--parallel", "-p",
        help="Max parallel section processing (default: 2)",
    ),
):
    """
    VA Creator — Generate animated tutorial slides with Hindi audio from a markdown script.

    For the web UI, run: streamlit run app.py
    """
    if not project:
        project = typer.prompt("📁 Enter a project name")

    if parallel:
        import config
        config.MAX_PARALLEL_SECTIONS = parallel

    run_pipeline(script_path=script, project=project)


if __name__ == "__main__":
    app()
