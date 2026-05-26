import json
import re
from crewai import Crew, Process
from agents import (
    script_parser_agent,
    visual_designer_agent,
    audio_generator_agent,
    html_saver_agent,
)
from tasks import make_parse_task, make_visual_task, make_audio_task, make_save_task


def extract_json(text: str):
    """Extract JSON array from agent output."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("Could not parse JSON from parser output")


def extract_html(text: str):
    """Extract raw HTML from agent output."""
    text = re.sub(r"^```(?:html)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start = text.find("<!DOCTYPE")
    if start == -1:
        start = text.find("<html")
    end = text.rfind("</html>")
    if start != -1 and end != -1:
        return text[start:end + len("</html>")]
    return text


def run_pipeline():
    # Read the script from markdown file
    print("\n" + "="*60)
    print("Reading script from script.md...")
    print("="*60)
    try:
        with open("script.md", "r", encoding="utf-8") as f:
            raw_script = f.read()
    except FileNotFoundError:
        print("❌ Error: script.md not found in current directory.")
        return

    # STEP 1: Parse the script into sections
    print("\n" + "="*60)
    print("STEP 1: Parsing script into sections...")
    print("="*60)

    parse_task = make_parse_task(script_parser_agent, raw_script)
    parse_crew = Crew(
        agents=[script_parser_agent],
        tasks=[parse_task],
        process=Process.sequential,
        verbose=True,
        tracing=True,
    )
    parse_result = parse_crew.kickoff()
    sections = extract_json(str(parse_result))
    print(f"\n✅ Parsed {len(sections)} sections")

    # STEP 2: For each section, generate visual + audio + save
    for idx, section in enumerate(sections):
        print("\n" + "="*60)
        print(f"PROCESSING {section['section_id']}: {section['title']}")
        print("="*60)

        next_section_id = sections[idx + 1]['section_id'] if idx + 1 < len(sections) else ""

        # Visual generation
        visual_task = make_visual_task(visual_designer_agent, section)
        # Audio generation
        audio_task = make_audio_task(audio_generator_agent, section)

        section_crew = Crew(
            agents=[visual_designer_agent, audio_generator_agent],
            tasks=[visual_task, audio_task],
            process=Process.sequential,
            verbose=True,
            tracing=True,
        )
        section_crew.kickoff()

        html_content = extract_html(str(visual_task.output.raw))  # type: ignore

        # Save HTML with audio binding + next redirect
        save_task = make_save_task(
            html_saver_agent, section, html_content, next_section_id
        )
        save_crew = Crew(
            agents=[html_saver_agent],
            tasks=[save_task],
            process=Process.sequential,
            verbose=True,
            tracing=True,
        )
        save_crew.kickoff()

        print(f"✅ Completed {section['section_id']}")

    print("\n" + "="*60)
    print("🎉 ALL SECTIONS GENERATED!")
    print(f"Open output/{sections[0]['section_id']}.html in your browser.")
    print("="*60)


if __name__ == "__main__":
    run_pipeline()