"""
Project context — manages per-project output folders.

All generated files (sections.json, progress.json, index.html, section_XX.html/.mp3)
are stored under: <OUTPUT_ROOT>/<project_slug>/

The active project is process-global state set via set_active_project().
Path-resolving helpers are used everywhere instead of import-time constants so that
switching projects at runtime takes effect immediately across all modules.
"""

import os
import re
import logging

from config import OUTPUT_DIR as OUTPUT_ROOT

logger = logging.getLogger("va_creator.project")

# Process-global active project and theme state
_state: dict[str, str | None] = {
    "project": None,
    "theme": "Dark Cyber (Default)"
}


def slugify(name: str) -> str:
    """Convert a human project name into a safe folder name."""
    slug = re.sub(r"[^\w\s-]", "", (name or "").strip()).lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    return slug or "default"


def set_active_project(name: str) -> str:
    """Set the active project (by human name) and ensure its folder exists.
    Returns the resolved slug.
    """
    slug = slugify(name)
    _state["project"] = slug
    os.makedirs(get_project_dir(), exist_ok=True)
    logger.info(f"Active project set to '{slug}' ({get_project_dir()})")
    return slug


def get_active_project() -> str | None:
    """Return the active project slug, or None if not set."""
    return _state["project"]


def set_active_theme(theme_name: str):
    _state["theme"] = theme_name


def get_active_theme() -> str:
    return _state.get("theme", "Dark Cyber (Default)")


def get_project_dir() -> str:
    """Return the directory for the active project."""
    proj = _state["project"] or "default"
    return os.path.join(OUTPUT_ROOT, proj)


def get_sections_json() -> str:
    return os.path.join(get_project_dir(), "sections.json")


def get_progress_json() -> str:
    return os.path.join(get_project_dir(), "progress.json")


def get_index_path() -> str:
    return os.path.join(get_project_dir(), "index.html")


def audio_path(section_id: str) -> str:
    return os.path.join(get_project_dir(), f"{section_id}.mp3")


def html_path(section_id: str) -> str:
    return os.path.join(get_project_dir(), f"{section_id}.html")


def list_projects() -> list[str]:
    """List existing project folders under the output root."""
    if not os.path.isdir(OUTPUT_ROOT):
        return []
    return sorted(
        d for d in os.listdir(OUTPUT_ROOT)
        if os.path.isdir(os.path.join(OUTPUT_ROOT, d))
    )
