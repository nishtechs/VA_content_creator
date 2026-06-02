"""
Deterministic slide renderer.

Instead of asking the LLM to author full HTML (unreliable across models), the LLM
only supplies structured CONTENT (headline, subtitle, cards, code). This module
renders that content into a consistent, high-quality dark-cyber-themed HTML slide
with reliable audio autoplay + chaining — identical quality on any model.
"""

import html as _html
import json
from typing import Any


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return _html.escape(str(text or ""), quote=True)


def _cards_html(cards: list[dict[str, str]]) -> str:
    out = []
    for i, card in enumerate(cards):
        title = _esc(card.get("title", ""))
        body = _esc(card.get("text", card.get("body", "")))
        delay = 0.15 * i
        out.append(f"""
        <div class="card" tabindex="0" style="animation-delay:{delay:.2f}s">
          <div class="card-num">{i + 1:02d}</div>
          <div class="card-title">{title}</div>
          <div class="card-body">{body}</div>
        </div>""")
    return "\n".join(out)


def _code_block_html(code: str, language: str) -> str:
    """Code block markup; the typing animation is driven by JS using the data attribute."""
    safe = _esc(code)
    lang = _esc(language or "code")
    return f"""
      <div class="code-wrap">
        <div class="code-head">
          <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
          <span class="code-lang">{lang}</span>
        </div>
        <pre class="code-body"><code id="codeTarget" data-code="{safe}"></code><span class="cursor">▋</span></pre>
      </div>"""


