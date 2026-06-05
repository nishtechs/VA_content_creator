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
        role="Premium HTML Visual Designer",
        goal=(
            "Generate VISUALLY STUNNING slide content with custom HTML elements and CSS rules "
            "that look like a premium tech keynote presentation. Use glassmorphism panels, "
            "flow-step components, icons, grid layouts, and neon accents. "
            "ALL visible text must be in ENGLISH. Never produce boring plain-text slides."
        ),
        backstory=(
            "You are a world-class frontend designer who has designed keynote presentations for "
            "Apple, Google, and top tech conferences. You specialize in dark-themed educational "
            "visual components with glassmorphism, neon gradients, and smooth CSS animations. "
            "You use pre-built component classes (glass-box, flow-step, command-box) to create "
            "visually rich, structured layouts. Every slide you produce looks premium and polished — "
            "never a boring wall of text. Every word of visible text is in English."
        ),
        llm=nvidia_llm_creative,
        verbose=False,
        allow_delegation=False,
    )

