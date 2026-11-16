"""Micro-precision cut boundary snapping: word, sentence, and silence snapping."""

import re
from typing import List, Optional, Tuple
from clipora.pipeline.transcription.diarization import TranscriptWord

# Common abbreviations that should NOT trigger a sentence cut
ABBREVIATIONS = {
    "dr.", "mr.", "mrs.", "ms.", "vs.", "e.g.", "i.e.", "dott.", "prof.", "inc.", "corp.", "etc.", "st."
}

SENTENCE_PUNCTUATION = {".", "!", "?", "…"}

def snap_clip_to_words(
    start: float,
    end: float,
    words: List[TranscriptWord],
    window_sec: float = 0.6,
    pre_pad_sec: float = 0.050,   # 50ms lead pad
    post_pad_sec: float = 0.080,  # 80ms release pad
    video_duration: Optional[float] = None,
) -> Tuple[float, float]:
    """Snap start/end timestamps to nearest real word boundaries with lead/release pads."""
    if not words:
        return start, end

    best_start = start
    min_start_diff = window_sec

    best_end = end
    min_end_diff = window_sec

    for w in words:
        # Check start proximity
        diff_s = abs(w.start - start)
        if diff_s < min_start_diff:
            min_start_diff = diff_s
            best_start = max(0.0, w.start - pre_pad_sec)

        # Check end proximity
        diff_e = abs(w.end - end)
        if diff_e < min_end_diff:
            min_end_diff = diff_e
            best_end = w.end + post_pad_sec
            if video_duration is not None:
                best_end = min(video_duration, best_end)

    return round(best_start, 3), round(best_end, 3)

def is_abbreviation(word_text: str) -> bool:
    """Return True if word is a recognized abbreviation rather than a true sentence end."""
    clean = word_text.strip().lower()
    return clean in ABBREVIATIONS

def snap_to_sentences(
    start: float,
    end: float,
    words: List[TranscriptWord],
    max_backward_start_sec: float = 2.5,  # Asymmetric: up to 2.5s back to catch thought opening
    max_forward_end_sec: float = 1.5,     # Asymmetric: up to 1.5s forward to catch thought ending
    video_duration: Optional[float] = None,
) -> Tuple[float, float]:
    """Extend cut points to respect complete sentence boundaries without false abbreviation cuts."""
    if not words:
        return start, end

    snapped_start = start
    snapped_end = end

    # 1. Start boundary: look backward for preceding sentence end to begin at opening of thought
    for w in reversed(words):
        if w.end <= start:
            if (start - w.end) <= max_backward_start_sec:
                token = w.word.strip()
                if any(token.endswith(p) for p in SENTENCE_PUNCTUATION) and not is_abbreviation(token):
                    # The word *after* this sentence end is where our thought begins
                    idx = words.index(w)
                    if idx + 1 < len(words):
                        snapped_start = max(0.0, words[idx + 1].start - 0.05)
                        break
            else:
                break

    # 2. End boundary: look forward for the first sentence end
    for w in words:
        if w.end >= end:
            if (w.end - end) <= max_forward_end_sec:
                token = w.word.strip()
                if any(token.endswith(p) for p in SENTENCE_PUNCTUATION) and not is_abbreviation(token):
                    snapped_end = w.end + 0.08
                    if video_duration is not None:
                        snapped_end = min(video_duration, snapped_end)
                    break
            else:
                break

    return round(snapped_start, 3), round(snapped_end, 3)

def snap_to_silences(
    start: float,
    end: float,
    silence_intervals: List[Tuple[float, float]],
    window_sec: float = 0.75,
) -> Tuple[float, float]:
    """Snap boundaries inside silence intervals (noise <= -30dB) if within window_sec."""
    snapped_start = start
    snapped_end = end

    for s_start, s_end in silence_intervals:
        # Check start boundary
        if abs(s_end - start) <= window_sec or (s_start <= start <= s_end):
            # Cut in the middle or end of silence interval
            mid = (s_start + s_end) / 2.0
            snapped_start = mid
            break

    for s_start, s_end in silence_intervals:
        # Check end boundary
        if abs(s_start - end) <= window_sec or (s_start <= end <= s_end):
            mid = (s_start + s_end) / 2.0
            snapped_end = mid
            break

    return round(snapped_start, 3), round(snapped_end, 3)
