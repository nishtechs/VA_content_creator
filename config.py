"""
Configuration module with validation.
Loads environment variables and sets up LLM instances.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

# ─── Logging ────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("va_creator")

# ─── API Keys ───────────────────────────────────────────────────────────────
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# ─── Startup Validation ─────────────────────────────────────────────────────
def validate_config():
    """Validate required configuration at startup."""
    errors = []
    if not NVIDIA_API_KEY:
        errors.append("NVIDIA_API_KEY is missing in .env")
    if not SARVAM_API_KEY:
        errors.append("SARVAM_API_KEY is missing in .env")
    if errors:
        for e in errors:
            logger.error(f"❌ {e}")
        sys.exit(1)

validate_config()

# ─── LLM Instances ──────────────────────────────────────────────────────────
nvidia_llm = LLM(
    model=f"openai/{NVIDIA_MODEL}",
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
    temperature=0.3,
    max_tokens=8192,
)

nvidia_llm_creative = LLM(
    model=f"openai/{NVIDIA_MODEL}",
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
    temperature=0.7,
    max_tokens=8192,
)

# ─── Paths ───────────────────────────────────────────────────────────────────
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
SECTIONS_JSON = os.path.join(OUTPUT_DIR, "sections.json")
PROGRESS_JSON = os.path.join(OUTPUT_DIR, "progress.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Chunking Settings ──────────────────────────────────────────────────────
MAX_WORDS_PER_SECTION: int = 120
MIN_WORDS_PER_SECTION: int = 40

# ─── TTS Settings ───────────────────────────────────────────────────────────
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "hi-IN")
TTS_SPEAKER = os.getenv("TTS_SPEAKER", "shubh")
TTS_PACE = float(os.getenv("TTS_PACE", "1.1"))
TTS_MODEL = os.getenv("TTS_MODEL", "bulbul:v3")

# ─── Parallelism ────────────────────────────────────────────────────────────
# Keep low to respect NVIDIA NIM free-tier rate limits (~40 req/min)
MAX_PARALLEL_SECTIONS: int = int(os.getenv("MAX_PARALLEL_SECTIONS", "2"))
