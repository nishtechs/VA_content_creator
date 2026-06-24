"""
Feedback and Learning Engine for VA Creator.
Tracks user corrections and constructs few-shot prompts to guide agent improvement.
"""

import os
import json
from typing import Dict, List, Optional
from config import logger

FEEDBACK_FILE_NAME = "feedback.json"

def _get_feedback_filepath(proj_dir: str) -> str:
    """Get absolute path to feedback.json in project output directory."""
    return os.path.join(proj_dir, FEEDBACK_FILE_NAME)

def load_feedback(proj_dir: str) -> List[Dict]:
    """Load logged feedback items for a project."""
    filepath = _get_feedback_filepath(proj_dir)
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading feedback: {e}")
        return []

def save_feedback(proj_dir: str, feedback_list: List[Dict]) -> None:
    """Save feedback items for a project."""
    filepath = _get_feedback_filepath(proj_dir)
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(feedback_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")

def log_feedback(proj_dir: str, section_id: str, original: Dict, corrected: Dict) -> bool:
    """Compares original vs. corrected section data. Logs differences if any."""
    if not proj_dir:
        return False

    diffs = {}
    
    # Check for changes in key visual and narrative fields
    for field in ("slide_html", "custom_css", "audio_text", "title", "visual", "visual_brief"):
        orig_val = original.get(field, "").strip() if original.get(field) else ""
        corr_val = corrected.get(field, "").strip() if corrected.get(field) else ""
        if orig_val != corr_val:
            diffs[field] = {
                "before": orig_val,
                "after": corr_val
            }
            
    if not diffs:
        # No changes made
        return False

    feedback_entry = {
        "section_id": section_id,
        "category": corrected.get("category", "concept"),
        "title": corrected.get("title", ""),
        "differences": diffs,
        "timestamp": os.path.getmtime(proj_dir) if os.path.exists(proj_dir) else 0.0 # simple fallback timestamp
    }
    
    feedback_list = load_feedback(proj_dir)
    
    # Avoid duplicate entries for same section if already logged
    # We update or append
    updated = False
    for i, entry in enumerate(feedback_list):
        if entry.get("section_id") == section_id:
            feedback_list[i] = feedback_entry
            updated = True
            break
            
    if not updated:
        feedback_list.append(feedback_entry)
        
    save_feedback(proj_dir, feedback_list)
    logger.info(f"Logged feedback for {section_id} in {proj_dir}")
    return True

def get_feedback_examples(proj_dir: str, category: str, limit: int = 2) -> str:
    """Constructs prompt-friendly few-shot exemplars from past corrections of the same category."""
    feedback_list = load_feedback(proj_dir)
    
    # Filter by category
    relevant = [f for f in feedback_list if f.get("category") == category]
    
    # If not enough category-specific feedback, add general ones
    if len(relevant) < limit:
        general = [f for f in feedback_list if f.get("category") != category]
        relevant.extend(general[:limit - len(relevant)])
        
    relevant = relevant[:limit]
    if not relevant:
        return ""
        
    prompt_blocks = []
    for idx, entry in enumerate(relevant):
        title = entry.get("title", "Slide")
        block = f"--- EXAMPLE CORRECTION #{idx+1} ({title}) ---\n"
        
        diffs = entry.get("differences", {})
        
        # Audio text correction description
        if "audio_text" in diffs:
            block += (
                f"Narrative Spoken Script Correction:\n"
                f"  [AVOID]: {diffs['audio_text']['before']}\n"
                f"  [PREFER]: {diffs['audio_text']['after']}\n\n"
            )
            
        # HTML/CSS correction description
        if "slide_html" in diffs or "custom_css" in diffs:
            orig_html = diffs.get("slide_html", {}).get("before", "") or entry.get("differences", {}).get("slide_html", {}).get("before", "")
            corr_html = diffs.get("slide_html", {}).get("after", "") or entry.get("differences", {}).get("slide_html", {}).get("after", "")
            
            orig_css = diffs.get("custom_css", {}).get("before", "")
            corr_css = diffs.get("custom_css", {}).get("after", "")
            
            block += "Slide Layout / Style Correction:\n"
            if orig_html:
                block += f"  [AVOID HTML Layout]:\n```html\n{orig_html}\n```\n"
            if orig_css:
                block += f"  [AVOID Custom CSS]:\n```css\n{orig_css}\n```\n"
            if corr_html:
                block += f"  [PREFER HTML Layout]:\n```html\n{corr_html}\n```\n"
            if corr_css:
                block += f"  [PREFER Custom CSS]:\n```css\n{corr_css}\n```\n"
                
        prompt_blocks.append(block)
        
    return "\n".join(prompt_blocks)
