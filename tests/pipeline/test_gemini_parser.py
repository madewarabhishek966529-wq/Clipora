"""Unit tests for the 5-level Gemini JSON parser and repair chain."""

import pytest
from clipora.pipeline.analysis.gemini_parser import parse_viral_clips_response
from clipora.pipeline.transcription.diarization import NormalizedTranscript, TranscriptWord

def test_level1_strict_parse():
    raw = """Some chain of thought here...
### JSON ###
{
  "clips": [
    {
      "start": 10.0,
      "end": 35.0,
      "viral_score": 90,
      "viral_reason": "Strong pattern interrupt with unexpected punchline.",
      "viral_hook_text": "You won't believe what he said",
      "video_title_for_youtube_short": "Shocking reveal",
      "video_description_for_tiktok": "Wait for the end",
      "video_description_for_instagram": "Unreal"
    }
  ]
}"""
    clips = parse_viral_clips_response(raw)
    assert len(clips) == 1
    assert clips[0].viral_score == 90
    assert clips[0].start == 10.0

def test_level2_deterministic_cleanup_markdown_and_trailing_commas():
    raw = """### JSON ###
```json
{
  "clips": [
    {
      "start": 5.5,
      "end": 25.0,
      "viral_score": 85,
      "viral_reason": "High emotional payoff and funny reaction beat.",
      "viral_hook_text": "Did he actually just say that",
      "video_title_for_youtube_short": "He went too far",
      "video_description_for_tiktok": "Wild moment",
      "video_description_for_instagram": "Check this",
    },
  ],
}
```"""
    clips = parse_viral_clips_response(raw)
    assert len(clips) == 1
    assert clips[0].viral_score == 85

def test_level3_json_repair_broken_json():
    # Missing quotes and incomplete closing
    raw = """### JSON ###
{
  clips: [
    {
      start: 12.0,
      end: 42.0,
      viral_score: 88,
      viral_reason: "A very clear explanation of how this worked out in the end.",
      viral_hook_text: "The secret trick revealed"
    }
  ]
"""
    clips = parse_viral_clips_response(raw)
    assert len(clips) == 1
    assert clips[0].start == 12.0
    assert clips[0].viral_score == 88

def test_level5_texttiling_fallback_when_corrupted():
    raw = "Totally unparseable garbage text without any JSON structure at all."
    words = [
        TranscriptWord(word=f"word_{i}.", start=float(i * 2), end=float(i * 2 + 1.5))
        for i in range(25)
    ]
    transcript = NormalizedTranscript(text="dummy transcript", words=words)

    clips = parse_viral_clips_response(raw, transcript=transcript)
    assert len(clips) >= 1
    assert clips[0].viral_score == 72
