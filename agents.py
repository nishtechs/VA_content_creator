"""
CrewAI Agent definitions.

IMPORTANT: Agents are created via factory functions (not module-level singletons)
because each CrewAI Agent holds a stateful internal executor. Sharing a single
agent instance across concurrent or retried crew runs causes:
    "RuntimeError: Executor is already running."
Always build a fresh agent per crew invocation.
"""

from crewai import Agent
from config import nvidia_llm, nvidia_llm_creative


def make_chunk_structurer_agent() -> Agent:
    """Create a fresh Content Structurer agent."""
    return Agent(
        role="Content Structurer",
        goal=(
            "Convert raw markdown chunks into clean structured JSON sections. "
            "The 'audio_text' (spoken narration) MUST be in Hindi/Hinglish. "
            "The 'title' and 'visual_brief' (used for the on-screen slide) MUST be in English."
        ),
        backstory=(
            "You are an expert at distilling tutorial content into bite-sized educational slides. "
            "You separate spoken narration from visual elements with surgical precision. "
            "You keep the spoken audio narration in Hindi while keeping all on-screen slide text in English. "
            "You always return valid JSON with no markdown fences."
        ),
        llm=nvidia_llm,
        verbose=False,
        allow_delegation=False,
    )


def make_visual_designer_agent() -> Agent:
    """Create a fresh HTML Visual Designer agent."""
    return Agent(
        role="HTML Visual Designer",
        goal=(
            "Generate stunning animated HTML slides matching the dark cyber-themed design system. "
            "ALL visible text on the slide must be written in ENGLISH."
        ),
        backstory=(
            "You are a senior frontend designer specializing in dark-themed educational micro-slides "
            "with glassmorphism, gradients, and smooth CSS animations. You always produce complete, "
            "valid HTML documents with proper accessibility attributes (aria-labels, semantic headings, "
            "keyboard navigation support). "
            "Every word of visible text you put on the slide is in English."
        ),
        llm=nvidia_llm_creative,
        verbose=False,
        allow_delegation=False,
    )
