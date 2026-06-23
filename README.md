# 🎬 VA Creator — AI-Powered Tutorial Video Generator  `v1.3.0`

Command to Run: `venv\Scripts\streamlit.exe run app.py`

> Convert long-form Markdown tutorial scripts into a chain of beautiful, animated HTML slides with synchronized Hindi (Hinglish) audio narration — fully automated using **CrewAI multi-agents**, **NVIDIA LLMs**, and **Sarvam AI TTS**.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.80+-orange.svg)](https://www.crewai.com/)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-NIM-76B900.svg)](https://build.nvidia.com/)
[![Sarvam AI](https://img.shields.io/badge/Sarvam-TTS-purple.svg)](https://www.sarvam.ai/)

---

## ✨ Features

- 🖥️ **Streamlit Web UI Dashboard** — Interactive control panel to manage project folders, chunk scripts, run sections, and monitor real-time generation logs.
- 🤖 **Multi-Agent Pipeline** — CrewAI orchestrates 4 specialized agents (Structurer, Designer, Audio Generator, Publisher) for robust execution.
- 🧠 **NVIDIA NIM LLM Powered** — Uses Llama 3.3 70B by default via OpenAI-compatible endpoints.
- 🎙️ **Hindi/Hinglish TTS** — High-quality, natural regional voice narration via Sarvam AI (`bulbul:v3`).
- 🎨 **Premium Cyber-Themed Slides** — Clean glassmorphism, animated gradients, and responsive layouts powered by CSS3 and GSAP.
- 🛡️ **CSS Sanitization Engine** — Automatically strips LLM overrides of base-template classes to preserve premium styling consistency.
- 🔤 **Devanagari Font Support** — Noto Sans Devanagari for proper Hindi title and content rendering without clipping.
- 📜 **Auto-Scrolling Code Typewriter** — Large code blocks automatically scroll down to follow the typewriter typing animation character-by-character, preventing cutoff.
- ✏️ **Section Script & Style Editor** — Expandable edit panel for every section to directly modify titles, audio script, visual descriptions, code snippets, or custom HTML layouts.
- ⚡ **AI Regeneration vs. Instant Re-Rendering** — Redo slides/audio using the CrewAI LLM designer, or instantly compile direct HTML/CSS code tweaks.
- 🌓 **Dynamic Contrast Theme Support** — Dashboard layout adapts dynamically to Streamlit light and dark themes for clear text readability.
- 📦 **Smart Chunker** — Intelligently parses long scripts into well-paced visual section chunks.
- ♻️ **Smart Resume Support** — Fast resume skips already completed slide/audio files, with incremental saves after each section.
- 🔌 **MCP Server Integration** — Integrates `@remotion/mcp` (Remotion docs), `@genwave/svgmaker-mcp` (SVG generation), `@lottiefiles/creator-mcp` (Lottie animations), `stylelint-mcp` (CSS linting), `@prettier/mcp` (code formatting), `exa-mcp-server` (web search), and `@madhan-g-p/devdocs-mcp-server` (documentation lookup) into the agents to enhance research depth, slide quality, and code accuracy.

---

## 📁 Project Structure

```
VA_creator/
├── .env                    # API keys (DO NOT COMMIT)
├── .gitignore
├── requirements.txt
├── README.md
├── app.py                  # Streamlit Web UI Dashboard
├── main.py                 # CLI Pipeline entrypoint
├── config.py               # LLM + path configuration
├── agents.py               # CrewAI agent definitions
├── tasks.py                # Task templates per agent
├── tools.py                # Sarvam TTS + HTML saver tools
├── slide_template.py       # Deterministic slide renderer + CSS sanitizer
├── chunker.py              # Pre-splits markdown into chunks
├── utils.py                # JSON, progress, helper utilities
├── CHANGELOG.md            # Version history
└── output/                 # Generated artifacts
    ├── sections.json
    ├── progress.json
    ├── index.html          # Master launcher
    ├── section_01.html
    ├── section_01.mp3
    ├── section_02.html
    ├── section_02.mp3
    └── ...
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **NVIDIA API Key** — Get free credits at [build.nvidia.com](https://build.nvidia.com/)
- **Sarvam AI API Key** — Sign up at [sarvam.ai](https://www.sarvam.ai/)
- Windows / macOS / Linux

### 2. Clone the Repo

```bash
git clone https://github.com/nishtechs/VA_creator.git
cd VA_creator
```

### 3. Create a Virtual Environment

**Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SARVAM_API_KEY=your-sarvam-api-key-here
NVIDIA_MODEL=meta/llama-3.3-70b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

> ⚠️ **Never commit `.env`** — it is listed in `.gitignore`.

### 6. Run the Dashboard

Start the interactive Streamlit dashboard:

```bash
venv\Scripts\streamlit.exe run app.py
```

Open `http://localhost:8501/` in your browser to manage, preview, edit, and regenerate your slides.

---

## 🎯 How It Works

```
   ┌──────────────────┐
   │  Markdown Script │
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │   Chunker (re)   │  Splits by SECTION headers + word count
   └────────┬─────────┘
            ▼
   ┌────────────────────────┐
   │  Content Structurer    │  Agent 1 (NVIDIA LLM)
   │  Agent → sections.json │  Extracts audio_text + visual details
   └────────┬───────────────┘
            ▼
   ┌─────────────────────────────────────────┐
   │   For each section (sequential):       │
   │   ┌────────────────┐                   │
   │   │ Visual Designer│ → HTML slide      │
   │   │ (CSS sanitized)│                   │
   │   └───────┬────────┘                   │
   │           ▼                            │
   │   ┌────────────────┐                   │
   │   │ Audio Generator│ → MP3 narration   │
   │   └───────┬────────┘                   │
   │           ▼                            │
   │   ┌────────────────┐                   │
   │   │ HTML Publisher │ Saves + chains    │
   │   └────────────────┘                   │
   │       💾 sections.json saved           │
   └─────────────────────────────────────────┘
            ▼
   ┌──────────────────┐
   │  Master Index    │  Launcher with all slides
   └──────────────────┘
```

### The Agents

| Agent | Role | Tool Used |
| :--- | :--- | :--- |
| **Content Structurer** | Parses script chunks → clean JSON sections | — |
| **Visual Designer** | Generates dark cyber-themed HTML slide page | `@remotion/mcp`, `@genwave/svgmaker-mcp`, `@lottiefiles/creator-mcp`, `stylelint-mcp`, `@prettier/mcp`, `exa-mcp-server`, `@madhan-g-p/devdocs-mcp-server` (MCP Servers via Stdio) |
| **Audio Generator** | Calls Sarvam TTS for Hindi MP3 narration | `SarvamTTSTool` |
| **HTML Publisher** | Injects audio source & slide navigation chains | `HTMLSaverTool` |

---

## ⚙️ Configuration

Tune the pipeline limits in `config.py`:

```python
MAX_WORDS_PER_SECTION = 120     # Each audio section ~30-45 sec
MIN_WORDS_PER_SECTION = 40
```

### NVIDIA LLM Models

You can configure different LLM options in `.env`:

```env
# Fast
NVIDIA_MODEL=meta/llama-3.1-8b-instruct

# Balanced (Default)
NVIDIA_MODEL=meta/llama-3.3-70b-instruct

# Most Capable
NVIDIA_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
```

### Switching TTS Voice

Configure the TTS model parameters in `tools.py`:

```python
"speaker": "shubh",       # Male speaker (default)
# Options: "anushka" (female), "meera", "pavithra", "maitreyi", "arvind", "amol"
"pace": 1.1,              # Speaking speed (0.5 – 2.0)
```

---

## 🔁 Resume, Rerun & Edit Slide content

The generator automatically skips sections where both output files (`.html` and `.mp3`) exist and are valid.

You can modify sections inside the Streamlit Web UI:

1. Open the **✏️ Edit Section Content** expander under any section.
2. Make manual corrections to titles, scripts, visual details, or code.
3. Click **💾 Save & Regenerate (via AI)** to have CrewAI rebuild it, or **⚡ Save & Re-render (Instant)** to update text/code styling changes instantly!

---

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## 📜 License

MIT License. Feel free to use, modify, and distribute.