def render_slide(
    section: dict[str, Any],
    content: dict[str, Any],
    next_section_id: str = "",
    project_name: str = "",
) -> str:
    """
    Render a complete HTML slide.

    section: structured section (has section_id, category, code, code_language)
    content: LLM-provided display content {headline, subtitle, cards[], footer}
    next_section_id: for auto-advance chaining
    """
    sid = section.get("section_id", "section")
    category = (section.get("category") or content.get("category") or "concept").lower()

    headline = _esc(content.get("headline") or section.get("title") or "")
    subtitle = _esc(content.get("subtitle") or "")
    footer = _esc(content.get("footer") or project_name or "VA Creator")
    badge = _esc(content.get("badge") or category.upper())

    cards = content.get("cards") or []
    code = section.get("code") or content.get("code") or ""
    code_language = section.get("code_language") or content.get("code_language") or "text"
    has_code = bool(str(code).strip())

    # Build the main body region depending on whether there's code
    if has_code:
        body_region = _code_block_html(code, code_language)
        if cards:
            body_region = f'<div class="cards">{_cards_html(cards[:2])}</div>' + body_region
    elif cards:
        body_region = f'<div class="cards">{_cards_html(cards[:4])}</div>'
    else:
        body_region = ""

    subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""

    # Auto-advance script (only if there is a next slide)
    chain_js = ""
    if next_section_id:
        chain_js = f"""
    player.addEventListener('ended', function() {{
      document.body.style.transition = 'opacity 0.5s ease';
      document.body.style.opacity = '0';
      setTimeout(function() {{ window.location.href = '{next_section_id}.html'; }}, 500);
    }});"""

    # Code typewriter script (only if there is code)
    code_js = ""
    if has_code:
        code_js = """
  (function() {
    var el = document.getElementById('codeTarget');
    if (!el) return;
    var full = el.getAttribute('data-code') || '';
    var i = 0;
    function type() {
      if (i <= full.length) {
        el.textContent = full.slice(0, i);
        i++;
        setTimeout(type, 12);
      } else {
        var c = document.querySelector('.cursor');
        if (c) c.style.animation = 'blink 1s steps(1) infinite';
      }
    }
    type();
  })();"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{headline}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  :root {{ --cyan:#00d4ff; --purple:#a78bfa; --bg:#0a0e27; }}
  body {{
    font-family:'Poppins',sans-serif; background:var(--bg); color:#fff;
    min-height:100vh; overflow:hidden; position:relative;
    display:flex; flex-direction:column; justify-content:center;
    padding:48px 56px; animation:fadeIn .6s ease forwards;
  }}
  @keyframes fadeIn {{ from {{opacity:0;}} to {{opacity:1;}} }}
  .orb {{ position:fixed; border-radius:50%; filter:blur(80px); opacity:.55; z-index:0; animation:float 8s ease-in-out infinite; }}
  .orb.cyan {{ width:340px; height:340px; background:var(--cyan); top:-80px; left:-60px; }}
  .orb.purple {{ width:380px; height:380px; background:var(--purple); bottom:-120px; right:-80px; animation-delay:-4s; }}
  @keyframes float {{ 0%,100%{{transform:translateY(0)}} 50%{{transform:translateY(-30px)}} }}
  .grid {{ position:fixed; inset:0; z-index:0;
    background-image:linear-gradient(rgba(0,212,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,.04) 1px,transparent 1px);
    background-size:50px 50px; }}
  .stage {{ position:relative; z-index:1; max-width:1100px; margin:0 auto; width:100%; }}
  .badge {{ display:inline-block; border:1px solid var(--cyan); color:var(--cyan);
    border-radius:100px; padding:5px 16px; font-size:.62rem; font-weight:700;
    letter-spacing:2px; text-transform:uppercase; margin-bottom:18px; }}
  .hero-title {{ font-size:2.4rem; font-weight:800; line-height:1.15; margin-bottom:10px;
    opacity:0; transform:translateY(16px); animation:rise .6s ease .15s forwards; }}
  .hero-title .hl {{ background:linear-gradient(135deg,var(--cyan),#7ef9ff);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
  .subtitle {{ font-size:1rem; color:#b0b8d4; margin-bottom:26px; max-width:760px;
    opacity:0; transform:translateY(16px); animation:rise .6s ease .3s forwards; }}
  .divider {{ height:2px; width:100%; margin:6px 0 26px;
    background:linear-gradient(90deg,transparent,var(--cyan),transparent); opacity:.6; }}
  @keyframes rise {{ to {{opacity:1; transform:translateY(0);}} }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin-bottom:22px; }}
  .card {{ background:rgba(0,212,255,.05); border:1.5px solid rgba(0,212,255,.22);
    border-radius:14px; padding:20px; opacity:0; transform:translateY(18px);
    animation:rise .5s ease forwards; transition:transform .3s, border-color .3s, box-shadow .3s; }}
  .card:hover, .card:focus {{ transform:translateY(-8px); border-color:var(--cyan);
    box-shadow:0 14px 40px rgba(0,212,255,.18); outline:none; }}
  .card-num {{ width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center;
    background:linear-gradient(135deg,var(--cyan),#0090c0); color:#02121a; font-weight:800; margin-bottom:12px; }}
  .card-title {{ font-size:1.05rem; font-weight:700; margin-bottom:6px; }}
  .card-body {{ font-size:.9rem; color:#b0b8d4; line-height:1.5; }}
  .code-wrap {{ background:#0c1330; border:1.5px solid rgba(0,212,255,.28); border-radius:14px;
    overflow:hidden; box-shadow:0 12px 50px rgba(0,212,255,.12);
    opacity:0; transform:translateY(18px); animation:rise .5s ease .2s forwards; }}
  .code-head {{ display:flex; align-items:center; gap:8px; padding:10px 16px;
    background:rgba(255,255,255,.03); border-bottom:1px solid rgba(0,212,255,.15); }}
  .dot {{ width:11px; height:11px; border-radius:50%; }}
  .dot.red{{background:#ff5f56}} .dot.yellow{{background:#ffbd2e}} .dot.green{{background:#27c93f}}
  .code-lang {{ margin-left:auto; font-family:'JetBrains Mono',monospace; font-size:.72rem; color:var(--cyan); letter-spacing:1px; }}
  .code-body {{ margin:0; padding:20px; font-family:'JetBrains Mono',monospace; font-size:.92rem;
    line-height:1.6; color:#d6e7ff; white-space:pre; overflow-x:auto; min-height:60px; }}
  .cursor {{ color:var(--cyan); font-weight:700; }}
  @keyframes blink {{ 0%,50%{{opacity:1}} 51%,100%{{opacity:0}} }}
  footer {{ position:fixed; bottom:18px; left:0; right:0; text-align:center;
    color:#5a6488; font-size:.72rem; z-index:1; }}
  @media (max-width:768px) {{
    body {{ padding:28px 22px; }}
    .hero-title {{ font-size:1.6rem; }}
    .cards {{ grid-template-columns:1fr; }}
  }}
</style>
</head>
<body>
<div class="orb cyan" aria-hidden="true"></div>
<div class="orb purple" aria-hidden="true"></div>
<div class="grid" aria-hidden="true"></div>
<main class="stage" role="main" aria-label="Tutorial slide">
  <div class="badge">{badge}</div>
  <h1 class="hero-title">{headline}</h1>
  {subtitle_html}
  <div class="divider"></div>
  {body_region}
</main>
<footer>{footer}</footer>

<audio id="audioPlayer" autoplay style="display:none;">
  <source src="{sid}.mp3" type="audio/mpeg">
</audio>

<script>
  (function() {{
    var player = document.getElementById('audioPlayer');

    // Try to autoplay with sound; if blocked, unmute + play on first interaction.
    function tryPlay() {{
      if (!player) return;
      player.muted = false;
      var p = player.play();
      if (p && p.catch) {{ p.catch(function() {{ /* wait for interaction */ }}); }}
    }}
    window.addEventListener('load', tryPlay);
    ['click','keydown','scroll','touchstart','mousemove'].forEach(function(ev) {{
      document.addEventListener(ev, function once() {{
        player.muted = false;
        player.play();
        ['click','keydown','scroll','touchstart','mousemove'].forEach(function(e2) {{
          document.removeEventListener(e2, once);
        }});
      }}, {{ once:false }});
    }});
{chain_js}
{code_js}
  }})();
</script>
</body>
</html>"""


def parse_content(raw: str) -> dict[str, Any]:
    """Parse the LLM's JSON content output, tolerating fences/extra text."""
    import re
    txt = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        cleaned = re.sub(r",\s*}", "}", m.group(0))
        cleaned = re.sub(r",\s*]", "]", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {}


def build_and_save_slide(
    section: dict[str, Any],
    content: dict[str, Any],
    next_section_id: str = "",
    project_name: str = "",
) -> str:
    """Render the slide and write it to the active project's folder. Returns the path."""
    from project import html_path

    sid = section.get("section_id", "section")
    html = render_slide(section, content, next_section_id, project_name)
    out_path = html_path(sid)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path
