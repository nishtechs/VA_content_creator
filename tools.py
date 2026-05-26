import os
import re
import json
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from config import SARVAM_API_KEY, OUTPUT_DIR


class TTSInput(BaseModel):
    text: str = Field(..., description="Hindi text to convert to speech")
    filename: str = Field(..., description="Output filename without extension, e.g., 'section_1'")


class SarvamTTSTool(BaseTool):
    name: str = "Sarvam TTS Generator"
    description: str = "Converts Hindi text to MP3 audio using Sarvam AI streaming TTS."
    args_schema: Type[BaseModel] = TTSInput

    def _run(self, text: str, filename: str) -> str:
        api_url = "https://api.sarvam.ai/text-to-speech/stream"
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "target_language_code": "hi-IN",
            "speaker": "shubh",
            "model": "bulbul:v3",
            "pace": 1.1,
            "speech_sample_rate": 22050,
            "output_audio_codec": "mp3",
            "enable_preprocessing": True
        }

        output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp3")
        try:
            with requests.post(api_url, headers=headers, json=payload, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return f"Audio saved successfully: {output_path}"
        except Exception as e:
            return f"Error generating audio: {str(e)}"


class HTMLSaveInput(BaseModel):
    html_content: str = Field(..., description="Complete HTML code to save")
    filename: str = Field(..., description="Output filename without extension")
    audio_filename: str = Field(..., description="Corresponding audio filename (without .mp3)")
    next_html: str = Field(default="", description="Next HTML filename to redirect to after audio ends")


class HTMLSaverTool(BaseTool):
    name: str = "HTML File Saver"
    description: str = "Saves HTML content with audio binding and auto-redirect to next slide."
    args_schema: Type[BaseModel] = HTMLSaveInput

    def _run(self, html_content: str, filename: str, audio_filename: str, next_html: str = "") -> str:
        # Inject correct audio src
        html_content = re.sub(
            r'<source\s+src="[^"]*"\s+type="audio/mpeg">',
            f'<source src="{audio_filename}.mp3" type="audio/mpeg">',
            html_content
        )

        # Inject redirect script when audio ends
        redirect_script = ""
        if next_html:
            redirect_script = f"""
<script>
  document.getElementById('audioPlayer').addEventListener('ended', function() {{
      window.location.href = '{next_html}.html';
  }});
</script>
"""
        html_content = html_content.replace("</body>", f"{redirect_script}</body>")

        output_path = os.path.join(OUTPUT_DIR, f"{filename}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return f"HTML saved: {output_path}"