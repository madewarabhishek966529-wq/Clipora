"""Natural language instruction parser translating edit prompts into time drop ranges."""

import re
from typing import List, Tuple

def parse_natural_language_edit_instructions(
    instruction: str,
    clip_duration: float,
) -> List[Tuple[float, float]]:
    """Parse text prompt into (start_sec, end_sec) drop intervals.
    
    Examples:
        - "cut the first 5 seconds" -> [(0.0, 5.0)]
        - "remove the last 3.5 seconds" -> [(clip_duration - 3.5, clip_duration)]
        - "cut from 10 to 15" -> [(10.0, 15.0)]
    """
    clean = instruction.lower().strip()
    drop_ranges: List[Tuple[float, float]] = []

    # Match "cut/trim/remove first X seconds"
    m_first = re.search(r"(?:cut|trim|remove|drop)\s+(?:the\s+)?first\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?", clean)
    if m_first:
        sec = float(m_first.group(1))
        drop_ranges.append((0.0, min(sec, clip_duration)))

    # Match "cut/trim/remove last X seconds"
    m_last = re.search(r"(?:cut|trim|remove|drop)\s+(?:the\s+)?last\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?", clean)
    if m_last:
        sec = float(m_last.group(1))
        drop_ranges.append((max(0.0, clip_duration - sec), clip_duration))

    # Match "cut/remove between A and B" or "from A to B"
    m_range = re.search(r"(?:between|from)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?\s*(?:and|to|-)\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?", clean)
    if m_range:
        a = float(m_range.group(1))
        b = float(m_range.group(2))
        s, e = min(a, b), max(a, b)
        drop_ranges.append((s, min(e, clip_duration)))

    return drop_ranges
