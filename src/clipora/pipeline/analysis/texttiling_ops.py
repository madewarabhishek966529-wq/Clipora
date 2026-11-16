"""TextTiling-inspired topic segmentation fallback when LLM parsing is unavailable."""

import re
from typing import List
from clipora.core.clip_schema import ViralClip
from clipora.pipeline.transcription.diarization import NormalizedTranscript

SENTENCE_ENDINGS = {".", "!", "?"}

def fallback_topic_segmentation(
    transcript: NormalizedTranscript,
    min_clip_duration: float = 20.0,
    target_clip_duration: float = 40.0,
    max_clip_duration: float = 58.0,
) -> List[ViralClip]:
    """Segment transcript into sensible candidate clips based on sentence cadence."""
    words = transcript.words
    if not words:
        return []

    clips: List[ViralClip] = []
    current_start_idx = 0
    total_words = len(words)

    while current_start_idx < total_words:
        start_word = words[current_start_idx]
        start_time = start_word.start

        # Look ahead for a sentence boundary that gives 20s - 58s duration
        best_end_idx = None
        for i in range(current_start_idx, total_words):
            dur = words[i].end - start_time
            has_punct = any(words[i].word.endswith(p) for p in SENTENCE_ENDINGS)

            if dur >= min_clip_duration and has_punct:
                best_end_idx = i
                if dur >= target_clip_duration:
                    break

            if dur > max_clip_duration:
                # Exceeded max duration, use current best or clamp here
                if best_end_idx is None:
                    best_end_idx = i
                break

        if best_end_idx is None:
            # Reached end of transcript
            best_end_idx = total_words - 1

        end_time = words[best_end_idx].end
        dur = end_time - start_time

        if dur >= min_clip_duration:
            clip_words = words[current_start_idx : best_end_idx + 1]
            clip_text = " ".join(w.word for w in clip_words)
            first_few = " ".join(w.word for w in clip_words[:6])

            clips.append(
                ViralClip(
                    start=round(start_time, 3),
                    end=round(end_time, 3),
                    viral_score=72,
                    viral_reason="Topic segment identified via lexical cadence and natural sentence pauses.",
                    viral_hook_text=first_few[:50] or "Watch this moment",
                    video_title_for_youtube_short=(first_few[:90] + "...") if len(first_few) > 30 else "Highlights you cannot miss",
                    video_description_for_tiktok=clip_text[:200],
                    video_description_for_instagram=clip_text[:200],
                )
            )

        # Advance to next segment with a small step or from end_idx
        current_start_idx = best_end_idx + 1

    return clips
