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


def make_research_script_task(agent, topic: str) -> Task:
    """Create a task to research a topic and generate structured sections JSON directly."""
    return Task(
        description=(
            f"Topic: {topic}\n\n"
            f"1. Use your web search tool to gather accurate, up-to-date technical information on this topic.\n"
            f"2. Generate structured tutorial sections/slides directly as a JSON array of objects (no markdown narration script, output JSON directly).\n"
            f"3. Each object in the JSON array must represent a slide and have EXACTLY these fields:\n"
            f'   - "section_id": "section_01", "section_02", etc.\n'
            f'   - "title": "<short engaging title for this slide in ENGLISH, max 6 words>"\n'
            f'   - "audio_text": "<spoken narration in HINDI written in DEVANAGARI script. Conversational Hindi, explaining the concepts/code clearly, 40-120 words. No English characters, no code, no markdown inside this field>"\n'
            f'   - "visual": "<ENGLISH bullet description of what to show on screen. Must list the same points as audio_text>"\n'
            f'   - "code": "<code snippet verbatim if any, or empty string>"\n'
            f'   - "code_language": "<language of the code block, e.g. python, bash, or empty string>"\n'
            f'   - "category": "<one of: intro, concept, code, setup, demo, summary>"\n'
            f"4. Return ONLY the JSON array, no markdown fences, no explanation."
        ),
        expected_output="A single JSON array of structured sections/slides.",
        agent=agent,
    )


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
            f'  "visual": "<ENGLISH bullet description of what to show on screen. '
            f'MUST cover the SAME key concepts/steps described in audio_text so the viewer sees '
            f'on screen what the narrator is explaining. Include: key points, icons, layout suggestions, '
            f'any URLs to display as plain text>",\n'
            f"{code_field_spec}"
            f'  "category": "<one of: intro, concept, code, setup, demo, summary>"\n\n'
            f"QUALITY RULE — VISUAL & AUDIO ALIGNMENT (CRITICAL):\n"
            f"- The 'visual' and 'audio_text' MUST be about the SAME topic and cover the SAME core points.\n"
            f"- If the audio narration explains three steps, the visual MUST list the same three steps.\n"
            f"- If the audio talks about a specific tool/library/concept, the visual MUST reference it.\n"
            f"- There should be NO mismatch between what the viewer sees and what the narrator says.\n\n"
            f"LANGUAGE RULES (STRICT):\n"
            f"- audio_text → HINDI in DEVANAGARI script ONLY (this becomes the spoken narration). "
            f"If the source narration is in English or romanized Hinglish, TRANSLATE it into proper Hindi (देवनागरी). "
            f"Must contain ONLY speakable words: no code, no markdown, no timestamps, no stage directions.\n"
            f"- title and visual → ENGLISH ONLY (these drive the on-screen slide).\n"
            f"- code → keep EXACTLY as written (any language), empty string if no code.\n\n"
            f"Return ONLY the JSON object, no markdown fences, no explanation."
        ),
        expected_output="A single JSON object with section_id, title, audio_text, visual, code, code_language, category.",
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
    else:
        code_note = (
            "\n\nNOTE: This section does NOT contain code. You MUST NOT include any code blocks, "
            "typewriter code, or `code-wrap` elements in your slide_html. Keep all visuals strictly "
            "focused on concepts, theory, steps, or features using flow-steps or glass-boxes.\n"
        )

    theme_name = section_data.get("theme", "Dark Cyber (Default)")

    return Task(
        description=(
            f"Produce PREMIUM structured content for one tutorial slide as a JSON object.\n\n"
            f"SLIDE TITLE: {section_data['title']}\n"
            f"SLIDE THEME: {theme_name}\n"
            f"SLIDE CATEGORY: {section_data.get('category', 'concept')}\n"
            f"VISUAL: {section_data.get('visual') or section_data.get('visual_brief') or ''}\n"
            f"AUDIO TEXT (narrator will say this — your visual MUST match): {section_data.get('audio_text', 'N/A')}\n"
            f"{code_note}\n"
            f"═══════════════════════════════════════════\n"
            f"YOUR GOAL: You are responsible for the FULL HTML layout of the slide.\n"
            f"Create VISUALLY STUNNING, creative layouts using CSS Grid or Flexbox.\n"
            f"Do not just make a single column of text. Use split panes, metrics grids, centered hero views, etc.\n"
            f"═══════════════════════════════════════════\n\n"
            f"AVAILABLE PRE-BUILT COMPONENTS (use these for consistent premium styling):\n\n"
            f"1. GLASS BOX: <div class=\"glass-box\"><h3>Title</h3><p>Content</p></div>\n"
            f"   - A frosted-glass panel with backdrop blur. Use for info sections.\n\n"
            f"2. FLOW STEP: <div class=\"flow-step\"><div class=\"step-num\">1</div><div><strong>Step Title</strong><br><span style=\"color:var(--text-dim)\">Description</span></div></div>\n"
            f"   - A numbered step with left accent border. Stack multiples for processes.\n\n"
            f"3. COMMAND BOX: <div class=\"command-box\">your-command-here</div>\n"
            f"   - Terminal-styled command box with auto $ prefix. Use for CLI commands RELEVANT to the slide topic only.\n\n"
            f"4. HIGHLIGHT TEXT: <span class=\"highlight\">cyan text</span> or <span class=\"highlight-purple\">purple text</span>\n\n"
            f"5. ICONS: FontAwesome 6 — <i class=\"fas fa-robot\"></i>, <i class=\"fas fa-database\"></i>, etc.\n\n"
            f"═══════════════════════════════════════════\n"
            f"GSAP ANIMATION CLASSES (CRITICAL):\n"
            f"═══════════════════════════════════════════\n"
            f"Add this class to your custom visual elements so our animation engine can sequence them:\n"
            f"- `gsap-reveal`: Add to ANY container (like `glass-box`, `flow-step`, `code-wrap`) that should stagger-animate into view.\n\n"
            f"Note: The slide title, subtitle, and badge are rendered automatically at the top of the slide by the system template. DO NOT generate them inside your slide_html.\n"
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
            f"- LAYOUT: DO NOT assume the parent container is a grid or flexbox. You MUST explicitly wrap your content in `<div style=\"display: grid; ...\">` or `<div style=\"display: flex; ...\">` if you want a grid/flex layout.\n"
            f"- OVERFLOW: The slide height is FIXED at 100vh with overflow:hidden. NEVER stack 4-5 tall blocks vertically. If you have a lot of content, you MUST use a side-by-side flexbox or grid to spread it horizontally.\n"
            f"- NEVER use height:100vh on any element inside slide_html. The slide height is already managed by the page body.\n"
            f"- COLORS: Use CSS variables ONLY: var(--bg-card) for box backgrounds, var(--border) for borders, var(--text) for text, var(--text-dim) for secondary text, var(--cyan) or var(--purple) for accents. NEVER hardcode hex or rgba colors like #fff or rgba(15,23,42). ALWAYS use var().\n"
            f"- Add border-radius:14px, padding:16px to custom containers.\n"
            f"- CUSTOM_CSS: NEVER re-declare or override pre-built component classes (glass-box, flow-step, step-num, card, card-icon, card-title, card-body, code-wrap, badge, hero-title, subtitle, divider, command-box). These are already perfectly styled by the template. Only use custom_css for truly NEW classes you invent.\n"
            f"- EXAMPLES: The component examples above show syntax patterns only. NEVER copy example content literally (like placeholder commands). Always use content relevant to the actual slide topic.\n\n"
            f"Return a JSON object with EXACTLY these fields (no markdown fences):\n"
            f"{{\n"
            f'  "slide_html": "<The HTML layout of the slide body. DO NOT include the slide badge, title, or subtitle here. Only include your custom visual layout components like glass-boxes, flow-steps, or grids.>",\n'
            f'  "custom_css": "<additional CSS if needed beyond pre-built classes>"\n'
            f"}}\n"
        ),
        expected_output='A single JSON object with slide_html and custom_css.',
        agent=agent,
    )

