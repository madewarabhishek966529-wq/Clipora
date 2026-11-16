"""Unit tests for micro-precision cut boundary snapping."""

import pytest
from clipora.pipeline.transcription.diarization import TranscriptWord
from clipora.pipeline.cut_ops import snap_clip_to_words, snap_to_sentences, is_abbreviation

def test_word_snapping_lead_and_release_pads():
    words = [
        TranscriptWord(word="Hello", start=10.000, end=10.450),
        TranscriptWord(word="everyone", start=10.480, end=11.100),
        TranscriptWord(word="today", start=11.150, end=11.600),
    ]

    # Approximate start at 10.1s -> should snap to 10.000 - 0.050 = 9.950s
    # Approximate end at 11.5s -> should snap to 11.600 + 0.080 = 11.680s
    s, e = snap_clip_to_words(10.100, 11.500, words)
    assert s == 9.950
    assert e == 11.680

def test_abbreviation_shield():
    assert is_abbreviation("Dr.")
    assert is_abbreviation("Mr.")
    assert is_abbreviation("vs.")
    assert is_abbreviation("e.g.")
    assert not is_abbreviation("Hello.")
    assert not is_abbreviation("Done!")

def test_sentence_boundary_asymmetric_budget():
    words = [
        TranscriptWord(word="Previous.", start=1.0, end=1.8),
        TranscriptWord(word="This", start=2.0, end=2.4),
        TranscriptWord(word="is", start=2.5, end=2.8),
        TranscriptWord(word="a", start=2.9, end=3.0),
        TranscriptWord(word="sentence.", start=3.1, end=3.8),
        TranscriptWord(word="Next", start=4.0, end=4.5),
    ]

    # Start inside the sentence at 2.6 -> backward budget can move start to 2.0 (after Previous.)
    # End inside sentence at 3.3 -> forward budget can move end to 3.8 + 0.08 = 3.88
    s, e = snap_to_sentences(2.6, 3.3, words)
    assert s == 1.95  # 2.0 - 0.05
    assert e == 3.88  # 3.8 + 0.08
