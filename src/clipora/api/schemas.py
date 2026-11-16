"""API request and response schemas (Pydantic v2)."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CreateJobRequest(BaseModel):
    source_url: Optional[str] = None
    input_file: Optional[str] = None
    reframe_mode: str = "auto"
    custom_instructions: Optional[str] = None
    transcription_provider: Optional[str] = None

class BatchCreateJobRequest(BaseModel):
    urls: List[str]
    reframe_mode: str = "auto"
    custom_instructions: Optional[str] = None
    transcription_provider: Optional[str] = None

class ConfigPatchRequest(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    allowed_origins: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = None
    max_concurrent_jobs: Optional[int] = None
    gemini_api_key: Optional[str] = None
    deepgram_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    transcription_provider: Optional[str] = None
    audio_isolation: Optional[bool] = None
    reframe_mode: Optional[str] = None
    reframe_static_auto: Optional[int] = None
    zernio_api_key: Optional[str] = None
    zernio_base_url: Optional[str] = None
    zernio_min_gap_seconds: Optional[int] = None
    twitch_client_id: Optional[str] = None
    twitch_client_secret: Optional[str] = None
    watermark_position: Optional[str] = None
    watermark_opacity: Optional[float] = None
    watermark_scale: Optional[str] = None
    attribution_banner_enabled: Optional[bool] = None
    default_subtitle_preset: Optional[str] = None
    default_grade_preset: Optional[str] = None

class PublishClipRequest(BaseModel):
    platforms: List[str] = Field(default_factory=lambda: ["tiktok", "instagram", "youtube_shorts"])
    schedule_mode: str = "now"  # "now" | "auto" | "manual"
    manual_scheduled_for: Optional[str] = None
    caption: Optional[str] = None

class SmartCutRequest(BaseModel):
    min_silence_gap: float = 0.8

class ReframeClipRequest(BaseModel):
    reframe_mode: str = "auto"

class EditAIRequest(BaseModel):
    instruction: str

class AddMonitorRequest(BaseModel):
    platform: str
    channel_id: str
    enabled: bool = True
    prelive_skip_minutes: int = 30
    segment_slice_minutes: int = 30
    min_viral_score: int = 70
    auto_publish: bool = False
