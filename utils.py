import os
import json
import re
from config import OUTPUT_DIR, SECTIONS_JSON, PROGRESS_JSON


def extract_json_object(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            cleaned = re.sub(r",\s*}", "}", match.group(0))
            cleaned = re.sub(r",\s*]", "]", cleaned)
            return json.loads(cleaned)
    raise ValueError(f"No JSON object found in: {text[:200]}")


def extract_html(text: str):
    text = re.sub(r"^```(?:html)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start = text.find("<!DOCTYPE")
    if start == -1:
        start = text.find("<html")
    end = text.rfind("</html>")
    if start != -1 and end != -1:
        return text[start:end + len("</html>")]
    return text


def save_sections_json(sections: list):
    with open(SECTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)


def load_sections_json():
    if os.path.exists(SECTIONS_JSON):
        with open(SECTIONS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_progress():
    if os.path.exists(PROGRESS_JSON):
        with open(PROGRESS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed": []}


def save_progress(progress):
    with open(PROGRESS_JSON, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def mark_completed(section_id: str):
    progress = load_progress()
    if section_id not in progress["completed"]:
        progress["completed"].append(section_id)
        save_progress(progress)


def is_completed(section_id: str) -> bool:
    html_path = os.path.join(OUTPUT_DIR, f"{section_id}.html")
    audio_path = os.path.join(OUTPUT_DIR, f"{section_id}.mp3")
    return (
        os.path.exists(html_path)
        and os.path.exists(audio_path)
        and os.path.getsize(audio_path) > 1000
    )


def generate_master_index(sections: list):
    """Creates an index.html launcher page."""
    cards_html = ""
    for i, sec in enumerate(sections):
        cards_html += f"""
        <a href="{sec['section_id']}.html" class="slide-card">
          <div class="slide-num">{i+1:02d}</div>
          <div class="slide-title">{sec['title']}</div>
          <div class="slide-cat">{sec.get('category', 'concept').upper()}</div>
        </a>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Tutorial Slides Index</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Poppins',sans-serif; background:#0a0e27; color:#fff; padding:40px 20px; min-height:100vh; }}
.bg {{ position:fixed; inset:0; background:
  radial-gradient(circle at 15% 50%, rgba(0,212,255,0.08) 0%, transparent 45%),
  radial-gradient(circle at 85% 30%, rgba(167,139,250,0.07) 0%, transparent 50%);
  z-index:0; }}
.container {{ position:relative; z-index:1; max-width:1200px; margin:0 auto; }}
h1 {{ font-size:2.5rem; margin-bottom:8px; background:linear-gradient(135deg,#00d4ff,#a78bfa);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.sub {{ color:#b0b8d4; margin-bottom:40px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:16px; }}
.slide-card {{ background:rgba(0,212,255,0.05); border:1.5px solid rgba(0,212,255,0.2);
  border-radius:14px; padding:20px; text-decoration:none; color:#fff; transition:all 0.3s;
  display:flex; flex-direction:column; gap:8px; }}
.slide-card:hover {{ transform:translateY(-6px); border-color:#00d4ff;
  box-shadow:0 12px 40px rgba(0,212,255,0.2); }}
.slide-num {{ font-size:0.75rem; color:#00d4ff; font-weight:700; letter-spacing:2px; }}
.slide-title {{ font-size:1rem; font-weight:600; }}
.slide-cat {{ font-size:0.65rem; color:#a78bfa; letter-spacing:1.5px; font-weight:700; }}
.play-all {{ display:inline-block; background:linear-gradient(135deg,#00d4ff,#00ffff);
  color:#0a0e27; padding:12px 28px; border-radius:100px; text-decoration:none;
  font-weight:700; margin-bottom:30px; }}
</style>
</head>
<body>
<div class="bg"></div>
<div class="container">
  <h1>🎬 Tutorial Slides</h1>
  <p class="sub">{len(sections)} slides ready • Click any slide to start, or play all from beginning</p>
  <a href="{sections[0]['section_id']}.html" class="play-all">▶ Play From Start</a>
  <div class="grid">{cards_html}</div>
</div>
</body>
</html>"""

    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    return index_path