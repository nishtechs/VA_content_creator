"""
Deterministic slide renderer — Premium Visual Edition.

The LLM supplies structured CONTENT (headline, subtitle, visual_html, custom_css,
cards, code). This module renders that content into a consistent, ultra-polished
dark-cyber-themed HTML slide with reliable audio autoplay + chaining.
"""

import html as _html
import json
from typing import Any


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return _html.escape(str(text or ""), quote=True)


def _cards_html(cards: list[dict[str, str]]) -> str:
    icons = ["fas fa-lightbulb", "fas fa-rocket", "fas fa-layer-group", "fas fa-check-circle",
             "fas fa-cogs", "fas fa-chart-line", "fas fa-shield-alt", "fas fa-puzzle-piece"]
    out = []
    for i, card in enumerate(cards):
        title = _esc(card.get("title", ""))
        body = _esc(card.get("text", card.get("body", "")))
        delay = 0.15 * i
        icon = icons[i % len(icons)]
        out.append(f"""
        <div class="card" tabindex="0" style="animation-delay:{delay:.2f}s">
          <div class="card-icon"><i class="{icon}"></i></div>
          <div class="card-title">{title}</div>
          <div class="card-body">{body}</div>
          <div class="card-glow"></div>
        </div>""")
    return "\n".join(out)


def _code_block_html(code: str, language: str) -> str:
    """Code block markup with premium terminal styling."""
    safe = _esc(code)
    lang = _esc(language or "code")
    return f"""
      <div class="code-wrap">
        <div class="code-head">
          <div class="code-dots">
            <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
          </div>
          <span class="code-filename">{lang}</span>
          <div class="code-actions"><i class="fas fa-terminal" style="color:var(--cyan);font-size:.6rem;opacity:.6"></i></div>
        </div>
        <pre class="code-body"><code id="codeTarget" data-code="{safe}"></code></pre>
      </div>"""


def _hex_to_rgb(hex_color: str) -> str:
    """Convert a hex color like '#00d4ff' to '0, 212, 255'."""
    h = hex_color.lstrip('#')
    if len(h) == 6:
        return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"
    return "0, 212, 255"


