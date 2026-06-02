"""
Task definitions for CrewAI agents.
Only LLM-dependent tasks remain here (structuring + visual design).
"""

from crewai import Task

HTML_TEMPLATE_REFERENCE = """
Design System (MUST FOLLOW EXACTLY):
- Background: #0a0e27 with two animated floating orbs (cyan #00d4ff & purple #a78bfa, blur 80px)
- Grid overlay: 50px lines, rgba(0,212,255,0.02)
- Fonts: Poppins (400/600/700/800) + JetBrains Mono
- Top badge: rounded, cyan border, uppercase, 0.62rem
- Hero title: 2.2rem, white, with gradient highlight span (cyan-to-cyan-glow)
- Subtitle: 0.95rem, color #b0b8d4
- Divider line with cyan center gradient
- Section title with emoji icon + highlight span
- Cards (step-card / tech-card): glassmorphism, cyan border 1.5px, hover translateY(-8px), staggered animation delays
- Step number badges: 44px circular cyan gradient
- Disclaimer box: purple-tinted background
- cursor:none !important on all
- Responsive @media (max-width:768px)
- MUST contain: <audio id="audioPlayer" autoplay muted style="display:none;"><source src="PLACEHOLDER.mp3" type="audio/mpeg"></audio>
- Autoplay script with click/scroll fallback
- Add tabindex="0" to interactive elements for keyboard navigation
- Use semantic HTML (header, main, section, footer)
- Include aria-label on key sections
- Use proper heading hierarchy (h1 > h2 > h3)
"""


def make_chunking_task(agent, chunk: dict, section_id: str) -> Task:
    """Create a task to structure a raw chunk into a JSON section.
    The spoken_text is pre-extracted, so the LLM only needs to clean/refine it
    and generate the visual brief.
    """
    # Use pre-extracted spoken text if available
    pre_extracted_audio = chunk.get("spoken_text", "")
    audio_instruction = ""
    if pre_extracted_audio:
        audio_instruction = (
            f"\n\nSOURCE NARRATION (convert this into the audio_text):\n{pre_extracted_audio}\n"
            f"Translate/convert it into natural spoken HINDI in DEVANAGARI script. "
            f"DO NOT add timestamps, code, or stage directions.\n"
        )
    else:
        audio_instruction = (
            "\n\nNOTE: Extract ONLY the spoken narration from > quoted lines and render it as "
            "natural HINDI in DEVANAGARI script. "
            "DO NOT include timestamps, [Screen:] tags, code blocks, or English instructions."
        )

    # Code-aware instructions
    code_blocks = chunk.get("code_blocks", [])
    has_code = bool(code_blocks)
    code_instruction = ""
    code_field_spec = '  "code": "",\n  "code_language": "",\n'
    if has_code:
        # Join all code blocks for this chunk
        joined_code = "\n\n".join(
            f"# [{b.get('language', 'text')}]\n{b.get('code', '')}" for b in code_blocks
        )
        primary_lang = code_blocks[0].get("language", "text")
        code_instruction = (
            f"\n\nTHIS SECTION CONTAINS CODE:\n{joined_code}\n\n"
            f"CODE HANDLING RULES:\n"
            f"- Put the most relevant code block VERBATIM into the 'code' field "
            f"(preserve indentation and newlines).\n"
            f"- Set 'code_language' to the language (e.g. python, bash, javascript).\n"
            f"- The 'audio_text' MUST be written in HINDI using DEVANAGARI script and MUST clearly "
            f"EXPLAIN what this code does, line by line or step by step, in simple conversational Hindi — "
            f"so a listener understands the code without seeing it. Technical keywords/identifiers "
            f"(function names, library names) may stay in English, but the explanation around them is Hindi.\n"
            f"- Set 'category' to 'code'.\n"
        )
        code_field_spec = (
            '  "code": "<the code VERBATIM with original newlines/indentation>",\n'
            f'  "code_language": "{primary_lang}",\n'
        )

    return Task(
        description=(
            f"Convert the following raw tutorial chunk into a structured JSON section.\n\n"
            f"SECTION ID TO USE: {section_id}\n"
            f"PARENT HEADING: {chunk['heading']}\n"
            f"RAW CHUNK:\n{chunk['content']}\n"
            f"{audio_instruction}"
            f"{code_instruction}\n\n"
            f"Return a JSON object with EXACTLY these fields:\n"
            f'  "section_id": "{section_id}",\n'
            f'  "title": "<short engaging title for this slide in ENGLISH, max 6 words>",\n'
            f'  "audio_text": "<the spoken narration in HINDI written in DEVANAGARI script (देवनागरी). '
            f'NO code, NO timestamps, NO [Screen:] tags, NO markdown, NO English sentences. '
            f'Natural conversational Hindi speech, 40-120 words. '
            f'If this section has code, this Hindi narration must EXPLAIN the code>",\n'
            f'  "visual_brief": "<ENGLISH bullet description of what to show on screen: key points, code snippets, icons, layout>",\n'
            f"{code_field_spec}"
            f'  "category": "<one of: intro, concept, code, setup, demo, summary>"\n\n'
            f"LANGUAGE RULES (STRICT):\n"
            f"- audio_text → HINDI in DEVANAGARI script ONLY (this becomes the spoken narration). "
            f"If the source narration is in English or romanized Hinglish, TRANSLATE it into proper Hindi (देवनागरी). "
            f"Must contain ONLY speakable words: no code, no markdown, no timestamps, no stage directions.\n"
            f"- title and visual_brief → ENGLISH ONLY (these drive the on-screen slide).\n"
            f"- code → keep EXACTLY as written (any language), empty string if no code.\n\n"
            f"Return ONLY the JSON object, no markdown fences, no explanation."
        ),
        expected_output="A single JSON object with section_id, title, audio_text, visual_brief, code, code_language, category.",
        agent=agent,
    )


