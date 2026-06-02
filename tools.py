"""
Tools module — Sarvam TTS and HTML Saver.
These are now callable both as CrewAI tools AND as direct Python functions.
"""

import os
import re
import io
import time
import random
import logging
import requests
from typing import ClassVar, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pydub import AudioSegment

from config import SARVAM_API_KEY, TTS_LANGUAGE, TTS_SPEAKER, TTS_PACE, TTS_MODEL
from project import audio_path, html_path

logger = logging.getLogger("va_creator.tools")


# ─── TTS Tool ───────────────────────────────────────────────────────────────

class TTSInput(BaseModel):
    text: str = Field(..., description="Hindi text to convert to speech")
    filename: str = Field(..., description="Output filename without extension")


class SarvamTTSTool(BaseTool):
    name: str = "Sarvam TTS Generator"
    description: str = "Converts Hindi text to MP3 using Sarvam AI. Handles long text via chunking."
    args_schema: Type[BaseModel] = TTSInput

    MAX_CHARS: ClassVar[int] = 450  # Sarvam limit per call

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks respecting sentence boundaries."""
        sentences = re.split(r'(?<=[.!?।])\s+', text)
        chunks: list[str] = []
        current = ""
        for s in sentences:
            if len(current) + len(s) < self.MAX_CHARS:
                current += " " + s
            else:
                if current:
                    chunks.append(current.strip())
                current = s
        if current:
            chunks.append(current.strip())
        return chunks if chunks else [text[:self.MAX_CHARS]]

    def _call_sarvam(self, text: str, retries: int = 3) -> bytes:
        """Call Sarvam TTS API with exponential backoff + jitter."""
        api_url = "https://api.sarvam.ai/text-to-speech/stream"
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "target_language_code": TTS_LANGUAGE,
            "speaker": TTS_SPEAKER,
            "model": TTS_MODEL,
            "pace": TTS_PACE,
            "speech_sample_rate": 22050,
            "output_audio_codec": "mp3",
            "enable_preprocessing": True
        }
        for attempt in range(retries):
            try:
                with requests.post(api_url, headers=headers, json=payload, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    return b"".join(chunk for chunk in r.iter_content(8192) if chunk)
            except Exception as e:
                if attempt == retries - 1:
                    raise
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"TTS attempt {attempt+1} failed: {e}. Retrying in {wait:.1f}s...")
                time.sleep(wait)
        return b""

    def _normalize_audio(self, audio_bytes: bytes) -> bytes:
        """Normalize audio volume across chunks using pydub."""
        try:
            audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            # Normalize to -20 dBFS
            change_in_dBFS = -20.0 - audio.dBFS
            normalized = audio.apply_gain(change_in_dBFS)
            buffer = io.BytesIO()
            normalized.export(buffer, format="mp3")
            return buffer.getvalue()
        except Exception as e:
            logger.warning(f"Audio normalization failed (using raw): {e}")
            return audio_bytes

    def _run(self, text: str, filename: str) -> str:
        output_path = audio_path(filename)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"Audio already exists (skipped): {output_path}")
            return f"Audio already exists (skipped): {output_path}"

        try:
            chunks = self._split_text(text)
            audio_bytes = b""
            for i, chunk in enumerate(chunks):
                logger.info(f"  🔊 TTS chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
                audio_bytes += self._call_sarvam(chunk)

            # Normalize volume
            audio_bytes = self._normalize_audio(audio_bytes)

            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"Audio saved: {output_path} ({len(audio_bytes)} bytes)")
            return f"Audio saved: {output_path} ({len(audio_bytes)} bytes)"
        except Exception as e:
            logger.error(f"Error generating audio for {filename}: {e}")
            return f"Error generating audio: {str(e)}"


# ─── HTML Saver Tool ────────────────────────────────────────────────────────

class HTMLSaveInput(BaseModel):
    html_content: str = Field(..., description="Complete HTML code")
    filename: str = Field(..., description="Output filename without extension")
    audio_filename: str = Field(..., description="Audio filename without .mp3")
    next_html: str = Field(default="", description="Next HTML to redirect to")


class HTMLSaverTool(BaseTool):
    name: str = "HTML File Saver"
    description: str = "Saves HTML with audio binding and auto-redirect."
    args_schema: Type[BaseModel] = HTMLSaveInput

    def _run(self, html_content: str, filename: str, audio_filename: str, next_html: str = "") -> str:
        # Fix audio src
        html_content = re.sub(
            r'<source\s+src="[^"]*"\s+type="audio/mpeg">',
            f'<source src="{audio_filename}.mp3" type="audio/mpeg">',
            html_content
        )

        # Inject transition + redirect script
        redirect_script = ""
        if next_html:
            redirect_script = f"""
<script>
  (function() {{
    const player = document.getElementById('audioPlayer');
    if (player) {{
      player.addEventListener('ended', function() {{
        document.body.style.opacity = '0';
        document.body.style.transition = 'opacity 0.5s ease';
        setTimeout(function() {{
          window.location.href = '{next_html}.html';
        }}, 500);
      }});
    }}
  }})();
</script>
"""
        # Add page transition CSS
        transition_css = """
<style>
  body { animation: fadeIn 0.5s ease forwards; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
"""
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", f"{transition_css}</head>")

        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{redirect_script}</body>")
        else:
            html_content += redirect_script

        # Add accessibility attributes
        html_content = html_content.replace("<html>", '<html lang="en">')
        if 'role="main"' not in html_content:
            html_content = html_content.replace("<body>", "<body>\n<main role=\"main\" aria-label=\"Tutorial slide\">")
            html_content = html_content.replace("</body>", "</main>\n</body>")

        output_path = html_path(filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"HTML saved: {output_path}")
        return f"HTML saved: {output_path}"


# ─── Direct function wrappers (bypass LLM for deterministic tasks) ───────────

def generate_audio_direct(text: str, filename: str) -> str:
    """Call TTS directly without LLM agent overhead."""
    tool = SarvamTTSTool()
    return tool._run(text=text, filename=filename)


def save_html_direct(html_content: str, filename: str, audio_filename: str, next_html: str = "") -> str:
    """Save HTML directly without LLM agent overhead."""
    tool = HTMLSaverTool()
    return tool._run(
        html_content=html_content,
        filename=filename,
        audio_filename=audio_filename,
        next_html=next_html
    )