def render_slide(
    section: dict[str, Any],
    content: dict[str, Any],
    next_section_id: str = "",
    project_name: str = "",
) -> str:
    """
    Render a complete HTML slide with premium visual styling.
    """
    import re

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

    visual_html = content.get("visual_html") or content.get("slide_html") or ""
    custom_css = content.get("custom_css", "")

    # Clean markdown code blocks from custom html/css if present
    if visual_html:
        visual_html = re.sub(r"^```(?:html)?|```$", "", visual_html.strip(), flags=re.MULTILINE).strip()
    if custom_css:
        custom_css = re.sub(r"^```(?:css)?|```$", "", custom_css.strip(), flags=re.MULTILINE).strip()

    # Category-specific accent color for variety
    category_accents = {
        "intro": "#00d4ff",
        "concept": "#7c3aed",
        "code": "#10b981",
        "setup": "#f59e0b",
        "demo": "#ec4899",
        "summary": "#06b6d4",
    }
    accent = category_accents.get(category, "#00d4ff")

    # Build the main body region
    if visual_html:
        if has_code:
            body_region = f"""
            <div class="visual-layout">
              <div class="visual-content">{visual_html}</div>
              {_code_block_html(code, code_language)}
            </div>
            """
        else:
            body_region = f'<div class="visual-content">{visual_html}</div>'
    elif has_code:
        body_region = _code_block_html(code, code_language)
        if cards:
            body_region = f'<div class="cards">{_cards_html(cards[:2])}</div>' + body_region
    elif cards:
        body_region = f'<div class="cards">{_cards_html(cards[:4])}</div>'
    else:
        body_region = ""

    subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""

    # Auto-advance script
    chain_js = ""
    if next_section_id:
        chain_js = f"""
    player.addEventListener('ended', function() {{
      document.body.classList.add('slide-exit');
      setTimeout(function() {{ window.location.href = '{next_section_id}.html'; }}, 600);
    }});"""

    # Code typewriter script
    code_js = ""
    if has_code:
        code_js = """
  (function() {
    var el = document.getElementById('codeTarget');
    if (!el) return;
    var container = el.parentElement;
    var full = el.getAttribute('data-code') || '';
    var i = 0;
    function type() {
      if (i <= full.length) {
        el.textContent = full.slice(0, i);
        i++;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
        setTimeout(type, 14);
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<style>
  /* ═══════════════════════════════════════════════════════
     GLOBAL RESET & ANTI-SCROLL
  ═══════════════════════════════════════════════════════ */
  *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; cursor:none !important; }}
  *::-webkit-scrollbar {{ display:none !important; }}
  * {{ -ms-overflow-style:none !important; scrollbar-width:none !important; }}

  :root {{
    --cyan: #00d4ff;
    --purple: #a78bfa;
    --accent: {accent};
    --bg: #050816;
    --bg-card: rgba(15, 23, 42, 0.65);
    --border: rgba(0, 212, 255, 0.15);
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --glow-cyan: 0 0 30px rgba(0, 212, 255, 0.15);
    --glow-accent: 0 0 30px rgba({_hex_to_rgb(accent)}, 0.2);
  }}

  html, body {{
    overflow: hidden !important;
    width: 100vw; height: 100vh;
  }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg); color: var(--text);
    min-height: 100vh; position: relative;
    display: flex; flex-direction: column; justify-content: center;
    padding: clamp(24px, 4vh, 48px) clamp(20px, 5vw, 64px);
    animation: fadeIn .7s cubic-bezier(.16,1,.3,1) forwards;
  }}

  html {{ cursor: none !important; }}

  /* Links as plain text */
  a, a:visited, a:hover, a:active {{
    color: var(--cyan); text-decoration: none;
    pointer-events: none; cursor: none !important;
  }}

  /* ═══════════════════════════════════════════════════════
     BACKGROUND EFFECTS
  ═══════════════════════════════════════════════════════ */
  @keyframes fadeIn {{ from {{opacity:0; transform:scale(.97)}} to {{opacity:1; transform:scale(1)}} }}
  @keyframes float {{ 0%,100%{{transform:translate(0,0)}} 25%{{transform:translate(12px,-22px)}} 50%{{transform:translate(-8px,-40px)}} 75%{{transform:translate(18px,-12px)}} }}
  @keyframes floatSlow {{ 0%,100%{{transform:translate(0,0) rotate(0deg)}} 33%{{transform:translate(-15px,-25px) rotate(2deg)}} 66%{{transform:translate(10px,-40px) rotate(-1deg)}} }}
  @keyframes pulse {{ 0%,100%{{opacity:.3}} 50%{{opacity:.8}} }}
  @keyframes scanline {{ 0%{{top:-10%}} 100%{{top:110%}} }}
  @keyframes shimmer {{ 0%{{background-position:-200% 0}} 100%{{background-position:200% 0}} }}
  @keyframes glowPulse {{ 0%,100%{{box-shadow:0 0 8px rgba(0,212,255,.1)}} 50%{{box-shadow:0 0 24px rgba(0,212,255,.25)}} }}
  @keyframes borderGlow {{ 0%,100%{{border-color:rgba(0,212,255,.15)}} 50%{{border-color:rgba(0,212,255,.35)}} }}
  @keyframes breathe {{ 0%,100%{{transform:scale(1)}} 50%{{transform:scale(1.02)}} }}
  @keyframes particleDrift {{ 0%{{transform:translateY(100vh) scale(0); opacity:0}} 10%{{opacity:1}} 90%{{opacity:1}} 100%{{transform:translateY(-10vh) scale(1); opacity:0}} }}
  @keyframes slideInLeft {{ from {{opacity:0; transform:translateX(-30px)}} to {{opacity:1; transform:translateX(0)}} }}
  @keyframes slideInRight {{ from {{opacity:0; transform:translateX(30px)}} to {{opacity:1; transform:translateX(0)}} }}
  @keyframes popIn {{ 0%{{opacity:0; transform:scale(.8) translateY(20px)}} 60%{{transform:scale(1.03) translateY(-3px)}} 100%{{opacity:1; transform:scale(1) translateY(0)}} }}
  @keyframes iconSpin {{ 0%{{transform:rotateY(0deg)}} 100%{{transform:rotateY(360deg)}} }}
  @keyframes dividerSweep {{ 0%{{width:0; opacity:0}} 100%{{width:100%; opacity:.4}} }}
  @keyframes textReveal {{ from {{clip-path:inset(0 100% 0 0)}} to {{clip-path:inset(0 0 0 0)}} }}

  .orb {{
    position:fixed; border-radius:50%; filter:blur(100px);
    opacity:.35; z-index:0; animation:float 12s ease-in-out infinite;
  }}
  .orb.cyan {{
    width:clamp(200px,30vw,420px); height:clamp(200px,30vw,420px);
    background:radial-gradient(circle, var(--cyan), transparent 70%);
    top:-10%; left:-5%;
  }}
  .orb.purple {{
    width:clamp(240px,35vw,480px); height:clamp(240px,35vw,480px);
    background:radial-gradient(circle, var(--purple), transparent 70%);
    bottom:-15%; right:-8%; animation-delay:-6s; animation-duration:16s;
  }}
  .orb.accent {{
    width:clamp(120px,18vw,240px); height:clamp(120px,18vw,240px);
    background:radial-gradient(circle, var(--accent), transparent 70%);
    top:40%; right:15%; opacity:.2; animation:floatSlow 18s ease-in-out infinite;
  }}

  /* Subtle grid with slow drift */
  .grid {{
    position:fixed; inset:0; z-index:0; opacity:.4;
    background-image:
      linear-gradient(rgba(0,212,255,.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,212,255,.03) 1px, transparent 1px);
    background-size:60px 60px;
    animation:breathe 10s ease-in-out infinite;
  }}

  /* Animated scan line */
  .scanline {{
    position:fixed; left:0; width:100%; height:2px; z-index:0;
    background:linear-gradient(90deg, transparent, rgba(0,212,255,.1), rgba(167,139,250,.06), transparent);
    animation:scanline 6s linear infinite;
  }}

  /* Floating particles */
  .particle {{
    position:fixed; border-radius:50%; z-index:0; pointer-events:none;
    animation:particleDrift linear infinite;
  }}

  /* ═══════════════════════════════════════════════════════
     SLIDE EXIT ANIMATION
  ═══════════════════════════════════════════════════════ */
  .slide-exit {{
    animation: slideOut .6s cubic-bezier(.4,0,.2,1) forwards;
  }}
  @keyframes slideOut {{
    to {{ opacity:0; transform:translateY(-20px) scale(.97); }}
  }}

  /* ═══════════════════════════════════════════════════════
     MAIN STAGE
  ═══════════════════════════════════════════════════════ */
  .stage {{
    position:relative; z-index:1;
    max-width:1200px; margin:0 auto; width:100%;
    overflow:hidden;
  }}

  /* Badge — GSAP animated */
  .badge {{
    display:inline-flex; align-items:center; gap:6px;
    border:1px solid var(--accent); color:var(--accent);
    border-radius:100px; padding:5px 18px;
    font-size:clamp(.5rem,.7vw,.62rem); font-weight:700;
    letter-spacing:2.5px; text-transform:uppercase;
    margin-bottom:clamp(12px,1.8vh,20px);
    background:rgba({_hex_to_rgb(accent)}, 0.08);
    backdrop-filter:blur(4px);
    opacity:0; transform:translateY(20px) scale(0.8);
  }}
  .badge::before {{
    content:''; width:7px; height:7px; border-radius:50%;
    background:var(--accent);
    animation:pulse 1.5s ease-in-out infinite;
    box-shadow:0 0 6px var(--accent);
  }}

  /* Hero Title — GSAP animated */
  .hero-title {{
    font-size:clamp(1.5rem,3.5vw,2.8rem); font-weight:800;
    line-height:1.1; margin-bottom:12px;
    background:linear-gradient(90deg, #fff 0%, var(--cyan) 40%, #fff 60%, var(--purple) 100%);
    background-size:200% 100%;
    -webkit-background-clip:text; background-clip:text;
    -webkit-text-fill-color:transparent;
    opacity:0; transform:translateY(30px);
  }}

  /* Subtitle — GSAP animated */
  .subtitle {{
    font-size:clamp(.82rem,1.1vw,1rem); color:var(--text-dim);
    margin-bottom:clamp(16px,2.2vh,28px); max-width:780px;
    line-height:1.6; font-weight:400;
    opacity:0; transform:translateY(20px);
  }}

  /* Divider — GSAP animated */
  .divider {{
    height:1px; margin:4px 0 clamp(16px,2.2vh,28px);
    background:linear-gradient(90deg, transparent, var(--accent), var(--cyan), transparent);
    width:0; opacity:0;
  }}

  /* ═══════════════════════════════════════════════════════
     PREMIUM CARDS
  ═══════════════════════════════════════════════════════ */
  .cards {{
    display:grid;
    grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));
    gap:clamp(12px,1.5vw,18px);
    margin-bottom:24px; overflow:hidden;
  }}

  .card {{
    position:relative;
    background:var(--bg-card);
    backdrop-filter:blur(16px) saturate(1.8);
    -webkit-backdrop-filter:blur(16px) saturate(1.8);
    border:1px solid var(--border);
    border-radius:16px; padding:clamp(16px,2vw,24px);
    opacity:0; transform:scale(0.85) translateY(20px);
    transition:all .35s cubic-bezier(.16,1,.3,1);
    overflow:hidden;
  }}
  .card::before {{
    content:''; position:absolute; inset:-1px;
    border-radius:17px; padding:1px;
    background:linear-gradient(135deg, rgba(0,212,255,.2), transparent 50%, rgba(167,139,250,.2));
    -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite:xor; mask-composite:exclude;
    opacity:0; transition:opacity .35s ease;
  }}
  .card:hover::before, .card:focus::before {{ opacity:1; }}
  .card:hover, .card:focus {{
    transform:translateY(-6px);
    box-shadow:var(--glow-cyan);
    border-color:rgba(0,212,255,.3);
    outline:none;
  }}
  .card-glow {{
    position:absolute; bottom:-20px; left:50%; transform:translateX(-50%);
    width:80%; height:40px; border-radius:50%;
    background:var(--accent); filter:blur(30px); opacity:0;
    transition:opacity .35s ease;
  }}
  .card:hover .card-glow {{ opacity:.15; }}

  .card-icon {{
    width:48px; height:48px; border-radius:14px;
    display:flex; align-items:center; justify-content:center;
    background:linear-gradient(135deg, rgba(0,212,255,.15), rgba(167,139,250,.1));
    border:1px solid rgba(0,212,255,.2);
    margin-bottom:14px; font-size:1.1rem; color:var(--cyan);
    animation:glowPulse 3s ease-in-out infinite, borderGlow 4s ease-in-out infinite;
  }}
  .card-icon i {{
    animation:breathe 3s ease-in-out infinite;
  }}
  .card-title {{
    font-size:clamp(.88rem,1.1vw,1.05rem);
    font-weight:700; margin-bottom:8px; color:#fff;
  }}
  .card-body {{
    font-size:clamp(.78rem,1vw,.88rem); color:var(--text-dim);
    line-height:1.6; overflow-wrap:break-word; word-break:break-word;
  }}

  /* ═══════════════════════════════════════════════════════
     PREMIUM CODE BLOCK
  ═══════════════════════════════════════════════════════ */
  .code-wrap {{
    background:rgba(10, 15, 36, 0.9);
    border:1px solid rgba(0,212,255,.2);
    border-radius:16px; overflow:hidden;
    box-shadow:0 8px 32px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.03);
    backdrop-filter:blur(12px);
    opacity:0; transform:translateY(30px);
  }}
  .code-head {{
    display:flex; align-items:center; padding:12px 18px;
    background:rgba(255,255,255,.02);
    border-bottom:1px solid rgba(0,212,255,.1);
  }}
  .code-dots {{ display:flex; gap:7px; }}
  .dot {{ width:12px; height:12px; border-radius:50%; }}
  .dot.red {{ background:#ff5f57; }}
  .dot.yellow {{ background:#febc2e; }}
  .dot.green {{ background:#28c840; }}
  .code-filename {{
    margin-left:auto; font-family:'JetBrains Mono',monospace;
    font-size:.68rem; color:var(--cyan); letter-spacing:1px;
    text-transform:uppercase; opacity:.7;
  }}
  .code-actions {{ margin-left:12px; }}
  .code-body {{
    margin:0; padding:clamp(14px,2vw,22px); padding-left:clamp(20px,2.5vw,32px);
    font-family:'JetBrains Mono',monospace;
    font-size:clamp(.7rem,.9vw,.88rem); line-height:1.7; color:#c9d8f0;
    white-space:pre-wrap; word-wrap:break-word; word-break:break-all;
    overflow-y:auto; max-height:clamp(250px, 55vh, 600px); min-height:40px;
    border-left:2px solid rgba(0,212,255,.1);
  }}

  /* ═══════════════════════════════════════════════════════
     FOOTER
  ═══════════════════════════════════════════════════════ */
  footer {{
    position:fixed; bottom:clamp(10px,1.5vh,20px); left:0; right:0;
    text-align:center; color:var(--text-dim); font-size:.7rem;
    z-index:1; opacity:.5;
    font-family:'Inter',sans-serif; letter-spacing:.5px;
  }}

  /* ═══════════════════════════════════════════════════════
     PROGRESS BAR (top of screen)
  ═══════════════════════════════════════════════════════ */
  .progress-bar {{
    position:fixed; top:0; left:0; height:3px; z-index:10;
    background:linear-gradient(90deg, var(--cyan), var(--accent), var(--purple));
    animation:progressGrow linear forwards;
    box-shadow:0 0 12px rgba(0,212,255,.4);
  }}

  /* ═══════════════════════════════════════════════════════
     RESPONSIVE
  ═══════════════════════════════════════════════════════ */
  @media (max-width:768px) {{
    body {{ padding:20px 16px; }}
    .hero-title {{ font-size:1.4rem; }}
    .cards {{ grid-template-columns:1fr; }}
    .visual-layout {{ grid-template-columns:1fr !important; gap:16px !important; }}
  }}
  @media (min-width:769px) and (max-width:1024px) {{
    body {{ padding:30px 28px; }}
    .hero-title {{ font-size:2rem; }}
  }}
  @media (min-width:1921px) {{
    .stage {{ max-width:1500px; }}
    .hero-title {{ font-size:3.2rem; }}
    body {{ padding:56px 80px; }}
  }}

  /* ═══════════════════════════════════════════════════════
     VISUAL LAYOUT SYSTEM
  ═══════════════════════════════════════════════════════ */
  .visual-layout {{
    display:grid; grid-template-columns:1.2fr 1fr;
    gap:clamp(16px,2.5vw,32px); align-items:start;
    margin-bottom:22px; overflow:hidden;
  }}
  @media (max-width:900px) {{
    .visual-layout {{ grid-template-columns:1fr; gap:16px; }}
  }}
  .visual-content {{
    opacity:0; transform:translateY(20px);
    width:100%; overflow:hidden;
    overflow-wrap:break-word; word-break:break-word;
  }}
  /* Children start hidden — GSAP reveals them */
  .visual-content > * {{
    opacity:0; transform:translateY(15px);
  }}

  /* Utility classes for LLM-generated visual_html */
  .highlight {{ color:var(--cyan); font-weight:600; }}
  .highlight-purple {{ color:var(--purple); font-weight:600; }}
  .highlight-accent {{ color:var(--accent); font-weight:600; }}

  .glass-box {{
    background:var(--bg-card); backdrop-filter:blur(16px);
    border:1px solid var(--border); border-radius:14px;
    padding:clamp(14px,2vw,22px);
  }}
  .glass-box h2, .glass-box h3 {{
    font-size:clamp(.9rem,1.2vw,1.1rem); font-weight:700;
    margin-bottom:10px; color:#fff;
  }}
  .glass-box p, .glass-box li {{
    font-size:clamp(.78rem,1vw,.88rem); color:var(--text-dim);
    line-height:1.6;
  }}
  .glass-box ul {{ list-style:none; padding:0; }}
  .glass-box li {{ padding:4px 0; }}
  .glass-box li i {{ margin-right:8px; color:var(--cyan); }}

  .flow-step {{
    display:flex; align-items:center; gap:12px;
    padding:12px 16px; margin-bottom:8px;
    background:rgba(0,212,255,.04); border-radius:12px;
    border-left:3px solid var(--cyan);
    transition:all .3s ease;
    opacity:0; transform:translateX(-30px);
  }}
  .flow-step:hover {{
    background:rgba(0,212,255,.08);
    transform:translateX(6px);
    border-left-color:var(--accent);
  }}
  .flow-step .step-num {{
    min-width:32px; height:32px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    background:linear-gradient(135deg, var(--cyan), #0090c0);
    color:#02121a; font-weight:800; font-size:.8rem;
    animation:glowPulse 3s ease-in-out infinite;
  }}

  .command-box {{
    background:rgba(10,15,36,.9); border:1px solid rgba(0,212,255,.15);
    border-radius:10px; padding:12px 18px;
    font-family:'JetBrains Mono',monospace; font-size:clamp(.72rem,.9vw,.85rem);
    color:#10b981; margin:8px 0;
  }}
  .command-box::before {{
    content:'$ '; color:var(--cyan); font-weight:600;
  }}

  /* ═══════════════════════════════════════════════════════
     LLM CUSTOM CSS
  ═══════════════════════════════════════════════════════ */
  {custom_css}
</style>
</head>
<body>
<!-- Background effects -->
<div class="orb cyan" aria-hidden="true"></div>
<div class="orb purple" aria-hidden="true"></div>
<div class="orb accent" aria-hidden="true"></div>
<div class="grid" aria-hidden="true"></div>
<div class="scanline" aria-hidden="true"></div>

<!-- Floating particles -->
<div class="particle" style="width:3px;height:3px;background:var(--cyan);left:10%;animation-duration:12s;animation-delay:0s" aria-hidden="true"></div>
<div class="particle" style="width:2px;height:2px;background:var(--purple);left:25%;animation-duration:15s;animation-delay:2s" aria-hidden="true"></div>
<div class="particle" style="width:4px;height:4px;background:var(--accent);left:50%;animation-duration:10s;animation-delay:4s" aria-hidden="true"></div>
<div class="particle" style="width:2px;height:2px;background:var(--cyan);left:70%;animation-duration:14s;animation-delay:1s" aria-hidden="true"></div>
<div class="particle" style="width:3px;height:3px;background:var(--purple);left:85%;animation-duration:11s;animation-delay:3s" aria-hidden="true"></div>
<div class="particle" style="width:2px;height:2px;background:var(--accent);left:40%;animation-duration:16s;animation-delay:5s" aria-hidden="true"></div>

<!-- Progress bar synced with audio -->
<div class="progress-bar" id="progressBar" style="width:0%"></div>

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
    var bar = document.getElementById('progressBar');

    // ═══════════════════════════════════════════════
    // GSAP MASTER TIMELINE — Cinematic Slide Reveal
    // ═══════════════════════════════════════════════
    var tl = gsap.timeline({{ defaults: {{ ease: 'power3.out' }} }});

    // Phase 1: Badge pop-in (t=0.2s)
    tl.to('.badge', {{
      opacity: 1, y: 0, scale: 1, duration: 0.5,
      ease: 'back.out(1.7)'
    }}, 0.2);

    // Phase 2: Hero title cinematic rise (t=0.5s)
    tl.to('.hero-title', {{
      opacity: 1, y: 0, duration: 0.8,
      ease: 'power4.out'
    }}, 0.5);

    // Phase 3: Subtitle fade in (t=0.9s)
    tl.to('.subtitle', {{
      opacity: 1, y: 0, duration: 0.6
    }}, 0.9);

    // Phase 4: Divider sweep (t=1.1s)
    tl.to('.divider', {{
      width: '100%', opacity: 0.4, duration: 0.7,
      ease: 'power2.inOut'
    }}, 1.1);

    // Phase 5: Visual content container (t=1.3s)
    tl.to('.visual-content', {{
      opacity: 1, y: 0, duration: 0.5
    }}, 1.3);

    // Phase 6: Visual content children — staggered reveal (t=1.5s)
    tl.to('.visual-content > *', {{
      opacity: 1, y: 0, duration: 0.5,
      stagger: 0.2, ease: 'power2.out'
    }}, 1.5);

    // Phase 5 alt: Cards — staggered pop-in with bounce (t=1.3s)
    tl.to('.card', {{
      opacity: 1, y: 0, scale: 1, duration: 0.6,
      stagger: 0.15, ease: 'back.out(1.4)'
    }}, 1.3);

    // Phase 6 alt: Code block reveal (t=1.6s)
    tl.to('.code-wrap', {{
      opacity: 1, y: 0, duration: 0.7,
      ease: 'power3.out'
    }}, 1.6);

    // Phase 7: Flow steps — slide in from left staggered (t=1.5s)
    tl.to('.flow-step', {{
      opacity: 1, x: 0, duration: 0.5,
      stagger: 0.15, ease: 'power2.out'
    }}, 1.5);

    // Phase 8: Glass boxes — staggered pop-in (t=1.4s)
    tl.to('.glass-box', {{
      opacity: 1, y: 0, duration: 0.6,
      stagger: 0.2, ease: 'back.out(1.2)'
    }}, 1.4);

    // Phase 9: Footer fade (t=2.5s)
    tl.to('footer', {{
      opacity: 0.5, duration: 0.8
    }}, 2.5);

    // ═══════════════════════════════════════════════
    // GSAP CONTINUOUS ANIMATIONS (loop forever)
    // ═══════════════════════════════════════════════

    // Title gradient shimmer — continuous sweep
    gsap.to('.hero-title', {{
      backgroundPosition: '200% 0',
      duration: 4, repeat: -1, ease: 'none',
      delay: 2
    }});

    // Card icons — gentle floating pulse
    gsap.to('.card-icon', {{
      boxShadow: '0 0 20px rgba(0,212,255,0.25)',
      duration: 1.5, repeat: -1, yoyo: true, ease: 'sine.inOut',
      stagger: 0.3
    }});
    gsap.to('.card-icon i', {{
      scale: 1.1, duration: 2, repeat: -1, yoyo: true,
      ease: 'sine.inOut', stagger: 0.2
    }});

    // Flow step numbers — glow pulse
    gsap.to('.step-num', {{
      boxShadow: '0 0 16px rgba(0,212,255,0.3)',
      duration: 2, repeat: -1, yoyo: true, ease: 'sine.inOut',
      stagger: 0.4
    }});

    // Code block border glow
    gsap.to('.code-wrap', {{
      borderColor: 'rgba(0,212,255,0.35)',
      duration: 2.5, repeat: -1, yoyo: true, ease: 'sine.inOut',
      delay: 2
    }});

    // Glass-box subtle hover effect (continuous)
    gsap.to('.glass-box', {{
      borderColor: 'rgba(0,212,255,0.25)',
      duration: 3, repeat: -1, yoyo: true, ease: 'sine.inOut',
      stagger: 0.5
    }});

    // Orbs — additional GSAP-driven smooth random movement
    gsap.to('.orb.cyan', {{
      x: 'random(-30, 30)', y: 'random(-30, 30)',
      duration: 6, repeat: -1, yoyo: true, ease: 'sine.inOut'
    }});
    gsap.to('.orb.purple', {{
      x: 'random(-40, 40)', y: 'random(-20, 20)',
      duration: 8, repeat: -1, yoyo: true, ease: 'sine.inOut'
    }});

    // ═══════════════════════════════════════════════
    // PROGRESS BAR — Audio sync
    // ═══════════════════════════════════════════════
    if (player && bar) {{
      player.addEventListener('timeupdate', function() {{
        if (player.duration) {{
          var pct = (player.currentTime / player.duration) * 100;
          gsap.to(bar, {{ width: pct + '%', duration: 0.3, ease: 'none' }});
        }}
      }});
    }}

    // ═══════════════════════════════════════════════
    // SLIDE EXIT — GSAP powered
    // ═══════════════════════════════════════════════
{chain_js}

    // ═══════════════════════════════════════════════
    // CODE TYPEWRITER
    // ═══════════════════════════════════════════════
{code_js}

    // ═══════════════════════════════════════════════
    // AUDIO AUTOPLAY
    // ═══════════════════════════════════════════════
    function tryPlay() {{
      if (!player) return;
      player.muted = false;
      var p = player.play();
      if (p && p.catch) {{ p.catch(function() {{}}); }}
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
        return json.loads(m.group(0), strict=False)
    except json.JSONDecodeError:
        cleaned = re.sub(r",\s*}", "}", m.group(0))
        cleaned = re.sub(r",\s*]", "]", cleaned)
        # Remove control characters except for space, tab, newline, carriage return
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', cleaned)
        try:
            return json.loads(cleaned, strict=False)
        except json.JSONDecodeError as e:
            import logging
            logging.getLogger("va_creator.slide_template").warning(f"Failed parsing JSON from LLM: {e}\nRaw content was: {raw[:500]}...")
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