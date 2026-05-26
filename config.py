import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
# NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "mistralai/mistral-medium-3.5-128b")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# CrewAI LLM using NVIDIA's OpenAI-compatible endpoint via LiteLLM
nvidia_llm = LLM(
    model=f"openai/{NVIDIA_MODEL}",   # 'openai/' prefix tells LiteLLM to use OpenAI-compatible API
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
    temperature=0.3,
    max_tokens=4096,
)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)