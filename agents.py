"""
CrewAI Agent definitions.

IMPORTANT: Agents are created via factory functions (not module-level singletons)
because each CrewAI Agent holds a stateful internal executor. Sharing a single
agent instance across concurrent or retried crew runs causes:
    "RuntimeError: Executor is already running."
Always build a fresh agent per crew invocation.
"""

import os
from crewai import Agent
from crewai.mcp import MCPServerStdio
from crewai_tools import SerperDevTool
from config import nvidia_llm, nvidia_llm_creative


def make_research_scriptwriter_agent() -> Agent:
    """Create a fresh Technical Researcher & Scriptwriter agent."""
    exa_mcp = MCPServerStdio(
        command="npx",
        args=["-y", "exa-mcp-server"],
        env={"EXA_API_KEY": os.getenv("EXA_API_KEY", "")}
    )
    return Agent(
        role="Technical Researcher & Scriptwriter",
        goal=(
            "Search the web for accurate technical information on the requested topic and "
            "generate a comprehensive, structured sections JSON array for tutorial slides."
        ),
        backstory=(
            "You are an expert technical writer and researcher who scours the internet to gather "
            "accurate, up-to-date information and synthesizes it into engaging educational tutorials. "
            "You specialize in creating structured sections/slides directly in JSON format, separating "
            "spoken narration in Hindi Devanagari from visual content in English."
        ),
        tools=[SerperDevTool()],
        llm=nvidia_llm,
        mcps=[exa_mcp],
        verbose=False,
        allow_delegation=False,
    )


def make_chunk_structurer_agent() -> Agent:
    """Create a fresh Content Structurer agent."""
    return Agent(
        role="Content Structurer",
        goal=(
            "Convert raw markdown chunks into clean structured JSON sections. "
            "The 'audio_text' (spoken narration) MUST be in Hindi/Hinglish. "
            "The 'title' and 'visual' (used for the on-screen slide) MUST be in English."
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
    remotion_mcp = MCPServerStdio(
        command="npx",
        args=["-y", "@remotion/mcp@latest"]
    )
    svg_mcp = MCPServerStdio(
        command="npx",
        args=["-y", "@mcp/svg-generator"]
    )
    lottie_mcp = MCPServerStdio(
        command="npx",
        args=["-y", "@lottiefiles/creator-mcp@latest"]
    )
    stylelint_mcp = MCPServerStdio(
        command="npx",
        args=["-y", "stylelint-mcp"]
    )
    prettier_mcp = MCPServerStdio(
        command="npx",
        args=["-y", "prettier-mcp"]
    )
    exa_mcp = MCPServerStdio(
        command="npx",
        args=["-y", "exa-mcp-server"],
        env={"EXA_API_KEY": os.getenv("EXA_API_KEY", "")}
    )
    devdocs_mcp = MCPServerStdio(
        command="npx",
        args=["-y", "@madhan-g-p/devdocs-mcp-server"]
    )
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
        mcps=[remotion_mcp, svg_mcp, lottie_mcp, stylelint_mcp, prettier_mcp, exa_mcp, devdocs_mcp],
        verbose=False,
        allow_delegation=False,
    )

