"""Persistent configuration store with atomic updates and redactions."""

import os
import threading
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field
from clipora.storage.atomic import atomic_write_json, read_json_safe

DEFAULT_CONFIG_PATH = Path("data/config.json")

class CliporaConfig(BaseModel):
    # Server & API Network
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:8000"]
    )
    rate_limit_per_minute: int = Field(default=60)
    max_concurrent_jobs: int = Field(default=2)

    # AI & ASR API Keys
    gemini_api_key: str = Field(default="")
    deepgram_api_key: str = Field(default="")
    elevenlabs_api_key: str = Field(default="")

    # Transcription & Model Settings
    transcription_provider: str = Field(default="deepgram")
    audio_isolation: bool = Field(default=False)

    # Reframe Settings
    reframe_mode: str = Field(default="auto")
    reframe_static_auto: int = Field(default=1)

    # Publishing Integrations
    zernio_api_key: str = Field(default="")
    zernio_base_url: str = Field(default="https://api.zernio.com")
    zernio_min_gap_seconds: int = Field(default=5400)

    # Live Monitoring
    twitch_client_id: str = Field(default="")
    twitch_client_secret: str = Field(default="")

    # Branding Defaults
    watermark_position: str = Field(default="top-right")
    watermark_opacity: float = Field(default=0.85)
    watermark_scale: str = Field(default="M")
    attribution_banner_enabled: bool = Field(default=True)
    default_subtitle_preset: str = Field(default="hormozi_bold")
    default_grade_preset: str = Field(default="warm_cinematic")

    # Extra settings
    extra: Dict[str, Any] = Field(default_factory=dict)

SECRET_KEYS = {
    "gemini_api_key",
    "deepgram_api_key",
    "elevenlabs_api_key",
    "zernio_api_key",
    "twitch_client_secret",
}

class ConfigStore:
    """Thread-safe manager for Clipora configuration."""

    def __init__(self, config_path: Path | str = DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        self._lock = threading.Lock()
        self._cached_config: CliporaConfig | None = None
        self._load_initial()

    def _load_initial(self) -> None:
        with self._lock:
            if self.config_path.is_file():
                raw = read_json_safe(self.config_path, default={})
                self._cached_config = CliporaConfig.model_validate(raw)
            else:
                # Initialize from environment variables if present
                init_dict: dict[str, Any] = {}
                if os.getenv("HOST"):
                    init_dict["host"] = os.getenv("HOST")
                if os.getenv("PORT"):
                    try:
                        init_dict["port"] = int(os.getenv("PORT", "8000"))
                    except ValueError:
                        pass
                if os.getenv("RATE_LIMIT_PER_MINUTE"):
                    try:
                        init_dict["rate_limit_per_minute"] = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
                    except ValueError:
                        pass
                if os.getenv("MAX_CONCURRENT_JOBS"):
                    try:
                        init_dict["max_concurrent_jobs"] = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
                    except ValueError:
                        pass
                if os.getenv("ALLOWED_ORIGINS"):
                    init_dict["allowed_origins"] = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
                if os.getenv("GEMINI_API_KEY"):
                    init_dict["gemini_api_key"] = os.getenv("GEMINI_API_KEY")
                if os.getenv("DEEPGRAM_API_KEY"):
                    init_dict["deepgram_api_key"] = os.getenv("DEEPGRAM_API_KEY")
                if os.getenv("ELEVENLABS_API_KEY"):
                    init_dict["elevenlabs_api_key"] = os.getenv("ELEVENLABS_API_KEY")
                if os.getenv("TRANSCRIPTION_PROVIDER"):
                    init_dict["transcription_provider"] = os.getenv("TRANSCRIPTION_PROVIDER")
                if os.getenv("AUDIO_ISOLATION"):
                    init_dict["audio_isolation"] = os.getenv("AUDIO_ISOLATION", "").lower() in ("true", "1", "yes")
                if os.getenv("REFRAME_MODE"):
                    init_dict["reframe_mode"] = os.getenv("REFRAME_MODE")
                if os.getenv("REFRAME_STATIC_AUTO"):
                    try:
                        init_dict["reframe_static_auto"] = int(os.getenv("REFRAME_STATIC_AUTO", "1"))
                    except ValueError:
                        pass
                if os.getenv("ZERNIO_API_KEY"):
                    init_dict["zernio_api_key"] = os.getenv("ZERNIO_API_KEY")
                if os.getenv("ZERNIO_BASE_URL"):
                    init_dict["zernio_base_url"] = os.getenv("ZERNIO_BASE_URL")
                if os.getenv("TWITCH_CLIENT_ID"):
                    init_dict["twitch_client_id"] = os.getenv("TWITCH_CLIENT_ID")
                if os.getenv("TWITCH_CLIENT_SECRET"):
                    init_dict["twitch_client_secret"] = os.getenv("TWITCH_CLIENT_SECRET")

                self._cached_config = CliporaConfig.model_validate(init_dict)
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write_json(self.config_path, self._cached_config.model_dump())

    def get_config(self) -> CliporaConfig:
        with self._lock:
            if self._cached_config is None:
                self._load_initial()
            assert self._cached_config is not None
            return self._cached_config.model_copy()

    def get_redacted_config(self) -> dict[str, Any]:
        """Return config with secrets masked for safe client delivery."""
        cfg = self.get_config().model_dump()
        for key in SECRET_KEYS:
            val = cfg.get(key, "")
            if val:
                if len(val) > 8:
                    cfg[key] = f"{val[:3]}...{val[-4:]}"
                else:
                    cfg[key] = "********"
            else:
                cfg[key] = ""
        return cfg

    def update_config(self, patch: dict[str, Any]) -> CliporaConfig:
        with self._lock:
            current = self.get_config().model_dump()
            for k, v in patch.items():
                if v is not None:
                    # Ignore masked values when updating
                    if k in SECRET_KEYS and isinstance(v, str) and ("..." in v or v == "********"):
                        continue
                    current[k] = v

            updated = CliporaConfig.model_validate(current)
            atomic_write_json(self.config_path, updated.model_dump())
            self._cached_config = updated
            return updated.model_copy()

# Global default store singleton
_global_config_store = ConfigStore()

def get_config_store() -> ConfigStore:
    return _global_config_store
