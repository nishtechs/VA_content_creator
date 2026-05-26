from crewai import Agent
from config import nvidia_llm
from tools import SarvamTTSTool, HTMLSaverTool

# Agent 1: Parses the script into sections
script_parser_agent = Agent(
    role="Tutorial Script Parser",
    goal="Parse markdown tutorial scripts into structured sections, separating spoken narration from visual elements.",
    backstory=(
        "You are an expert content analyst specialized in breaking down educational scripts. "
        "You identify section boundaries, extract Hindi narration text (audio), and identify "
        "visual cues, code blocks, and screen descriptions (visuals)."
    ),
    llm=nvidia_llm,
    verbose=True,
    allow_delegation=False,
)

# Agent 2: Generates audio text (cleaned Hindi narration)
audio_script_agent = Agent(
    role="Hindi Audio Script Writer",
    goal="Clean and prepare Hindi narration text for TTS conversion, removing any markdown or stage directions.",
    backstory=(
        "You are a Hindi voice-over scriptwriter. You take raw section content and extract "
        "only the spoken Hindi (Hinglish) lines, making them sound natural for TTS narration. "
        "You preserve the conversational tone."
    ),
    llm=nvidia_llm,
    verbose=True,
    allow_delegation=False,
)

# Agent 3: Generates HTML visuals
visual_designer_agent = Agent(
    role="HTML Visual Designer",
    goal="Generate beautiful, animated HTML visual slides matching the section content using the provided design template.",
    backstory=(
        "You are a senior frontend designer who creates stunning dark-themed animated HTML slides "
        "with glassmorphism, gradients, and smooth animations. You strictly follow the provided "
        "HTML template style (dark background, cyan/purple accents, Poppins font, animated cards) "
        "while customizing content for each section."
    ),
    llm=nvidia_llm,
    verbose=True,
    allow_delegation=False,
)

# Agent 4: Audio generator (uses Sarvam TTS)
audio_generator_agent = Agent(
    role="Audio File Generator",
    goal="Convert Hindi narration text into MP3 audio files using Sarvam AI TTS.",
    backstory="You are responsible for generating high-quality Hindi audio files for each tutorial section.",
    llm=nvidia_llm,
    tools=[SarvamTTSTool()],
    verbose=True,
    allow_delegation=False,
)

# Agent 5: HTML file saver with audio binding + chaining
html_saver_agent = Agent(
    role="HTML Publisher",
    goal="Save HTML files with correct audio bindings and chain them so each slide auto-advances to the next.",
    backstory="You manage the final publishing step, ensuring audio sync and slide-to-slide navigation.",
    llm=nvidia_llm,
    tools=[HTMLSaverTool()],
    verbose=True,
    allow_delegation=False,
)