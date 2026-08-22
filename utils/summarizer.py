"""
Summary / Key Points / Main Ideas / Improvement Suggestions generation.

Summaries are content-proportional (the LLM is instructed to scale length to the
source, not a fixed word count) and large documents are handled with a
map-reduce strategy so we never exceed the LLM's context window.
"""

import os
from typing import List

from config import LARGE_DOC_CHAR_THRESHOLD, MAP_CHUNK_CHAR_SIZE
from utils.groq_client import generate

_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")


def _load_prompt(filename: str) -> str:
    with open(os.path.join(_PROMPTS_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


SUMMARY_PROMPT = _load_prompt("summary_prompt.txt")
KEY_POINTS_PROMPT = _load_prompt("key_points_prompt.txt")
MAIN_IDEAS_PROMPT = _load_prompt("main_ideas_prompt.txt")
IMPROVEMENT_PROMPT = _load_prompt("improvement_prompt.txt")


def _split_for_map_reduce(text: str, chunk_size: int = MAP_CHUNK_CHAR_SIZE) -> List[str]:
    """Simple character-based split on paragraph boundaries for map-reduce summarization."""
    paragraphs = text.split("\n\n")
    sections: List[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current += (("\n\n" if current else "") + para)
        else:
            if current:
                sections.append(current)
            current = para
    if current:
        sections.append(current)
    return sections or [text]


def generate_summary(full_text: str, detail_level: str = "Medium") -> str:
    """
    Content-proportional summary. Uses direct summarization for normal-sized
    documents, and hierarchical map-reduce for large ones so the LLM's context
    window is never exceeded.
    """
    if not full_text.strip():
        return ""

    if len(full_text) <= LARGE_DOC_CHAR_THRESHOLD:
        prompt = SUMMARY_PROMPT.format(detail_level=detail_level, content=full_text)
        return generate(prompt, temperature=0.3)

    # --- Map step: summarize each section independently at "Medium" detail ---
    sections = _split_for_map_reduce(full_text)
    intermediate_summaries = []
    for section in sections:
        section_prompt = SUMMARY_PROMPT.format(detail_level="Medium", content=section)
        intermediate_summaries.append(generate(section_prompt, temperature=0.3))

    combined = "\n\n".join(
        f"Section {i + 1} summary:\n{s}" for i, s in enumerate(intermediate_summaries)
    )

    # --- Reduce step: synthesize the intermediate summaries into one final summary ---
    final_prompt = SUMMARY_PROMPT.format(detail_level=detail_level, content=combined)
    return generate(final_prompt, temperature=0.3)


def generate_key_points(full_text: str) -> str:
    if not full_text.strip():
        return ""
    source = full_text if len(full_text) <= LARGE_DOC_CHAR_THRESHOLD else full_text[:LARGE_DOC_CHAR_THRESHOLD]
    prompt = KEY_POINTS_PROMPT.format(content=source)
    return generate(prompt, temperature=0.2)


def generate_main_ideas(full_text: str) -> str:
    if not full_text.strip():
        return ""
    source = full_text if len(full_text) <= LARGE_DOC_CHAR_THRESHOLD else full_text[:LARGE_DOC_CHAR_THRESHOLD]
    prompt = MAIN_IDEAS_PROMPT.format(content=source)
    return generate(prompt, temperature=0.2)


def generate_improvement_suggestions(full_text: str) -> str:
    if not full_text.strip():
        return ""
    source = full_text if len(full_text) <= LARGE_DOC_CHAR_THRESHOLD else full_text[:LARGE_DOC_CHAR_THRESHOLD]
    prompt = IMPROVEMENT_PROMPT.format(content=source)
    return generate(prompt, temperature=0.4)
