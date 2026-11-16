"""Unified transcription engine with multi-provider failover and disk caching."""

import logging
from pathlib import Path
from typing import Optional
from clipora.core.errors import TranscriptionError
from clipora.storage.config_store import get_config_store
from clipora.pipeline.hardware import pick_whisper_model
from clipora.pipeline.transcription.diarization import NormalizedTranscript, TranscriptWord
from clipora.pipeline.transcription.transcribe_cache import (
    get_cached_transcript,
    save_cached_transcript,
)
from clipora.pipeline.transcription.deepgram_transcribe import transcribe_deepgram
from clipora.pipeline.transcription.elevenlabs_transcribe import transcribe_elevenlabs

logger = logging.getLogger("clipora.transcription")

def transcribe_local_whisper(audio_path: Path | str) -> NormalizedTranscript:
    """Run local faster-whisper using hardware-adaptive model settings."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise TranscriptionError(
            "Local Faster-Whisper fallback requires 'faster-whisper' package installed: " + str(e)
        ) from e

    model_size, device, compute_type = pick_whisper_model()
    logger.info(f"Loading local Whisper model: {model_size} ({device}, {compute_type})")

    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(str(audio_path), word_timestamps=True)

    words: list[TranscriptWord] = []
    full_text_parts = []

    for segment in segments:
        full_text_parts.append(segment.text)
        if segment.words:
            for w in segment.words:
                words.append(
                    TranscriptWord(
                        word=w.word.strip(),
                        start=float(w.start),
                        end=float(w.end),
                        speaker="SPEAKER_00",
                        confidence=float(w.probability),
                        punctuated_word=w.word.strip(),
                    )
                )

    return NormalizedTranscript(
        text=" ".join(full_text_parts).strip(),
        words=words,
        language=info.language,
    )

def transcribe_audio(
    audio_path: Path | str,
    source_identifier: str,
    preferred_provider: Optional[str] = None,
) -> NormalizedTranscript:
    """Transcribe audio with disk caching and automatic multi-provider fallback.
    
    Order: Cache -> Preferred Provider -> Secondary Provider -> Local Whisper.
    """
    # 1. Check disk cache
    cached = get_cached_transcript(source_identifier)
    if cached:
        logger.info(f"Using cached transcript for {source_identifier}")
        return NormalizedTranscript.from_dict(cached)

    cfg = get_config_store().get_config()
    provider = (preferred_provider or cfg.transcription_provider).lower()

    transcript: Optional[NormalizedTranscript] = None

    # 2. Try Deepgram if selected or primary
    if provider == "deepgram" and cfg.deepgram_api_key:
        try:
            transcript = transcribe_deepgram(audio_path, cfg.deepgram_api_key)
        except Exception as e:
            logger.warning(f"Deepgram transcription failed, falling back: {e}")

    # 3. Try ElevenLabs if selected or fallback
    if transcript is None and (provider == "elevenlabs" or cfg.elevenlabs_api_key):
        if cfg.elevenlabs_api_key:
            try:
                transcript = transcribe_elevenlabs(audio_path, cfg.elevenlabs_api_key)
            except Exception as e:
                logger.warning(f"ElevenLabs transcription failed, falling back: {e}")

    # 4. Fallback to Local Whisper
    if transcript is None:
        try:
            transcript = transcribe_local_whisper(audio_path)
        except Exception as e:
            if transcript is None:
                raise TranscriptionError(
                    f"All transcription providers failed. Last error: {e}"
                ) from e

    # 5. Save to disk cache
    save_cached_transcript(source_identifier, transcript.to_dict())
    return transcript
