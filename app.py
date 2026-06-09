"""
VA Creator — Streamlit Web UI
A beautiful interface for generating tutorial slides with progress tracking and redo support.
"""

import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import streamlit as st
from crewai import Crew, Process

# Must import config first to validate env
from config import MAX_PARALLEL_SECTIONS, logger
from project import (
    set_active_project,
    get_active_project,
    get_project_dir,
    get_index_path,
    audio_path,
    html_path,
    list_projects,
    slugify,
)
from agents import make_chunk_structurer_agent, make_visual_designer_agent, make_research_scriptwriter_agent
from tasks import make_chunking_task, make_visual_task, make_research_script_task
from tools import generate_audio_direct, save_html_direct
from chunker import split_script_into_chunks
from llm_runner import run_crew_with_retry
from slide_template import render_slide, parse_content, build_and_save_slide
from utils import (
    extract_json_object,
    extract_json_array,
    extract_html,
    save_sections_json,
    load_sections_json,
    is_completed,
    has_chunk_changed,
    mark_completed,
    generate_master_index,
    load_progress,
    save_progress,
    is_clean_hindi_audio,
    has_devanagari,
    devanagari_ratio,
)

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VA Creator — Tutorial Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: var(--background-color); color: var(--text-color); }
    .main-header {
        background: linear-gradient(135deg, rgba(0,212,255,0.06), rgba(167,139,250,0.06));
        border: 1px solid rgba(0,212,255,0.2);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .section-card {
        background: rgba(0,212,255,0.03);
        border: 1.5px solid rgba(0,212,255,0.15);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        transition: all 0.3s;
    }
    .section-card:hover {
        border-color: #00d4ff;
        box-shadow: 0 8px 30px rgba(0,212,255,0.15);
    }
    .status-complete { color: #00ff88; font-weight: 700; }
    .status-failed { color: #ff4444; font-weight: 700; }
    .status-pending { color: #ffaa00; font-weight: 700; }
    .status-running { color: #00d4ff; font-weight: 700; }
    .stat-box {
        background: rgba(167,139,250,0.05);
        border: 1px solid rgba(167,139,250,0.20);
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
    }
    .stat-val { font-size: 1.8rem; font-weight: 800; color: #a78bfa; }
    .stat-label { font-size: 0.75rem; color: var(--text-color); opacity: 0.75; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ──────────────────────────────────────────────────────
def _audio_exists(sid: str) -> bool:
    """Check if a valid audio file exists for a section."""
    mp3_path = audio_path(sid)
    return os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1000


def _video_exists(sid: str) -> bool:
    """Check if an HTML slide file exists for a section."""
    return os.path.exists(html_path(sid))


def init_session_state():
    if "pipeline_running" not in st.session_state:
        st.session_state.pipeline_running = False
    if "sections" not in st.session_state:
        st.session_state.sections = load_sections_json() or []
    if "chunks" not in st.session_state:
        st.session_state.chunks = []
    if "progress_log" not in st.session_state:
        st.session_state.progress_log = []
    if "audio_status" not in st.session_state:
        st.session_state.audio_status = {}
    if "video_status" not in st.session_state:
        st.session_state.video_status = {}
    if "section_status" not in st.session_state:
        # Load status from existing files
        st.session_state.section_status = {}
        if st.session_state.sections:
            for sec in st.session_state.sections:
                sid = sec["section_id"]
                audio_ok = _audio_exists(sid)
                video_ok = _video_exists(sid)
                st.session_state.audio_status[sid] = "complete" if audio_ok else "pending"
                st.session_state.video_status[sid] = "complete" if video_ok else "pending"
                if audio_ok and video_ok:
                    st.session_state.section_status[sid] = "complete"
                else:
                    st.session_state.section_status[sid] = "pending"


def _clear_project_session():
    """Clear per-project session data when switching/creating a project."""
    for key in ["sections", "chunks", "progress_log", "audio_status",
                "video_status", "section_status", "pipeline_running"]:
        if key in st.session_state:
            del st.session_state[key]


def render_project_gate():
    """Show the project create/open screen. Sets st.session_state.project_name."""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin:0; background:linear-gradient(135deg,#00d4ff,#a78bfa);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        🎬 VA Creator</h1>
        <p style="color:var(--text-color); opacity:0.75; margin:4px 0 0 0;">
        Start by naming your project. All slides and audio will be saved in a folder for that project.
        </p>
    </div>
    """, unsafe_allow_html=True)

    existing = list_projects()

    tab_new, tab_open = st.tabs(["✨ New Project", "📂 Open Existing"])

    with tab_new:
        st.markdown("### Create a new project")
        new_name = st.text_input(
            "Project name",
            placeholder="e.g. LangChain Customer Support Bot",
            key="new_project_name_input",
        )
        if new_name.strip():
            st.caption(f"Files will be saved in: `{os.path.join('output', slugify(new_name))}/`")
        if st.button("🚀 Create Project", type="primary", disabled=not new_name.strip()):
            slug = set_active_project(new_name)
            _clear_project_session()
            st.session_state.project_name = new_name.strip()
            st.session_state.project_slug = slug
            st.rerun()

    with tab_open:
        st.markdown("### Open an existing project")
        if existing:
            chosen = st.selectbox("Select a project folder", existing)
            if st.button("📂 Open Project"):
                set_active_project(chosen)
                _clear_project_session()
                st.session_state.project_name = chosen
                st.session_state.project_slug = chosen
                st.rerun()
        else:
            st.info("No existing projects yet. Create one in the 'New Project' tab.")


# ─── Project Gate ────────────────────────────────────────────────────────────
if "project_name" not in st.session_state:
    st.session_state.project_name = None

if not st.session_state.project_name:
    render_project_gate()
    st.stop()

# Re-apply active project on every run (project module state is process-global)
set_active_project(st.session_state.project_name)

init_session_state()


# ─── Helper Functions ────────────────────────────────────────────────────────

def get_script_content() -> str:
    """Get script content from file upload or default script.md."""
    script_path = os.path.join(os.path.dirname(__file__), "script.md")
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _fallback_section(chunk: dict, section_id: str) -> dict[str, Any]:
    """Build a section from pre-extracted chunk data when the LLM is unavailable."""
    spoken = chunk.get("spoken_text") or chunk.get("content", "")[:500]
    code_blocks = chunk.get("code_blocks", [])
    primary_code = code_blocks[0].get("code", "") if code_blocks else ""
    primary_lang = code_blocks[0].get("language", "") if code_blocks else ""
    return {
        "section_id": section_id,
        "title": chunk.get("heading", section_id),
        "audio_text": spoken,
        "visual": chunk.get("heading", ""),
        "code": primary_code,
        "code_language": primary_lang,
        "category": "code" if code_blocks else "concept",
    }


def structure_single_chunk(chunk: dict, section_id: str) -> dict[str, Any]:
    """Structure a single chunk using the LLM agent.
    Falls back to pre-extracted chunk data if the LLM fails (e.g. rate limit).
    """
    try:
        result, _task = run_crew_with_retry(
            make_chunk_structurer_agent,
            lambda agent: make_chunking_task(agent, chunk, section_id),
        )
    except Exception as e:
        logger.warning(f"LLM unavailable for {section_id} ({type(e).__name__}). Using pre-extracted fallback.")
        st.session_state.progress_log.append(f"⚠️ {section_id}: LLM rate-limited, used fallback text")
        return _fallback_section(chunk, section_id)

    try:
        section = extract_json_object(str(result))
        section["section_id"] = section_id

        # Validate audio_text — must be clean Hindi (Devanagari), no code/markdown.
        audio = section.get("audio_text", "")
        if not is_clean_hindi_audio(audio):
            spoken = chunk.get("spoken_text", "")
            # Prefer the source narration ONLY if it is itself Hindi; otherwise keep LLM output.
            if spoken and has_devanagari(spoken) and devanagari_ratio(spoken) >= devanagari_ratio(audio):
                section["audio_text"] = spoken
                logger.warning(f"Replaced audio_text for {section_id} with Hindi source narration")
            else:
                logger.warning(
                    f"audio_text for {section_id} is not clean Hindi "
                    f"(devanagari ratio={devanagari_ratio(audio):.2f}); keeping LLM output"
                )
                st.session_state.progress_log.append(
                    f"⚠️ {section_id}: audio_text may not be fully Hindi — check & Redo Audio if needed"
                )

        # Backfill code fields from the chunk if the LLM omitted them
        code_blocks = chunk.get("code_blocks", [])
        if code_blocks:
            if not section.get("code"):
                section["code"] = code_blocks[0].get("code", "")
            if not section.get("code_language"):
                section["code_language"] = code_blocks[0].get("language", "")
            section["category"] = "code"

        return section
    except Exception as e:
        logger.warning(f"Failed to parse chunk for {section_id}: {e}")
        return _fallback_section(chunk, section_id)


def process_single_section(section: dict, next_section_id: str) -> tuple[str, bool, str]:
    """Process a single section (visual + audio in PARALLEL, then save). Returns (section_id, success, message)."""
    sid = section["section_id"]
    proj_name = st.session_state.project_name  # capture before threads (session_state not thread-safe)

    def gen_video() -> str:
        """Generate slide content via LLM if not present, then render deterministically (thread-safe)."""
        if "slide_html" in section and section["slide_html"]:
            build_and_save_slide(section, section, next_section_id, proj_name)
            return "ok"
        _result, task = run_crew_with_retry(
            make_visual_designer_agent,
            lambda agent: make_visual_task(agent, section),
        )
        content = parse_content(str(task.output.raw))
        build_and_save_slide(section, content, next_section_id, proj_name)
        return "ok"

    def gen_audio() -> str:
        """Generate audio via Sarvam TTS (no session_state access — thread-safe)."""
        return generate_audio_direct(text=section["audio_text"], filename=sid)

    video_ok = False
    audio_ok = False
    errors: list[str] = []

    try:
        # Run video (LLM) and audio (TTS) concurrently
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_video = ex.submit(gen_video)
            f_audio = ex.submit(gen_audio)

            # Collect video result
            try:
                f_video.result()
                video_ok = True
            except Exception as e:
                errors.append(f"Video failed: {e}")

            # Collect audio result
            try:
                audio_result = f_audio.result()
                if "Error" in audio_result:
                    errors.append(f"Audio failed: {audio_result}")
                else:
                    audio_ok = True
            except Exception as e:
                errors.append(f"Audio failed: {e}")

        # Update session state in the MAIN thread (thread-safe)
        st.session_state.video_status[sid] = "complete" if video_ok else "failed"
        st.session_state.audio_status[sid] = "complete" if audio_ok else "failed"

        if video_ok and audio_ok:
            mark_completed(sid)
            return sid, True, "✅ Complete"

        return sid, False, "❌ " + " | ".join(errors)

    except Exception as e:
        return sid, False, f"❌ Error: {str(e)}"


def regenerate_audio_only(section_idx: int) -> tuple[bool, str]:
    """Regenerate ONLY the audio (TTS) for a section. Returns (success, message)."""
    sections = st.session_state.sections
    if section_idx >= len(sections):
        return False, "Invalid section index"

    section = sections[section_idx]
    sid = section["section_id"]

    # Delete existing audio file
    mp3_path = audio_path(sid)
    if os.path.exists(mp3_path):
        os.remove(mp3_path)

    try:
        result = generate_audio_direct(text=section["audio_text"], filename=sid)
        if "Error" in result:
            st.session_state.audio_status[sid] = "failed"
            st.session_state.progress_log.append(f"[Redo Audio] {sid}: {result}")
            return False, result

        st.session_state.audio_status[sid] = "complete"
        st.session_state.progress_log.append(f"[Redo Audio] {sid}: ✅ Audio regenerated")
        _refresh_combined_status(sid)
        return True, "✅ Audio regenerated"
    except Exception as e:
        st.session_state.audio_status[sid] = "failed"
        msg = f"❌ Error: {str(e)}"
        st.session_state.progress_log.append(f"[Redo Audio] {sid}: {msg}")
        return False, msg


def regenerate_video_only(section_idx: int) -> tuple[bool, str]:
    """Regenerate ONLY the video/HTML slide for a section. Returns (success, message)."""
    sections = st.session_state.sections
    if section_idx >= len(sections):
        return False, "Invalid section index"

    section = sections[section_idx]
    sid = section["section_id"]

    # Delete existing HTML file
    h_path = html_path(sid)
    if os.path.exists(h_path):
        os.remove(h_path)

    try:
        if "slide_html" in section and section["slide_html"]:
            next_id = sections[section_idx + 1]["section_id"] if section_idx + 1 < len(sections) else ""
            build_and_save_slide(section, section, next_id, st.session_state.project_name)
        else:
            # Generate slide content via LLM, then render deterministically
            _result, task = run_crew_with_retry(
                make_visual_designer_agent,
                lambda agent: make_visual_task(agent, section),
            )
            content = parse_content(str(task.output.raw))

            # Render + save (chain to next section)
            next_id = sections[section_idx + 1]["section_id"] if section_idx + 1 < len(sections) else ""
            build_and_save_slide(section, content, next_id, st.session_state.project_name)

        st.session_state.video_status[sid] = "complete"
        st.session_state.progress_log.append(f"[Redo Video] {sid}: ✅ Slide regenerated")
        _refresh_combined_status(sid)
        return True, "✅ Slide regenerated"
    except Exception as e:
        st.session_state.video_status[sid] = "failed"
        msg = f"❌ Error: {str(e)}"
        st.session_state.progress_log.append(f"[Redo Video] {sid}: {msg}")
        return False, msg


def _refresh_combined_status(sid: str) -> None:
    """Recompute the combined section status from audio + video sub-statuses."""
    audio_ok = st.session_state.audio_status.get(sid) == "complete"
    video_ok = st.session_state.video_status.get(sid) == "complete"

    if audio_ok and video_ok:
        st.session_state.section_status[sid] = "complete"
        progress = load_progress()
        if sid not in progress.get("completed", []):
            progress.setdefault("completed", []).append(sid)
            save_progress(progress)
    else:
        # Not fully complete anymore
        st.session_state.section_status[sid] = "pending"
        progress = load_progress()
        if sid in progress.get("completed", []):
            progress["completed"].remove(sid)
            save_progress(progress)


def redo_section(section_idx: int):
    """Redo a specific section completely — regenerate both audio and video."""
    sections = st.session_state.sections
    if section_idx >= len(sections):
        return

    sid = sections[section_idx]["section_id"]
    st.session_state.section_status[sid] = "running"

    regenerate_video_only(section_idx)
    regenerate_audio_only(section_idx)
    _refresh_combined_status(sid)


# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    # Active project header + switch button
    st.markdown(f"### 📁 Project\n**{st.session_state.project_name}**")
    st.caption(f"`{os.path.abspath(get_project_dir())}`")
    if st.button("🔄 Switch / New Project", use_container_width=True):
        _clear_project_session()
        st.session_state.project_name = None
        st.rerun()

    st.divider()
    st.markdown("## ⚙️ Settings")

    script_source = st.radio(
        "Script Source",
        ["📄 Use script.md", "📝 Paste Script", "📁 Upload .md File", "🔍 Topic + Web Research", "⚙️ Upload/Paste sections.json"],
        index=0,
    )

    # Placeholders for fields
    md_placeholder = (
        "### 🎬 SECTION 1: INTRODUCTION\n"
        "[Screen: Show the title slide \"Introduction to Python\"]\n"
        "> \"नमस्ते दोस्तों! आज हम सीखेंगे कि कैसे एक वेब ऐप बनाते हैं।\"\n\n"
        "### 🎬 SECTION 2: SETUP\n"
        "[Screen: Show terminal command box]\n"
        "> \"सबसे पहले हम streamlit लाइब्रेरी इंस्टॉल करेंगे।\"\n"
        "```bash\n"
        "pip install streamlit\n"
        "```"
    )

    json_placeholder = (
        "[\n"
        "  {\n"
        "    \"section_id\": \"section_01\",\n"
        "    \"title\": \"Introduction to Python\",\n"
        "    \"audio_text\": \"आज हम पायथन के बारे में सीखेंगे। पायथन एक बहुत ही सरल और शक्तिशाली प्रोग्रामिंग भाषा है।\",\n"
        "    \"visual\": \"- Introduction to Python\\n- Why choose Python\\n- Simplicity & readability\",\n"
        "    \"code\": \"print('Hello, World!')\",\n"
        "    \"code_language\": \"python\",\n"
        "    \"category\": \"intro\"\n"
        "  }\n"
        "]"
    )

    if script_source == "📝 Paste Script":
        script_text = st.text_area("Paste your markdown script:", placeholder=md_placeholder, height=300)
    elif script_source == "📁 Upload .md File":
        uploaded = st.file_uploader("Upload .md file", type=["md", "txt"])
        if uploaded:
            script_text = uploaded.read().decode("utf-8")
        else:
            script_text = ""
    elif script_source == "🔍 Topic + Web Research":
        topic_text = st.text_input("Enter a topic for the AI to research and generate sections for:")
        script_text = st.session_state.get("researched_script", "")
        if st.button("🔍 Generate Sections via Research", use_container_width=True, disabled=not topic_text.strip()):
            with st.spinner("Researching and generating sections JSON... (This takes a minute)"):
                try:
                    result, _task = run_crew_with_retry(
                        make_research_scriptwriter_agent,
                        lambda agent: make_research_script_task(agent, topic_text),
                    )
                    # Safely parse and format as pretty JSON
                    parsed_array = extract_json_array(str(result))
                    st.session_state.researched_script = json.dumps(parsed_array, indent=2, ensure_ascii=False)
                    script_text = st.session_state.researched_script
                    st.success("Sections JSON generated! You can review it below or run the pipeline.")
                except Exception as e:
                    st.error(f"Research failed: {e}")
        if script_text:
            script_text = st.text_area("Review/Edit Researched Sections JSON:", value=script_text, height=300)
    elif script_source == "⚙️ Upload/Paste sections.json":
        sections_input_type = st.radio("Provide sections.json:", ["Paste JSON", "Upload JSON"])
        if sections_input_type == "Paste JSON":
            raw_json_input = st.text_area("Paste your sections array here:", placeholder=json_placeholder, height=300)
        else:
            uploaded_json = st.file_uploader("Upload sections.json", type=["json"])
            raw_json_input = uploaded_json.read().decode("utf-8") if uploaded_json else ""
        
        script_text = "BYPASS_MODE"  # dummy value so the "Run Full Pipeline" button enables
    else:
        script_text = get_script_content()

    st.divider()
    st.markdown("### 🎛️ Pipeline Options")
    parallel_count = st.slider("Parallel Sections", 1, 6, MAX_PARALLEL_SECTIONS)

    st.divider()
    if st.session_state.pipeline_running:
        st.warning("⚠️ Pipeline marked as running.")
        if st.button("🛑 Reset Running State", use_container_width=True):
            st.session_state.pipeline_running = False
            st.rerun()

    if st.button("🗑️ Clear This Project's Output", type="secondary", use_container_width=True):
        import shutil
        proj_dir = get_project_dir()
        if os.path.exists(proj_dir):
            shutil.rmtree(proj_dir)
            os.makedirs(proj_dir, exist_ok=True)
        st.session_state.sections = []
        st.session_state.section_status = {}
        st.session_state.audio_status = {}
        st.session_state.video_status = {}
        st.session_state.progress_log = []
        st.session_state.pipeline_running = False
        st.rerun()


# ─── Main Content ───────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1 style="margin:0; background:linear-gradient(135deg,#00d4ff,#a78bfa);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
    🎬 {st.session_state.project_name}</h1>
    <p style="color:var(--text-color); opacity:0.75; margin:4px 0 0 0;">
    VA Creator &bull; AI-Powered Tutorial Video Generator &bull;
    <span style="color:#a78bfa;">Project: {st.session_state.project_name}</span>
    </p>
</div>
""", unsafe_allow_html=True)

# ─── Stats Row ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
total_sections = len(st.session_state.sections)
completed = sum(1 for s in st.session_state.section_status.values() if s == "complete")
failed = sum(1 for s in st.session_state.section_status.values() if s == "failed")
pending = total_sections - completed - failed

with col1:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{total_sections}</div><div class="stat-label">Total Sections</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-box"><div class="stat-val" style="color:#00ff88">{completed}</div><div class="stat-label">Completed</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stat-box"><div class="stat-val" style="color:#ff4444">{failed}</div><div class="stat-label">Failed</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="stat-box"><div class="stat-val" style="color:#ffaa00">{pending}</div><div class="stat-label">Pending</div></div>', unsafe_allow_html=True)

st.markdown("")

# ─── Action Buttons ──────────────────────────────────────────────────────────
btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 2])

with btn_col1:
    run_full = st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True,
                         disabled=st.session_state.pipeline_running or not script_text)

with btn_col2:
    run_pending = st.button("▶️ Run Pending Only", use_container_width=True,
                            disabled=st.session_state.pipeline_running or total_sections == 0)

with btn_col3:
    if total_sections > 0:
        index_path = get_index_path()
        if os.path.exists(index_path):
            if st.button("🌐 Open Slides", use_container_width=True):
                os.startfile(os.path.abspath(index_path))
        else:
            st.button("🌐 Open Slides", disabled=True, use_container_width=True)

# ─── Pipeline Execution ─────────────────────────────────────────────────────
if run_full and script_text:
    st.session_state.pipeline_running = True
    st.session_state.progress_log = []

    try:
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🔄 Pipeline Running...")

            if script_source in ["⚙️ Upload/Paste sections.json", "🔍 Topic + Web Research"]:
                with st.status("⚙️ Loading sections from JSON...", expanded=True) as status:
                    json_to_load = raw_json_input if script_source == "⚙️ Upload/Paste sections.json" else script_text
                    if not json_to_load.strip():
                        st.error("No JSON provided!")
                        st.stop()
                    try:
                        sections = extract_json_array(json_to_load)
                        if not isinstance(sections, list):
                            st.error("Invalid JSON format. Expected an array of sections.")
                            st.stop()
                        st.session_state.sections = sections
                        save_sections_json(sections)

                        # Initialize status
                        for sec in sections:
                            sid = sec.get("section_id", "unknown")
                            st.session_state.audio_status[sid] = "pending"
                            st.session_state.video_status[sid] = "pending"
                            st.session_state.section_status[sid] = "pending"
                        status.update(label=f"⚙️ Loaded {len(sections)} sections directly from JSON", state="complete")
                    except Exception as e:
                        st.error(f"Invalid JSON: {e}")
                        st.stop()
            else:
                # Step 1: Chunk
                with st.status("📦 Splitting script into chunks...", expanded=True) as status:
                    chunks = split_script_into_chunks(script_text)
                    st.session_state.chunks = chunks
                    st.write(f"✓ Created **{len(chunks)}** chunks")
                    status.update(label=f"📦 Split into {len(chunks)} chunks", state="complete")

                # Step 2: Structure
                with st.status("🧠 Structuring sections with AI...", expanded=True) as status:
                    sections = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i, chunk in enumerate(chunks):
                        section_id = f"section_{i+1:02d}"
                        status_text.text(f"Processing chunk {i+1}/{len(chunks)}: {chunk['heading']}")

                        section = structure_single_chunk(chunk, section_id)
                        sections.append(section)

                        progress_bar.progress((i + 1) / len(chunks))
                        time.sleep(1.5)  # throttle to respect NVIDIA rate limits

                    st.session_state.sections = sections
                    save_sections_json(sections)

                    # Initialize status
                    for sec in sections:
                        sid = sec["section_id"]
                        audio_ok = _audio_exists(sid)
                        video_ok = _video_exists(sid)
                        st.session_state.audio_status[sid] = "complete" if audio_ok else "pending"
                        st.session_state.video_status[sid] = "complete" if video_ok else "pending"
                        if audio_ok and video_ok:
                            st.session_state.section_status[sid] = "complete"
                        else:
                            st.session_state.section_status[sid] = "pending"

                    status.update(label=f"🧠 Structured {len(sections)} sections", state="complete")

            # Step 3: Generate slides
            with st.status(f"🎨 Generating {len(sections)} slides...", expanded=True) as status:
                progress_bar2 = st.progress(0)
                status_text2 = st.empty()
                completed_count = 0

                for idx, section in enumerate(sections):
                    sid = section["section_id"]
                    if is_completed(sid):
                        st.session_state.section_status[sid] = "complete"
                        st.session_state.audio_status[sid] = "complete"
                        st.session_state.video_status[sid] = "complete"
                        completed_count += 1
                        progress_bar2.progress(completed_count / len(sections))
                        continue

                    st.session_state.section_status[sid] = "running"
                    status_text2.text(f"🎨 [{idx+1}/{len(sections)}] {sid}: {section['title']}")

                    next_id = sections[idx + 1]["section_id"] if idx + 1 < len(sections) else ""
                    _, success, msg = process_single_section(section, next_id)

                    if success:
                        st.session_state.section_status[sid] = "complete"
                    else:
                        st.session_state.section_status[sid] = "failed"

                    st.session_state.progress_log.append(f"{sid}: {msg}")
                    completed_count += 1
                    progress_bar2.progress(completed_count / len(sections))

                # Generate master index
                generate_master_index(sections, st.session_state.project_name)
                status.update(label=f"🎨 Generated {len(sections)} slides", state="complete")

        st.success("🎉 Pipeline complete! Open the slides using the button above. "
                   "Any sections that failed can be retried individually below.")
        st.balloons()

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        st.error(f"⚠️ Pipeline stopped: {type(e).__name__} — {e}. "
                 f"Your progress is saved. Use 'Run Pending Only' or the per-section redo buttons to continue.")
    finally:
        st.session_state.pipeline_running = False

elif run_pending and total_sections > 0:
    st.session_state.pipeline_running = True
    sections = st.session_state.sections

    try:
        with st.status("▶️ Processing pending sections...", expanded=True) as status:
            pending_sections = [
                (idx, sec) for idx, sec in enumerate(sections)
                if st.session_state.section_status.get(sec["section_id"]) != "complete"
            ]

            if not pending_sections:
                st.write("All sections already complete!")
            else:
                progress_bar = st.progress(0)
                for i, (idx, section) in enumerate(pending_sections):
                    sid = section["section_id"]
                    st.session_state.section_status[sid] = "running"
                    st.write(f"Processing {sid}: {section['title']}...")

                    next_id = sections[idx + 1]["section_id"] if idx + 1 < len(sections) else ""
                    _, success, msg = process_single_section(section, next_id)

                    if success:
                        st.session_state.section_status[sid] = "complete"
                    else:
                        st.session_state.section_status[sid] = "failed"

                    st.session_state.progress_log.append(f"{sid}: {msg}")
                    progress_bar.progress((i + 1) / len(pending_sections))

                generate_master_index(sections, st.session_state.project_name)
                status.update(label="▶️ Pending sections processed", state="complete")
    except Exception as e:
        logger.error(f"Run-pending error: {e}")
        st.error(f"⚠️ Stopped: {type(e).__name__} — {e}. Progress saved; try again.")
    finally:
        st.session_state.pipeline_running = False

    st.rerun()

# ─── Sections Grid ───────────────────────────────────────────────────────────
if st.session_state.sections:
    st.markdown("---")
    st.markdown("### 📋 Sections")
    st.caption("Each section has independent **🎙️ Audio** and **🎬 Video (slide)** generation. "
               "Use the dedicated redo buttons to regenerate just one part.")

    status_map = {
        "complete": "✅",
        "failed": "❌",
        "pending": "⏳",
        "running": "🔄",
    }

    for idx, section in enumerate(st.session_state.sections):
        sid = section["section_id"]
        audio_st = st.session_state.audio_status.get(sid, "pending")
        video_st = st.session_state.video_status.get(sid, "pending")

        audio_icon = status_map.get(audio_st, "⏳")
        video_icon = status_map.get(video_st, "⏳")

        with st.container():
            col_info, col_audio, col_video = st.columns([3, 3.5, 3])

            # ── Section info ──
            with col_info:
                st.markdown(f"**{sid}** — {section['title']}")
                st.caption(
                    f"Category: {section.get('category', 'N/A')} • "
                    f"{len(section.get('audio_text', '').split())} words"
                )

            # ── Audio column ──
            with col_audio:
                st.markdown(f"**{audio_icon} Audio**")
                a_path = audio_path(sid)
                if _audio_exists(sid):
                    st.audio(a_path, format="audio/mp3")
                else:
                    st.caption("No audio yet")

                if st.button("🎙️ Redo Audio", key=f"redo_audio_{sid}",
                             disabled=st.session_state.pipeline_running,
                             use_container_width=True):
                    with st.spinner(f"Regenerating audio for {sid}..."):
                        regenerate_audio_only(idx)
                    st.rerun()

            # ── Video column ──
            with col_video:
                st.markdown(f"**{video_icon} Video (slide)**")
                v_path = html_path(sid)
                if _video_exists(sid):
                    if st.button("🔗 Open slide", key=f"open_slide_{sid}", use_container_width=True):
                        os.startfile(os.path.abspath(v_path))
                else:
                    st.caption("No slide yet")

                if st.button("🎬 Redo Video", key=f"redo_video_{sid}",
                             disabled=st.session_state.pipeline_running,
                             use_container_width=True):
                    with st.spinner(f"Regenerating slide for {sid}..."):
                        regenerate_video_only(idx)
                        generate_master_index(st.session_state.sections, st.session_state.project_name)
                    st.rerun()

            # ── Edit Section Content ──
            with st.expander("✏️ Edit Section Content", expanded=False):
                edit_title = st.text_input("Title", value=section.get("title", ""), key=f"edit_title_{sid}")
                
                categories = ["intro", "concept", "code", "setup", "demo", "summary"]
                current_cat = section.get("category", "concept")
                cat_index = categories.index(current_cat) if current_cat in categories else 1
                edit_category = st.selectbox(
                    "Category",
                    categories,
                    index=cat_index,
                    key=f"edit_category_{sid}"
                )
                
                edit_audio_text = st.text_area("Audio Text (Hindi Devanagari)", value=section.get("audio_text", ""), key=f"edit_audio_text_{sid}", height=100)
                
                visual_val = section.get("visual") or section.get("visual_brief") or ""
                edit_visual = st.text_area("Visual Brief / Description (English)", value=visual_val, key=f"edit_visual_{sid}", height=100)
                
                edit_code = st.text_area("Code (optional)", value=section.get("code", ""), key=f"edit_code_{sid}", height=100)
                edit_code_lang = st.text_input("Code Language", value=section.get("code_language", ""), key=f"edit_code_lang_{sid}")
                
                # Advanced direct HTML/CSS edit (if slide has already been generated)
                edit_html = ""
                edit_css = ""
                has_slide_html = ("slide_html" in section and bool(section["slide_html"])) or ("visual_html" in section and bool(section["visual_html"]))
                current_slide_html = section.get("slide_html") or section.get("visual_html") or ""
                
                if has_slide_html:
                    st.markdown("---")
                    st.caption("🛠️ **Direct Presentation Code Tweaks (Optional)**")
                    edit_html = st.text_area("Direct HTML layout code", value=current_slide_html, key=f"edit_html_{sid}", height=150)
                    edit_css = st.text_area("Direct custom CSS code", value=section.get("custom_css", ""), key=f"edit_css_{sid}", height=80)
                
                # Action buttons
                btn_save_col1, btn_save_col2 = st.columns(2)
                
                with btn_save_col1:
                    if st.button("💾 Save & Regenerate (via AI)", key=f"save_ai_{sid}", use_container_width=True, disabled=st.session_state.pipeline_running):
                        # 1. Update sections data
                        section["title"] = edit_title
                        section["category"] = edit_category
                        section["audio_text"] = edit_audio_text
                        section["visual"] = edit_visual
                        section["visual_brief"] = edit_visual
                        section["code"] = edit_code
                        section["code_language"] = edit_code_lang
                        
                        # Remove generated slide elements so LLM regenerates
                        if "slide_html" in section:
                            del section["slide_html"]
                        if "visual_html" in section:
                            del section["visual_html"]
                        if "custom_css" in section:
                            del section["custom_css"]
                        
                        st.session_state.sections[idx] = section
                        save_sections_json(st.session_state.sections)
                        
                        # 2. Run regeneration
                        with st.spinner("Regenerating slide and audio via AI..."):
                            regenerate_audio_only(idx)
                            regenerate_video_only(idx)
                            generate_master_index(st.session_state.sections, st.session_state.project_name)
                        
                        st.success(f"✓ Section {sid} successfully regenerated!")
                        st.rerun()
                
                with btn_save_col2:
                    if st.button("⚡ Save & Re-render (Instant)", key=f"save_instant_{sid}", use_container_width=True, disabled=st.session_state.pipeline_running):
                        # 1. Update sections data
                        section["title"] = edit_title
                        section["category"] = edit_category
                        section["audio_text"] = edit_audio_text
                        section["visual"] = edit_visual
                        section["visual_brief"] = edit_visual
                        section["code"] = edit_code
                        section["code_language"] = edit_code_lang
                        
                        # If slide_html is edited directly, save it
                        if has_slide_html:
                            section["slide_html"] = edit_html
                            section["visual_html"] = edit_html
                            section["custom_css"] = edit_css
                        
                        st.session_state.sections[idx] = section
                        save_sections_json(st.session_state.sections)
                        
                        with st.spinner("Instantly re-rendering slide & audio..."):
                            regenerate_audio_only(idx)
                            
                            next_id = st.session_state.sections[idx + 1]["section_id"] if idx + 1 < len(st.session_state.sections) else ""
                            build_and_save_slide(section, section, next_id, st.session_state.project_name)
                            
                            st.session_state.video_status[sid] = "complete"
                            _refresh_combined_status(sid)
                            
                            generate_master_index(st.session_state.sections, st.session_state.project_name)
                        
                        st.success(f"✓ Section {sid} updated instantly!")
                        st.rerun()

        st.divider()

# ─── Progress Log ───────────────────────────────────────────────────────────
if st.session_state.progress_log:
    with st.expander("📜 Progress Log", expanded=False):
        for log_entry in reversed(st.session_state.progress_log[-50:]):
            st.text(log_entry)

# ─── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#666; font-size:0.8rem;'>"
    "VA Creator v2.0 — Powered by CrewAI + NVIDIA NIM + Sarvam AI TTS"
    "</p>",
    unsafe_allow_html=True,
)
