"""Core data schemas for viral clips, job metadata, and responses."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

class JobStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    REFRAMING = "reframing"
    POSTPROCESSING = "postprocessing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class ViralClip(BaseModel):
    start: float = Field(..., ge=0, description="Clip start timestamp in seconds")
    end: float = Field(..., gt=0, description="Clip end timestamp in seconds")
    viral_score: int = Field(..., ge=1, le=100, description="Virality score between 1 and 100")
    viral_reason: str = Field(..., min_length=20, description="Explanation of hook, payoff, or quote")
    viral_hook_text: str = Field(..., min_length=3, max_length=160, description="Scroll-stopping hook text overlay")
    video_title_for_youtube_short: str = Field("", max_length=110)
    video_description_for_tiktok: str = Field("", max_length=2200)
    video_description_for_instagram: str = Field("", max_length=2200)

    # Optional enriched fields generated during pipeline & editing
    original_index: Optional[int] = Field(None, description="Index in candidate list")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    clip_filename: Optional[str] = Field(None, description="Relative or absolute path to rendered mp4")
    thumbnail_filename: Optional[str] = Field(None, description="Relative or absolute path to thumbnail jpg")
    reframe_mode: Optional[str] = Field(None, description="Reframe mode applied")
    subtitle_preset: Optional[str] = Field("hormozi_bold", description="ASS karaoke style preset")
    grade_preset: Optional[str] = Field("warm_cinematic", description="Color grade preset")
    smart_cut_applied: Optional[bool] = Field(False, description="Whether silence removal was applied")
    logo_enabled: Optional[bool] = Field(False, description="Whether logo watermark is displayed")
    banner_enabled: Optional[bool] = Field(False, description="Whether creator attribution banner is displayed")

    @field_validator("start", "end", mode="before")
    @classmethod
    def normalize_timestamp(cls, v: Any) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            v = v.strip()
            if ":" in v:
                parts = v.split(":")
                if len(parts) == 2:
                    return float(parts[0]) * 60 + float(parts[1])
                if len(parts) == 3:
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            if v.count(".") > 1:
                parts = v.split(".")
                if len(parts) == 3:
                    return float(parts[0]) * 60 + float(parts[1]) + float(f"0.{parts[2]}")
                if len(parts) == 4:
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2]) + float(f"0.{parts[3]}")
            return float(v)
        raise ValueError(f"Cannot convert {v!r} to float timestamp")

class ViralClipsResponse(BaseModel):
    clips: List[ViralClip]

class JobMetadata(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    source_url: Optional[str] = None
    input_file: Optional[str] = None
    video_title: Optional[str] = None
    video_duration: Optional[float] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    progress_percent: float = 0.0
    current_phase: str = "queued"
    clips: List[ViralClip] = Field(default_factory=list)
    reframe_mode: str = "auto"
    custom_instructions: Optional[str] = None
    transcription_provider: str = "deepgram"
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
