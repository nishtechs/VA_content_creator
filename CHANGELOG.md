# Changelog

All notable changes to VA Creator are documented here.

## [1.3.0] - 2026-06-23

### Added
- **Hindi/Devanagari font support** — Loaded `Noto Sans Devanagari` from Google Fonts for proper rendering of Hindi titles and content.
- **CSS sanitization engine** — Strips LLM `custom_css` overrides of 16 protected base-template selectors (`.glass-box`, `.flow-step`, `.step-num`, `.card`, etc.) to preserve premium styling.
- **Inline style sanitizer** — Automatically removes `height:100vh` from LLM-generated visual HTML to prevent content overflow.
- **Stricter LLM prompt rules** — Added rules forbidding base-class CSS overrides, `height:100vh` usage, and literal copying of example placeholder text.
- **Incremental `sections.json` saves** — Progress is saved after each section completes, preventing data loss on interruptions.

### Fixed
- **Hero title clipping with Hindi text** — Increased `line-height` from `1.1` to `1.35` and changed `.stage` overflow from `hidden` to `visible` so Devanagari matras are not cut off.
- **First-time generation quality** — Stale `slide_html`/`visual_html`/`custom_css` are now cleared before every LLM call, ensuring consistent output on first run.
- **"pip install langchain" leak** — Replaced hardcoded example text in the prompt with a generic `your-command-here` placeholder.
- **Resource contention** — Switched from concurrent to sequential video+audio processing to prevent MCP server crashes.

---

## [1.2.0] - 2026-06-19

### Added
- MCP server integration: Remotion, SVG Maker, LottieFiles, Stylelint, Prettier, Exa Search, DevDocs.
- Optimized MCP startup using locally installed packages.

### Fixed
- Redo Video caching bug by clearing layout cache in `regenerate_video_only`.
- SVG generator and Prettier MCP package name corrections.

---

## [1.1.0] - 2026-06-17

### Added
- Section script & style editor in Streamlit UI.
- AI Regeneration vs. Instant Re-rendering modes.
- Auto-scrolling code typewriter animation.
- GSAP animation system for slide reveals.

### Fixed
- Duplicate typewriter `codeTarget` elements.
- Double title/subtitle rendering at both JSON and template level.
- Regex filter for stripping duplicate code blocks.

---

## [1.0.0] - 2026-06-14

### Added
- Initial release.
- Multi-agent pipeline with CrewAI (Structurer, Designer, Audio, Publisher).
- NVIDIA NIM LLM integration (Llama 3.3 70B).
- Sarvam AI Hindi/Hinglish TTS.
- Premium dark cyber-themed HTML slides.
- Smart chunker for long-form Markdown scripts.
- Smart resume support (skips completed sections).
- Streamlit Web UI Dashboard.
- Master index launcher.
