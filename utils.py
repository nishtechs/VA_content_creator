"""
Utility functions — JSON extraction, progress tracking, master index generation.
"""

import os
import json
import re
import logging
from typing import Any

from project import (
    get_project_dir,
    get_sections_json,
    get_progress_json,
    get_index_path,
    audio_path,
    html_path,
)
from slide_template import THEMES

logger = logging.getLogger("va_creator.utils")


# Devanagari Unicode range: \u0900–\u097F
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def has_devanagari(text: str) -> bool:
    """Return True if the text contains any Hindi (Devanagari) characters."""
    return bool(_DEVANAGARI_RE.search(text or ""))


def devanagari_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are Devanagari (0.0–1.0)."""
    if not text:
        return 0.0
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    deva = sum(1 for c in letters if "\u0900" <= c <= "\u097F")
    return deva / len(letters)


def is_clean_hindi_audio(text: str) -> bool:
    """Heuristic: audio_text is acceptable if it has no code/markdown markers
    and is predominantly Hindi (Devanagari)."""
    if not text or not text.strip():
        return False
    bad_markers = ["```", "###", "[Screen:", "import ", "def ", "(0:", "---", "pip install", "**["]
    if any(marker in text for marker in bad_markers):
        return False
    # Require a meaningful share of Devanagari so English/Hinglish gets rejected
    return devanagari_ratio(text) >= 0.5


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract a JSON object from LLM output text."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0), strict=False)
        except json.JSONDecodeError:
            # Try fixing common JSON issues
            cleaned = re.sub(r",\s*}", "}", match.group(0))
            cleaned = re.sub(r",\s*]", "]", cleaned)
            cleaned = re.sub(r'[\x00-\x1f]', ' ', cleaned)  # Remove control chars
            return json.loads(cleaned, strict=False)
    raise ValueError(f"No JSON object found in: {text[:200]}")


def extract_json_array(text: str) -> list[Any]:
    """Extract a JSON array from LLM output text."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0), strict=False)
        except json.JSONDecodeError:
            # Try fixing common JSON issues
            cleaned = re.sub(r",\s*}", "}", match.group(0))
            cleaned = re.sub(r",\s*]", "]", cleaned)
            cleaned = re.sub(r'[\x00-\x1f]', ' ', cleaned)  # Remove control chars
            return json.loads(cleaned, strict=False)
    raise ValueError(f"No JSON array found in: {text[:200]}")


