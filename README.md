\# 📄 README.md

Command to Run this :- "venv\Scripts\streamlit.exe run app.py --server.headless true"

````markdown

\# 🎬 VA Creator — AI-Powered Tutorial Video Generator



> Convert long-form Markdown tutorial scripts into a chain of beautiful, animated HTML slides with synchronized Hindi (Hinglish) audio narration — fully automated using \*\*CrewAI multi-agents\*\*, \*\*NVIDIA LLMs\*\*, and \*\*Sarvam AI TTS\*\*.



\[!\[Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

\[!\[CrewAI](https://img.shields.io/badge/CrewAI-0.80+-orange.svg)](https://www.crewai.com/)

\[!\[NVIDIA](https://img.shields.io/badge/NVIDIA-NIM-76B900.svg)](https://build.nvidia.com/)

\[!\[Sarvam AI](https://img.shields.io/badge/Sarvam-TTS-purple.svg)](https://www.sarvam.ai/)



\---



\## ✨ Features



\- 🤖 \*\*Multi-Agent Pipeline\*\* — CrewAI orchestrates 4 specialized agents (Structurer, Designer, Audio Generator, Publisher)

\- 🧠 \*\*NVIDIA LLM Powered\*\* — Uses NVIDIA NIM (Llama 3.3 70B by default) via OpenAI-compatible API

\- 🎙️ \*\*Hindi/Hinglish TTS\*\* — Natural voice narration via Sarvam AI (`bulbul:v3` model)

\- 🎨 \*\*Dark Cyber-Themed Slides\*\* — Glassmorphism, animated gradients, responsive HTML5/CSS3

\- 🔗 \*\*Auto-Chained Playback\*\* — Each slide auto-advances to the next when audio ends

\- 📦 \*\*Smart Chunking\*\* — Splits long scripts into 15-25 micro-sections for better pacing

\- ♻️ \*\*Resume Support\*\* — Skips already-generated slides on re-run

\- ⚡ \*\*Parallel Processing\*\* — Audio + Visual generated concurrently (2x faster)

\- 🔁 \*\*Retry Logic\*\* — Exponential backoff on API failures

\- 🏠 \*\*Master Index Page\*\* — Beautiful launcher with all slides listed

\- 💾 \*\*JSON Persistence\*\* — Sections and progress saved for inspection/editing



\---



\## 📁 Project Structure



```



VA\\\_creator/

├── .env                    # API keys (DO NOT COMMIT)

├── .gitignore

├── requirements.txt

├── README.md

├── main.py                 # Pipeline entrypoint

├── config.py               # LLM + path configuration

├── agents.py               # CrewAI agent definitions

├── tasks.py                # Task templates per agent

├── tools.py                # Sarvam TTS + HTML saver tools

├── chunker.py              # Pre-splits markdown into chunks

├── utils.py                # JSON, progress, helper utilities

└── output/                 # Generated artifacts

├── sections.json

├── progress.json

├── index.html          # Master launcher

├── section\\\_01.html

├── section\\\_01.mp3

├── section\\\_02.html

├── section\\\_02.mp3

└── …



````



\---



\## 🚀 Quick Start



\### 1. Prerequisites



\- \*\*Python 3.10+\*\*

\- \*\*NVIDIA API Key\*\* — Get free credits at \[build.nvidia.com](https://build.nvidia.com/)

\- \*\*Sarvam AI API Key\*\* — Sign up at \[sarvam.ai](https://www.sarvam.ai/)

\- Windows / macOS / Linux



\### 2. Clone the Repo



```bash

git clone https://github.com/your-username/VA\_creator.git

cd VA\_creator

````



\### 3. Create a Virtual Environment



\*\*Windows (PowerShell):\*\*



```powershell

python -m venv venv

venv\\Scripts\\activate

```



\*\*macOS / Linux:\*\*



```bash

python -m venv venv

source venv/bin/activate

```



\### 4. Install Dependencies



```bash

pip install -r requirements.txt

```



\### 5. Configure Environment Variables



Create a `.env` file in the project root:



```env

NVIDIA\_API\_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

SARVAM\_API\_KEY=your-sarvam-api-key-here

NVIDIA\_MODEL=meta/llama-3.3-70b-instruct

NVIDIA\_BASE\_URL=https://integrate.api.nvidia.com/v1

```



> ⚠️ \*\*Never commit `.env`\*\* — it's already in `.gitignore`.



\### 6. Add Your Tutorial Script



Open `main.py` and paste your Markdown tutorial script into the `RAW\_SCRIPT` variable:



```python

RAW\_SCRIPT = """

\# 🎬 Your Tutorial Title



\### 🎬 SECTION 1: HOOK + INTRO (0:00 – 1:30)

> "Namaste doston! ..."



\### 🎬 SECTION 2: WHAT WE'RE BUILDING (1:30 – 3:00)

> "Toh pehle samajhte hain ..."



... (rest of your script)

"""

```



\### 7. Run the Pipeline



```bash

python main.py

```



You'll see real-time progress:



```

🚀 TUTORIAL GENERATOR — Advanced Pipeline

\[1/3] Pre-splitting script into chunks...

&#x20;  ✓ Created 18 chunks

\[2/3] Structuring chunks into sections...

\[████████████████████████████████████████] 18/18 chunk 18

💾 Saved sections.json (18 sections)

\[3/3] Generating 18 slides...

&#x20; 🎨 \[1/18] section\_01: Customer Support Bot Intro

&#x20; 🔊 TTS chunk 1/1 (387 chars)

&#x20; ...

🎉 PIPELINE COMPLETE!

📂 Open: C:/Users/.../output/index.html

```



\### 8. View Your Slides



Open `output/index.html` in any modern browser. Click \*\*▶ Play From Start\*\* — the slides will auto-advance with synchronized Hindi audio narration.



\---



\## 🎯 How It Works



```

&#x20;  ┌──────────────────┐

&#x20;  │  Markdown Script │

&#x20;  └────────┬─────────┘

&#x20;           ▼

&#x20;  ┌──────────────────┐

&#x20;  │   Chunker (re)   │  Splits by SECTION headers + word count

&#x20;  └────────┬─────────┘

&#x20;           ▼

&#x20;  ┌────────────────────────┐

&#x20;  │  Content Structurer    │  Agent 1 (NVIDIA LLM)

&#x20;  │  Agent → sections.json │  Extracts audio\_text + visual\_brief

&#x20;  └────────┬───────────────┘

&#x20;           ▼

&#x20;  ┌─────────────────────────────────────────┐

&#x20;  │   For each section (in parallel):       │

&#x20;  │   ┌────────────────┐ ┌────────────────┐ │

&#x20;  │   │ Visual Designer│ │ Audio Generator│ │

&#x20;  │   │ Agent → HTML   │ │ Agent → MP3    │ │

&#x20;  │   └───────┬────────┘ └───────┬────────┘ │

&#x20;  │           └──────┬───────────┘          │

&#x20;  │                  ▼                      │

&#x20;  │         ┌────────────────┐              │

&#x20;  │         │ HTML Publisher │              │

&#x20;  │         │ Saves + chains │              │

&#x20;  │         └────────────────┘              │

&#x20;  └─────────────────────────────────────────┘

&#x20;           ▼

&#x20;  ┌──────────────────┐

&#x20;  │  Master Index    │  Launcher with all slides

&#x20;  └──────────────────┘

```



\### The 4 Agents



| Agent                   | Role                                         | Tool Used         |

| ----------------------- | -------------------------------------------- | ----------------- |

| \*\*Content Structurer\*\*  | Parses chunks → clean JSON sections          | —                 |

| \*\*Visual Designer\*\*     | Generates animated dark-themed HTML          | —                 |

| \*\*Audio Generator\*\*     | Calls Sarvam TTS for Hindi MP3               | `SarvamTTSTool`   |

| \*\*HTML Publisher\*\*      | Saves HTML + injects audio + chain redirects | `HTMLSaverTool`   |



\---



\## ⚙️ Configuration



Tune the pipeline in `config.py`:



```python

MAX\_WORDS\_PER\_SECTION = 120     # Each audio section \~30-45 sec

MIN\_WORDS\_PER\_SECTION = 40

```



\### Switching NVIDIA Models



Edit `.env`:



```env

\# Fastest

NVIDIA\_MODEL=meta/llama-3.1-8b-instruct



\# Balanced (default)

NVIDIA\_MODEL=meta/llama-3.3-70b-instruct



\# Most capable

NVIDIA\_MODEL=nvidia/llama-3.1-nemotron-70b-instruct



\# Mixtral

NVIDIA\_MODEL=mistralai/mixtral-8x7b-instruct-v0.1

```



\### Switching TTS Voice



Edit `tools.py` → `SarvamTTSTool.\_call\_sarvam`:



```python

"speaker": "shubh",       # Male — default

\# Options: "anushka" (female), "meera", "pavithra", "maitreyi", "arvind", "amol"

"pace": 1.1,              # 0.5 – 2.0

```



\---



\## ♻️ Resume / Re-run



The pipeline \*\*automatically skips\*\* any section where:



\- ✅ `output/section\_XX.html` exists, \*\*AND\*\*

\- ✅ `output/section\_XX.mp3` exists and is > 1 KB



To regenerate a specific section, just delete its `.html` and `.mp3` files and run `main.py` again.



To restart from scratch, delete the entire `output/` folder.



\---



\## 🐛 Troubleshooting



\### `pydantic ValidationError: llm.str ...`

You're passing a LangChain LLM directly. Use CrewAI's `LLM` class (already fixed in `config.py`).



\### `Sarvam TTS returns 400/422`

\- Check your API key in `.env`

\- Verify text isn't longer than 450 chars per chunk (handled automatically)

\- Ensure `target\_language\_code` matches the text language



\### Audio doesn't autoplay in browser

\- Modern browsers block autoplay until user interacts. Click anywhere on the page once.

\- The script has a built-in fallback that plays on first click/scroll.



\### `NVIDIA API: 401 Unauthorized`

\- Generate a fresh key at \[build.nvidia.com](https://build.nvidia.com/)

\- Make sure the key starts with `nvapi-`



\### Slides look broken or empty

\- Check `output/sections.json` to see if structuring worked

\- Re-run — the visual agent occasionally needs retries on complex sections



\---



\## 📊 Sample `.gitignore`



```gitignore

venv/

.env

\_\_pycache\_\_/

\*.pyc

output/

.DS\_Store

```



\---



\## 🎓 Use Cases



\- \*\*YouTube Tutorial Creators\*\* — Generate visual slides from a Hindi script

\- \*\*EdTech Platforms\*\* — Auto-convert course content into interactive lessons

\- \*\*Internal Training\*\* — Build company onboarding tutorials in regional languages

\- \*\*Documentation\*\* — Animated walkthroughs of code/concepts

\- \*\*Marketing\*\* — Product feature explainers with localized voice-over



\---



\## 🛠️ Tech Stack



| Component      | Technology                              |

| -------------- | --------------------------------------- |

| Orchestration  | \[CrewAI](https://www.crewai.com/)       |

| LLM            | NVIDIA NIM (Llama 3.3 70B)              |

| TTS            | \[Sarvam AI](https://www.sarvam.ai/) Bulbul v3 |

| LLM Router     | LiteLLM (built into CrewAI)             |

| Frontend       | Vanilla HTML5 + CSS3 + JS               |

| Fonts          | Poppins + JetBrains Mono                |



\---



\## 🗺️ Roadmap



\- \[ ] 🎙️ Multi-speaker alternation (male/female narration)

\- \[ ] 🎵 Background music with audio ducking

\- \[ ] 🖼️ AI-generated diagrams (NVIDIA image gen / DALL-E)

\- \[ ] 📹 Auto-record HTML chain to MP4 via Playwright

\- \[ ] 🌐 Multi-language parallel generation (Hindi + English + Tamil)

\- \[ ] 🐳 Docker container

\- \[ ] 🎨 Multiple theme presets (Cyber / Minimal / Neon / Corporate)

\- \[ ] 📈 Slide analytics dashboard



\---



\## 🤝 Contributing



1\. Fork the repo

2\. Create a feature branch (`git checkout -b feature/amazing-feature`)

3\. Commit your changes (`git commit -m 'Add amazing feature'`)

4\. Push to the branch (`git push origin feature/amazing-feature`)

5\. Open a Pull Request



\---



\## 📜 License



MIT License — feel free to use, modify, and distribute.



\---



\## 🙏 Acknowledgments



\- \[CrewAI](https://www.crewai.com/) for the brilliant multi-agent framework

\- \[NVIDIA NIM](https://build.nvidia.com/) for free, fast LLM inference

\- \[Sarvam AI](https://www.sarvam.ai/) for high-quality Indian-language TTS

\- The open-source community ❤️



\---



\## 📬 Contact



\- \*\*Author:\*\* Your Name

\- \*\*Email:\*\* your.email@example.com

\- \*\*GitHub:\*\* \[@your-username](https://github.com/your-username)



\---



<p align="center">Made with ❤️ for Hindi-speaking AI educators</p>

```



\---



\## 📌 How to Use This README



1\. Save the content above as `README.md` in your project root (`C:\\Users\\nisha\\OneDrive\\Desktop\\VA\_creator\\README.md`)

2\. Replace placeholders:

&#x20;  - `your-username` → your actual GitHub username

&#x20;  - `Your Name` → your real name

&#x20;  - `your.email@example.com` → your email

3\. (Optional) Add screenshots:

&#x20;  ```markdown

&#x20;  ## 📸 Screenshots

&#x20;  !\[Master Index](docs/index-screenshot.png)

&#x20;  !\[Slide Example](docs/slide-screenshot.png)

&#x20;  ```

4\. Commit and push:

&#x20;  ```bash

&#x20;  git add README.md

&#x20;  git commit -m "Add comprehensive README"

&#x20;  git push origin main

&#x20;  ```



Let me know if you want me to add a \*\*LICENSE file\*\*, \*\*CONTRIBUTING.md\*\*, or \*\*GitHub Actions workflow\*\* next! 🚀

