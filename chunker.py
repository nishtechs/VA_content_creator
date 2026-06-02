"""
Chunker module — splits markdown scripts into manageable chunks.
Uses content hashing to detect changes and skip re-processing.
Extracts ONLY spoken narration (> quoted lines) for audio.
"""

import re
import hashlib
import logging
from typing import Any

from config import MAX_WORDS_PER_SECTION, MIN_WORDS_PER_SECTION

logger = logging.getLogger("va_creator.chunker")


def hash_chunk(chunk: dict[str, Any]) -> str:
    """Generate a stable hash for a chunk to detect changes."""
    content = f"{chunk['heading']}:{chunk['sub_index']}:{chunk['content']}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def extract_code_blocks(content: str) -> list[dict[str, str]]:
    """
    Extract fenced code blocks (``` ... ```) from markdown content.
    Returns a list of {"language": str, "code": str} dicts.
    """
    blocks: list[dict[str, str]] = []
    # Match ```lang\n ... ``` (lang optional)
    pattern = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)
    for match in pattern.finditer(content):
        lang = match.group(1).strip() or "text"
        code = match.group(2).strip()
        if code:
            blocks.append({"language": lang, "code": code})
    return blocks


def extract_spoken_text(content: str) -> str:
    """
    Extract ONLY the spoken narration from markdown content.
    Spoken lines are those inside > "..." (blockquote with quotes).
    Strips timestamps, [Screen:] tags, code blocks, and other non-spoken content.
    """
    # Find all blockquote lines (lines starting with >)
    lines = content.split("\n")
    spoken_parts: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Match lines starting with > that contain actual narration
        if stripped.startswith(">"):
            # Remove the > prefix
            text = stripped[1:].strip()
            # Remove surrounding quotes if present
            text = re.sub(r'^["\u201c]|["\u201d]$', '', text.strip())
            # Skip empty lines
            if text and text != '---':
                spoken_parts.append(text)

    result = " ".join(spoken_parts)

    # Clean up any remaining markdown artifacts
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)  # Remove bold **text**
    result = re.sub(r'`([^`]+)`', r'\1', result)  # Remove inline code `text`
    result = re.sub(r'\[([^\]]+)\]', '', result)  # Remove [Screen:...] tags
    result = re.sub(r'\(.*?\)', '', result)  # Remove (timestamps)
    result = re.sub(r'\s+', ' ', result).strip()  # Normalize whitespace

    return result


def split_script_into_chunks(raw_script: str) -> list[dict[str, Any]]:
    """
    Pre-splits the markdown script into manageable chunks BEFORE sending to LLM.
    Splits by SECTION headers first, then by paragraphs if too long.
    Each chunk includes a content hash and pre-extracted spoken text.
    """
    # Split by main section markers
    section_pattern = r'(?=###\s*🎬\s*SECTION\s+\d+)'
    raw_sections = re.split(section_pattern, raw_script)
    raw_sections = [s.strip() for s in raw_sections if s.strip() and "SECTION" in s]

    if not raw_sections:
        logger.warning("No SECTION markers found. Treating entire script as one chunk.")
        spoken = extract_spoken_text(raw_script)
        code_blocks = extract_code_blocks(raw_script)
        return [{
            "heading": "Full Script",
            "sub_index": 1,
            "content": raw_script.strip(),
            "spoken_text": spoken,
            "code_blocks": code_blocks,
            "has_code": bool(code_blocks),
            "hash": hashlib.sha256(raw_script.encode()).hexdigest()[:16]
        }]

    chunks: list[dict[str, Any]] = []
    for sec in raw_sections:
        # Extract heading
        heading_match = re.search(r'###\s*🎬\s*SECTION\s+\d+:\s*(.+)', sec)
        heading = heading_match.group(1).strip() if heading_match else "Untitled"
        heading = re.sub(r'\(.*?\)', '', heading).strip()

        # Extract spoken text for this entire section
        section_spoken = extract_spoken_text(sec)

        # Split sub-chunks by paragraph blocks
        paragraphs = re.split(r'\n\s*\n', sec)
        current_chunk: list[str] = []
        current_word_count = 0
        sub_idx = 1

        for para in paragraphs:
            words = len(para.split())
            if current_word_count + words > MAX_WORDS_PER_SECTION and current_word_count >= MIN_WORDS_PER_SECTION:
                chunk_content = "\n\n".join(current_chunk)
                chunk_spoken = extract_spoken_text(chunk_content)
                code_blocks = extract_code_blocks(chunk_content)
                chunk_data = {
                    "heading": heading,
                    "sub_index": sub_idx,
                    "content": chunk_content,
                    "spoken_text": chunk_spoken,
                    "code_blocks": code_blocks,
                    "has_code": bool(code_blocks),
                }
                chunk_data["hash"] = hash_chunk(chunk_data)
                chunks.append(chunk_data)
                sub_idx += 1
                current_chunk = [para]
                current_word_count = words
            else:
                current_chunk.append(para)
                current_word_count += words

        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunk_spoken = extract_spoken_text(chunk_content)
            code_blocks = extract_code_blocks(chunk_content)
            chunk_data = {
                "heading": heading,
                "sub_index": sub_idx,
                "content": chunk_content,
                "spoken_text": chunk_spoken,
                "code_blocks": code_blocks,
                "has_code": bool(code_blocks),
            }
            chunk_data["hash"] = hash_chunk(chunk_data)
            chunks.append(chunk_data)

    # Filter out chunks with no spoken text (they're just code/notes)
    # But keep them if they have content for visual slides
    for chunk in chunks:
        if not chunk["spoken_text"]:
            logger.warning(f"Chunk '{chunk['heading']}' sub {chunk['sub_index']} has no spoken text")

    logger.info(f"Split script into {len(chunks)} chunks")
    return chunks
