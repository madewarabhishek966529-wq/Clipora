"""Deepgram Nova-3 API client with multilingual code-switching and diarization."""

from pathlib import Path
from typing import Optional
import httpx
from clipora.core.errors import TranscriptionError
from clipora.pipeline.transcription.diarization import NormalizedTranscript, TranscriptWord

DEEPGRAM_LISTEN_URL = "https://api.deepgram.com/v1/listen"

def transcribe_deepgram(
    audio_path: Path | str,
    api_key: str,
    model: str = "nova-3",
    language: str = "multi",
) -> NormalizedTranscript:
    """Transcribe audio file via Deepgram Nova-3 REST API."""
    path = Path(audio_path).resolve()
    if not path.is_file():
        raise TranscriptionError(f"Audio file does not exist: {audio_path}")

    if not api_key:
        raise TranscriptionError("Deepgram API key is missing.")

    params = {
        "model": model,
        "smart_format": "true",
        "diarize": "true",
        "language": language,
        "punctuate": "true",
    }
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "audio/flac",
    }

    try:
        with open(path, "rb") as audio_file:
            response = httpx.post(
                DEEPGRAM_LISTEN_URL,
                params=params,
                headers=headers,
                content=audio_file.read(),
                timeout=300.0,
            )

        if response.status_code != 200:
            raise TranscriptionError(
                f"Deepgram API error ({response.status_code}): {response.text}",
                details={"status_code": response.status_code, "body": response.text},
            )

        data = response.json()
        channel = data.get("results", {}).get("channels", [{}])[0]
        alt = channel.get("alternatives", [{}])[0]

        raw_words = alt.get("words", [])
        transcript_text = alt.get("transcript", "")

        words: list[TranscriptWord] = []
        for w in raw_words:
            speaker_idx = w.get("speaker")
            speaker = f"SPEAKER_{speaker_idx:02d}" if speaker_idx is not None else "SPEAKER_00"
            words.append(
                TranscriptWord(
                    word=w.get("word", ""),
                    start=float(w.get("start", 0.0)),
                    end=float(w.get("end", 0.0)),
                    speaker=speaker,
                    confidence=float(w.get("confidence", 1.0)),
                    punctuated_word=w.get("punctuated_word", w.get("word", "")),
                )
            )

        detected_language = alt.get("languages", ["en"])[0] if alt.get("languages") else "en"
        return NormalizedTranscript(
            text=transcript_text,
            words=words,
            language=detected_language,
        )

    except httpx.RequestError as e:
        raise TranscriptionError(f"Deepgram network request failed: {e}") from e