def extract_html(text: str) -> str:
    """Extract HTML content from LLM output text."""
    text = re.sub(r"^```(?:html)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start = text.find("<!DOCTYPE")
    if start == -1:
        start = text.find("<html")
    end = text.rfind("</html>")
    if start != -1 and end != -1:
        return text[start:end + len("</html>")]
    return text


def save_sections_json(sections: list[dict[str, Any]]) -> None:
    """Persist sections to JSON file."""
    with open(get_sections_json(), "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(sections)} sections to {get_sections_json()}")


def load_sections_json() -> list[dict[str, Any]] | None:
    """Load cached sections from JSON file."""
    path = get_sections_json()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_progress() -> dict[str, Any]:
    """Load progress tracking data."""
    path = get_progress_json()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed": [], "hashes": {}}


def save_progress(progress: dict[str, Any]) -> None:
    """Save progress tracking data."""
    with open(get_progress_json(), "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def mark_completed(section_id: str, chunk_hash: str = "") -> None:
    """Mark a section as completed in progress tracker."""
    progress = load_progress()
    if section_id not in progress["completed"]:
        progress["completed"].append(section_id)
    if chunk_hash:
        if "hashes" not in progress:
            progress["hashes"] = {}
        progress["hashes"][section_id] = chunk_hash
    save_progress(progress)


def is_completed(section_id: str) -> bool:
    """Check if a section's output files already exist and are valid."""
    h_path = html_path(section_id)
    a_path = audio_path(section_id)
    return (
        os.path.exists(h_path)
        and os.path.exists(a_path)
        and os.path.getsize(a_path) > 1000
    )


def has_chunk_changed(section_id: str, chunk_hash: str) -> bool:
    """Check if a chunk's content has changed since last run."""
    progress = load_progress()
    stored_hash = progress.get("hashes", {}).get(section_id, "")
    return stored_hash != chunk_hash


def generate_master_index(sections: list[dict[str, Any]], project_name: str = "", theme_name: str = "Dark Cyber (Default)") -> str:
    """Creates an index.html launcher page with accessibility and keyboard nav."""
    display_name = project_name or "Tutorial Slides"
    t = THEMES.get(theme_name, THEMES["Dark Cyber (Default)"])
    
    # We will use variables for the UI
    bg_color = t["bg"]
    card_bg = t["bg_card"]
    text_color = t["text"]
    text_dim = t["text_dim"]
    cyan = t["cyan"]
    purple = t["purple"]
    border_color = t["border"]
    cards_html = ""
    for i, sec in enumerate(sections):
        cards_html += f"""
        <a href="{sec['section_id']}.html" class="slide-card" tabindex="0"
           aria-label="Slide {i+1}: {sec['title']}">
          <div class="slide-num" aria-hidden="true">{i+1:02d}</div>
          <div class="slide-title">{sec['title']}</div>
          <div class="slide-cat">{sec.get('category', 'concept').upper()}</div>
        </a>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{display_name} — Slides</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Poppins',sans-serif; background:{bg_color}; color:{text_color}; padding:40px 20px; min-height:100vh; }}
.bg {{ position:fixed; inset:0; background:
  radial-gradient(circle at 15% 50%, {cyan} 10%, transparent 45%),
  radial-gradient(circle at 85% 30%, {purple} 10%, transparent 50%);
  opacity: 0.15; z-index:0; pointer-events:none; }}
.container {{ position:relative; z-index:1; max-width:1200px; margin:0 auto; }}
h1 {{ font-size:2.5rem; margin-bottom:8px; background:linear-gradient(135deg, {cyan}, {purple});
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.sub {{ color:{text_dim}; margin-bottom:40px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:16px; }}
.slide-card {{ background:{card_bg}; border:1.5px solid {border_color};
  border-radius:14px; padding:20px; text-decoration:none; color:{text_color}; transition:all 0.3s;
  display:flex; flex-direction:column; gap:8px; outline:none; }}
.slide-card:hover, .slide-card:focus {{ transform:translateY(-6px); border-color:{cyan};
  box-shadow:0 12px 40px {border_color}; }}
.slide-card:focus {{ outline:2px solid {cyan}; outline-offset:2px; }}
.slide-num {{ font-size:0.75rem; color:{cyan}; font-weight:700; letter-spacing:2px; }}
.slide-title {{ font-size:1rem; font-weight:600; }}
.slide-cat {{ font-size:0.65rem; color:{purple}; letter-spacing:1.5px; font-weight:700; }}
.play-all {{ display:inline-block; background:linear-gradient(135deg, {cyan}, {purple});
  color:#fff; padding:12px 28px; border-radius:100px; text-decoration:none;
  font-weight:700; margin-bottom:30px; transition:transform 0.2s; }}
.play-all:hover {{ transform:scale(1.05); }}
.play-all:focus {{ outline:2px solid {text_color}; outline-offset:4px; }}
.stats {{ display:flex; gap:20px; margin-bottom:20px; flex-wrap:wrap; }}
.stat {{ background:transparent; border:1px solid {border_color};
  border-radius:10px; padding:10px 16px; font-size:0.85rem; color:{text_dim}; }}
.stat-val {{ color:{purple}; font-weight:700; }}
@media (max-width:768px) {{
  h1 {{ font-size:1.8rem; }}
  .grid {{ grid-template-columns:1fr; }}
}}
/* Keyboard nav hint */
.kbd-hint {{ color:{text_dim}; font-size:0.75rem; margin-top:20px; }}
</style>
</head>
<body>
<div class="bg" aria-hidden="true"></div>
<div class="container" role="main" aria-label="Tutorial slides index">
  <h1>🎬 {display_name}</h1>
  <p class="sub">{len(sections)} slides ready &bull; Click any slide to start, or play all from beginning</p>
  <div class="stats">
    <div class="stat"><span class="stat-val">{len(sections)}</span> Total Slides</div>
    <div class="stat"><span class="stat-val">{len(set(s.get('category','') for s in sections))}</span> Categories</div>
  </div>
  <a href="{sections[0]['section_id']}.html" class="play-all" aria-label="Play all slides from the beginning">▶ Play From Start</a>
  <div class="grid" role="list">{cards_html}</div>
  <p class="kbd-hint">💡 Use Tab to navigate, Enter to select a slide</p>
</div>
<script>
  // Keyboard navigation
  document.querySelectorAll('.slide-card').forEach(card => {{
    card.addEventListener('keydown', e => {{
      if (e.key === 'Enter' || e.key === ' ') {{
        e.preventDefault();
        card.click();
      }}
    }});
  }});
</script>
</body>
</html>"""

    index_path = get_index_path()
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    logger.info(f"Master index generated: {index_path}")
    return index_path
