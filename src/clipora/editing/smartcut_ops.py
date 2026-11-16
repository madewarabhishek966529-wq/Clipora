"""Pure mathematical functions for silence detection and filler word drops."""

from typing import List, Tuple
from clipora.pipeline.transcription.diarization import TranscriptWord

FILLER_WORDS = {
    "um", "uh", "umm", "uhh", "er", "ah", "like", "cioè", "tipo", "ehm", "you know"
}

def detect_silence_gaps_from_words(
    words: List[TranscriptWord],
    min_silence_gap: float = 0.8,
    cushion_sec: float = 0.15,
) -> List[Tuple[float, float]]:
    """Detect dead-air intervals between consecutive words exceeding min_silence_gap."""
    gaps: List[Tuple[float, float]] = []
    if len(words) < 2:
        return gaps

    for i in range(len(words) - 1):
        gap_start = words[i].end
        gap_end = words[i + 1].start
        dur = gap_end - gap_start

        if dur >= min_silence_gap:
            # Leave cushion on both sides so cuts sound natural
            cut_start = gap_start + cushion_sec
            cut_end = gap_end - cushion_sec
            if cut_end > cut_start:
                gaps.append((round(cut_start, 3), round(cut_end, 3)))

    return gaps

def find_filler_word_ranges(
    words: List[TranscriptWord],
    pad_sec: float = 0.05,
) -> List[Tuple[float, float]]:
    """Identify time intervals occupied by filler words."""
    ranges: List[Tuple[float, float]] = []
    for w in words:
        clean = w.word.strip().lower().rstrip(".,!?")
        if clean in FILLER_WORDS:
            s = max(0.0, w.start - pad_sec)
            e = w.end + pad_sec
            ranges.append((round(s, 3), round(e, 3)))
    return ranges

def invert_cut_ranges_to_keep_ranges(
    cut_ranges: List[Tuple[float, float]],
    total_duration: float,
) -> List[Tuple[float, float]]:
    """Convert intervals to cut into contiguous intervals to keep."""
    if not cut_ranges:
        return [(0.0, total_duration)]

    # Sort and merge overlapping cut ranges
    sorted_cuts = sorted(cut_ranges, key=lambda x: x[0])
    merged_cuts: List[Tuple[float, float]] = []
    for start, end in sorted_cuts:
        if not merged_cuts:
            merged_cuts.append((start, end))
        else:
            prev_s, prev_e = merged_cuts[-1]
            if start <= prev_e:
                merged_cuts[-1] = (prev_s, max(prev_e, end))
            else:
                merged_cuts.append((start, end))

    keep_ranges: List[Tuple[float, float]] = []
    curr = 0.0
    for c_start, c_end in merged_cuts:
        if c_start > curr:
            keep_ranges.append((round(curr, 3), round(c_start, 3)))
        curr = max(curr, c_end)

    if curr < total_duration:
        keep_ranges.append((round(curr, 3), round(total_duration, 3)))

    return keep_ranges
