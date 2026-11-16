"""Unit tests for editing, subtitles, and smartcut math."""

import pytest
from pathlib import Path
from clipora.pipeline.transcription.diarization import TranscriptWord
from clipora.editing.smartcut_ops import (
    detect_silence_gaps_from_words,
    find_filler_word_ranges,
    invert_cut_ranges_to_keep_ranges,
)
from clipora.editing.subtitles import generate_ass_subtitles, SUBTITLE_PRESETS
from clipora.editing.clip_edit_ai import parse_natural_language_edit_instructions

def test_detect_silence_gaps():
    words = [
        TranscriptWord(word="First", start=1.0, end=2.0),
        TranscriptWord(word="Second", start=3.5, end=4.5), # 1.5s gap (> 0.8s)
        TranscriptWord(word="Third", start=4.8, end=5.5),  # 0.3s gap (<= 0.8s)
    ]
    gaps = detect_silence_gaps_from_words(words, min_silence_gap=0.8, cushion_sec=0.15)
    assert len(gaps) == 1
    # Gap from 2.0 to 3.5 -> cushion leaves cut from 2.15 to 3.35
    assert gaps[0] == (2.15, 3.35)

def test_find_filler_words():
    words = [
        TranscriptWord(word="So", start=1.0, end=1.5),
        TranscriptWord(word="um", start=1.6, end=1.9),
        TranscriptWord(word="we", start=2.0, end=2.4),
        TranscriptWord(word="like", start=2.5, end=2.8),
    ]
    fillers = find_filler_word_ranges(words, pad_sec=0.05)
    assert len(fillers) == 2

def test_invert_cut_ranges():
    total_duration = 30.0
    cuts = [(5.0, 8.0), (15.0, 18.0)]
    keeps = invert_cut_ranges_to_keep_ranges(cuts, total_duration)
    assert keeps == [(0.0, 5.0), (8.0, 15.0), (18.0, 30.0)]

def test_ass_karaoke_generation(tmp_path: Path):
    words = [
        TranscriptWord(word="Never", start=0.0, end=0.4),
        TranscriptWord(word="give", start=0.4, end=0.8),
        TranscriptWord(word="up", start=0.8, end=1.2),
    ]
    ass_path = tmp_path / "test.ass"
    generate_ass_subtitles(words, ass_path, preset_name="hormozi_bold", words_per_line=3)
    assert ass_path.is_file()
    content = ass_path.read_text(encoding="utf-8")
    assert "[Script Info]" in content
    assert "Dialogue:" in content
    assert "\\k" in content

def test_natural_language_ai_parser():
    ranges1 = parse_natural_language_edit_instructions("cut the first 5 seconds", clip_duration=45.0)
    assert ranges1 == [(0.0, 5.0)]

    ranges2 = parse_natural_language_edit_instructions("trim last 3.5 sec", clip_duration=45.0)
    assert ranges2 == [(41.5, 45.0)]

    ranges3 = parse_natural_language_edit_instructions("remove from 10 to 14.5", clip_duration=45.0)
    assert ranges3 == [(10.0, 14.5)]
