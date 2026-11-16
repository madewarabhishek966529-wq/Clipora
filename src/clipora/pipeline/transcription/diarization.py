"""Normalized transcript models and diarization normalization."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TranscriptWord(BaseModel):
    word: str
    start: float
    end: float
    speaker: Optional[str] = "SPEAKER_00"
    confidence: Optional[float] = 1.0
    punctuated_word: Optional[str] = None

class NormalizedTranscript(BaseModel):
    text: str
    words: List[TranscriptWord]
    language: str = "en"
    audio_tags: List[Dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedTranscript":
        return cls.model_validate(data)
