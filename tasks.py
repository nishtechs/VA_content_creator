from crewai import Task

HTML_TEMPLATE_REFERENCE = """
Use this exact design system:
- Dark background: #0a0e27 with radial gradient orbs (cyan #00d4ff & purple #a78bfa)
- Font: Poppins (400, 600, 700, 800) and JetBrains Mono
- Grid overlay, animated floating orbs
- Badge with cyan border at top
- Large title with gradient highlight span
- Card grid (step-card / tech-card) with hover animations (translateY -8px)
- Step numbers in circular cyan gradient badges
- Disclaimer box with purple accent
- Hidden <audio id="audioPlayer" autoplay> element
- Responsive @media (max-width:768px) rules
- Auto-play script with fallback on user interaction
- cursor:none !important on all elements
"""


def make_parse_task(agent, raw_script: str):
    return Task(
        description=(
            f"Parse the following tutorial script into a JSON array of sections. "
            f"Each section must have: section_id (e.g., 'section_1'), title, "
            f"audio_text (clean Hindi/Hinglish narration only, no code, no stage directions), "
            f"and visual_brief (description of visuals, code, key points to show on screen).\n\n"
            f"SCRIPT:\n{raw_script}\n\n"
            f"Return ONLY valid JSON array, no markdown fences."
        ),
        expected_output="A JSON array of section objects with section_id, title, audio_text, visual_brief.",
        agent=agent,
    )


def make_visual_task(agent, section_data: dict, context_task=None):
    return Task(
        description=(
            f"Create a complete standalone HTML file for this tutorial section.\n\n"
            f"SECTION ID: {section_data['section_id']}\n"
            f"TITLE: {section_data['title']}\n"
            f"VISUAL BRIEF: {section_data['visual_brief']}\n\n"
            f"DESIGN REQUIREMENTS:\n{HTML_TEMPLATE_REFERENCE}\n\n"
            f"The HTML MUST include:\n"
            f'1. <audio id="audioPlayer" autoplay muted style="display:none;">'
            f'<source src="PLACEHOLDER.mp3" type="audio/mpeg"></audio>\n'
            f"2. All the background orbs, grid overlay, badge, title, content cards\n"
            f"3. Autoplay JS with fallback\n"
            f"4. Responsive design\n\n"
            f"Return ONLY the raw HTML code starting with <!DOCTYPE html>. No explanations."
        ),
        expected_output="Complete HTML document as raw text starting with <!DOCTYPE html>.",
        agent=agent,
        context=[context_task] if context_task else None,
    )


def make_audio_task(agent, section_data: dict):
    return Task(
        description=(
            f"Generate the MP3 audio for section '{section_data['section_id']}' using the "
            f"Sarvam TTS Generator tool.\n\n"
            f"Use these exact tool arguments:\n"
            f"- text: {section_data['audio_text']}\n"
            f"- filename: {section_data['section_id']}\n\n"
            f"Call the tool and return the result."
        ),
        expected_output="Confirmation message that the audio file was saved.",
        agent=agent,
    )


def make_save_task(agent, section_data: dict, html_content: str, next_section_id: str):
    return Task(
        description=(
            f"Save the HTML file using the HTML File Saver tool with these arguments:\n"
            f"- html_content: (the HTML provided below)\n"
            f"- filename: {section_data['section_id']}\n"
            f"- audio_filename: {section_data['section_id']}\n"
            f'- next_html: {next_section_id}\n\n'
            f"HTML CONTENT:\n{html_content}"
        ),
        expected_output="Confirmation that HTML was saved with audio binding and next-slide redirect.",
        agent=agent,
    )