def make_visual_task(agent, section_data: dict) -> Task:
    """Create a task that asks the LLM for STRUCTURED SLIDE CONTENT (JSON), not HTML.
    The HTML is rendered deterministically by slide_template.render_slide(), so slide
    quality is identical regardless of which model is used.
    """
    code = section_data.get("code", "")
    has_code = bool(code and str(code).strip())

    code_note = ""
    if has_code:
        code_note = (
            "\n\nNOTE: This section has CODE (it will be shown automatically with a typing "
            "animation by the renderer — you do NOT need to include the code yourself). "
            "Provide 1-2 short cards that summarize what the code does, in English.\n"
        )

    return Task(
        description=(
            f"Produce STRUCTURED CONTENT for one tutorial slide as a JSON object. "
            f"Do NOT write HTML — only the content fields below.\n\n"
            f"TITLE: {section_data['title']}\n"
            f"CATEGORY: {section_data.get('category', 'concept')}\n"
            f"VISUAL BRIEF: {section_data['visual_brief']}\n"
            f"{code_note}\n"
            f"Return a JSON object with EXACTLY these fields (ALL TEXT IN ENGLISH):\n"
            f'  "headline": "<slide title, max 7 words>",\n'
            f'  "badge": "<2-3 word uppercase tag, e.g. INTRODUCTION, SETUP, CONCEPT>",\n'
            f'  "subtitle": "<one short sentence describing this slide>",\n'
            f'  "cards": [ {{"title": "<short>", "text": "<1 sentence>"}} ],\n'
            f'  "footer": "<very short footer line>"\n\n'
            f"RULES:\n"
            f"- ALL text must be in ENGLISH (translate any Hindi from the brief).\n"
            f"- For 'intro' use 1-2 cards or none; for 'concept'/'setup'/'summary' use 3-4 cards; "
            f"for 'code' use 1-2 cards summarizing the code.\n"
            f"- Keep each card short and scannable.\n"
            f"- Return ONLY the JSON object. No HTML, no markdown fences, no explanation."
        ),
        expected_output='A single JSON object with headline, badge, subtitle, cards[], footer.',
        agent=agent,
    )
