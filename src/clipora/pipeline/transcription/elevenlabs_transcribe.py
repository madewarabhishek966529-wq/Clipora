"""ElevenLabs Scribe API client with audio event tagging."""

from pathlib import Path
from typing import Optional
import httpx
from clipora.core.errors import TranscriptionError
from clipora.pipeline.transcription.diarization import NormalizedTranscript, TranscriptWord

ELEVENLABS_SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"

def transcribe_elevenlabs(
    audio_path: Path | str,
    api_key: str,
    model_id: str = "scribe_v1",
) -> NormalizedTranscript:
    """Transcribe audio file via ElevenLabs Scribe REST API."""
    path = Path(audio_path).resolve()
    if not path.is_file():
        raise TranscriptionError(f"Audio file does not exist: {audio_path}")

    if not api_key:
        raise TranscriptionError("ElevenLabs API key is missing.")

    headers = {
        "xi-api-key": api_key,
    }

    try:
        with open(path, "rb") as f:
            files = {"file": (path.name, f, "audio/flac")}
            data = {"model_id": model_id, "tag_audio_events": "true"}
            response = httpx.post(
                ELEVENLABS_SCRIBE_URL,
                headers=headers,
                data=data,
                files=files,
                timeout=300.0,
            )

        if response.status_code != 200:
            raise TranscriptionError(
                f"ElevenLabs Scribe API error ({response.status_code}): {response.text}",
                details={"status_code": response.status_code, "body": response.text},
            )

        res_json = response.json()
        raw_words = res_json.get("words", [])
        transcript_text = res_json.get("text", "")
        audio_events = res_json.get("audio_events", [])

        words: list[TranscriptWord] = []
        for w in raw_words:
            words.append(
                TranscriptWord(
                    word=w.get("text", "").strip(),
                    start=float(w.get("start", 0.0)),
                    end=float(w.get("end", 0.0)),
                    speaker=w.get("speaker_id", "SPEAKER_00"),
                    confidence=float(w.get("confidence", 1.0)),
                    punctuated_word=w.get("text", "").strip(),
                )
            )

        return NormalizedTranscript(
            text=transcript_text,
            words=words,
            language=res_json.get("language_code", "en"),
            audio_tags=audio_events,
        )

    except httpx.RequestError as e:
        raise TranscriptionError(f"ElevenLabs network request failed: {e}") from e
