import re
from config import MAX_WORDS_PER_SECTION, MIN_WORDS_PER_SECTION


def split_script_into_chunks(raw_script: str) -> list:
    """
    Pre-splits the markdown script into manageable chunks BEFORE sending to LLM.
    Splits by SECTION headers first, then by paragraphs if too long.
    """
    # Split by main section markers
    section_pattern = r'(?=###\s*🎬\s*SECTION\s+\d+)'
    raw_sections = re.split(section_pattern, raw_script)
    raw_sections = [s.strip() for s in raw_sections if s.strip() and "SECTION" in s]

    chunks = []
    for sec in raw_sections:
        # Extract heading
        heading_match = re.search(r'###\s*🎬\s*SECTION\s+\d+:\s*(.+)', sec)
        heading = heading_match.group(1).strip() if heading_match else "Untitled"
        heading = re.sub(r'\(.*?\)', '', heading).strip()

        # Split sub-chunks by paragraph blocks
        paragraphs = re.split(r'\n\s*\n', sec)
        current_chunk = []
        current_word_count = 0
        sub_idx = 1

        for para in paragraphs:
            words = len(para.split())
            if current_word_count + words > MAX_WORDS_PER_SECTION and current_word_count >= MIN_WORDS_PER_SECTION:
                chunks.append({
                    "heading": heading,
                    "sub_index": sub_idx,
                    "content": "\n\n".join(current_chunk)
                })
                sub_idx += 1
                current_chunk = [para]
                current_word_count = words
            else:
                current_chunk.append(para)
                current_word_count += words

        if current_chunk:
            chunks.append({
                "heading": heading,
                "sub_index": sub_idx,
                "content": "\n\n".join(current_chunk)
            })

    return chunks