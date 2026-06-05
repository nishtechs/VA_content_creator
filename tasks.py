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
            f'  "visual_brief": "<ENGLISH bullet description of what to show on screen. '
            f'MUST cover the SAME key concepts/steps described in audio_text so the viewer sees '
            f'on screen what the narrator is explaining. Include: key points, icons, layout suggestions, '
            f'any URLs to display as plain text>",\n'
            f"{code_field_spec}"
            f'  "category": "<one of: intro, concept, code, setup, demo, summary>"\n\n'
            f"QUALITY RULE — VISUAL & AUDIO ALIGNMENT (CRITICAL):\n"
            f"- The 'visual_brief' and 'audio_text' MUST be about the SAME topic and cover the SAME core points.\n"
            f"- If the audio narration explains three steps, the visual brief MUST list the same three steps.\n"
            f"- If the audio talks about a specific tool/library/concept, the visual brief MUST reference it.\n"
            f"- There should be NO mismatch between what the viewer sees and what the narrator says.\n\n"
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
    """Create a task that asks the LLM for STRUCTURED SLIDE CONTENT (JSON) including
    custom visual HTML and CSS to explain the slide's context with premium quality.
    """
    code = section_data.get("code", "")
    has_code = bool(code and str(code).strip())

    code_note = ""
    if has_code:
        code_note = (
            "\n\nNOTE: This section contains CODE. The code typewriter component is generated "
            "automatically by the rendering engine and placed side-by-side with your visual content. "
            "Your visual HTML should focus on explaining what the code does, showing data flows, "
            "inputs/outputs, or annotated step-by-step breakdowns — NOT repeating the raw code.\n"
        )

    return Task(
        description=(
            f"Produce PREMIUM structured content for one tutorial slide as a JSON object.\n\n"
            f"SLIDE TITLE: {section_data['title']}\n"
            f"SLIDE CATEGORY: {section_data.get('category', 'concept')}\n"
            f"VISUAL BRIEF: {section_data['visual_brief']}\n"
            f"AUDIO TEXT (narrator will say this — your visual MUST match): {section_data.get('audio_text', 'N/A')}\n"
            f"{code_note}\n"
            f"═══════════════════════════════════════════\n"
            f"YOUR GOAL: Create VISUALLY STUNNING HTML that explains the topic.\n"
            f"═══════════════════════════════════════════\n\n"
            f"AVAILABLE PRE-BUILT COMPONENTS (use these for consistent premium styling):\n\n"
            f"1. GLASS BOX: <div class=\"glass-box\"><h3>Title</h3><p>Content</p></div>\n"
            f"   - A frosted-glass panel with backdrop blur. Use for info sections.\n\n"
            f"2. FLOW STEP: <div class=\"flow-step\"><div class=\"step-num\">1</div><div><strong>Step Title</strong><br><span style=\"color:#94a3b8\">Description</span></div></div>\n"
            f"   - A numbered step with left accent border. Stack multiples for processes.\n\n"
            f"3. COMMAND BOX: <div class=\"command-box\">pip install langchain</div>\n"
            f"   - Terminal-styled command box with auto $ prefix. Use for CLI commands.\n\n"
            f"4. HIGHLIGHT TEXT: <span class=\"highlight\">cyan text</span> or <span class=\"highlight-purple\">purple text</span>\n\n"
            f"5. ICONS: FontAwesome 6 — <i class=\"fas fa-robot\"></i>, <i class=\"fas fa-database\"></i>, etc.\n\n"
            f"═══════════════════════════════════════════\n"
            f"CATEGORY-SPECIFIC LAYOUT RULES:\n"
            f"═══════════════════════════════════════════\n\n"
            f"• INTRO: Create an eye-catching overview with 2-3 glass-box panels in a grid showing "
            f"  key features/benefits. Use large icons and short punchy text.\n\n"
            f"• CONCEPT/THEORY: Build a visual flowchart using flow-step components showing the process. "
            f"  OR create a comparison grid with glass-box panels. Use icons to represent each concept.\n\n"
            f"• SETUP/INSTALLATION: Use command-box for terminal commands. Below, add a glass-box "
            f"  with a list of packages/dependencies with <i class=\"fas fa-check\"></i> icons.\n\n"
            f"• CODE WALKTHROUGH: Create annotated flow-step components explaining each part of the code. "
            f"  Show data flow: Input → Processing → Output using glass-box panels.\n\n"
            f"• DEMO: Create a mock chat interface with alternating user/bot messages. Use flex layout "
            f"  with different background colors for each speaker.\n\n"
            f"• SUMMARY: Create a recap grid with 3-4 glass-box panels, each with an icon and 2-3 "
            f"  key takeaway points.\n\n"
            f"═══════════════════════════════════════════\n"
            f"STRICT RULES:\n"
            f"═══════════════════════════════════════════\n"
            f"- ALL text in ENGLISH only.\n"
            f"- Minimum 3-5 distinct visual elements per slide (not just one big paragraph).\n"
            f"- NO <html>, <body>, <head>, <script> tags. Only inner elements.\n"
            f"- NO scrollable containers. No overflow:auto/scroll.\n"
            f"- NO <a href> anchor tags. Show URLs as <span class=\"highlight\">url</span>.\n"
            f"- Use CSS grid or flexbox for layout. Use gap for spacing.\n"
            f"- Use the dark palette: backgrounds rgba(15,23,42,0.65), borders rgba(0,212,255,0.15).\n"
            f"- Add border-radius:14px, padding:16px to custom containers.\n\n"
            f"Return a JSON object with EXACTLY these fields (no markdown fences):\n"
            f"{{\n"
            f'  "headline": "<engaging title, max 7 words in English>",\n'
            f'  "badge": "<2-3 words uppercase, e.g., CORE CONCEPT, RAG FLOW, LIVE DEMO>",\n'
            f'  "subtitle": "<one sentence describing this slide in English>",\n'
            f'  "visual_html": "<premium visual HTML using the components above>",\n'
            f'  "custom_css": "<additional CSS if needed beyond pre-built classes>",\n'
            f'  "footer": "<short footer text>"\n'
            f"}}\n"
        ),
        expected_output='A single JSON object with headline, badge, subtitle, visual_html, custom_css, and footer.',
        agent=agent,
    )

