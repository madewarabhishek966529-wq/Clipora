"""Clipora core domain primitives, errors, and schemas."""

from clipora.core.errors import (
    CliporaError,
    ValidationError,
    SSRFError,
    JobNotFoundError,
    JobAlreadyExistsError,
    JobCancelledError,
    JobExecutionError,
    SubprocessCrashError,
    ConfigError,
    TranscriptionError,
    ViralityAnalysisError,
    PublishError,
    RateLimitExceededError,
)

__all__ = [
    "CliporaError",
    "ValidationError",
    "SSRFError",
    "JobNotFoundError",
    "JobAlreadyExistsError",
    "JobCancelledError",
    "JobExecutionError",
    "SubprocessCrashError",
    "ConfigError",
    "TranscriptionError",
    "ViralityAnalysisError",
    "PublishError",
    "RateLimitExceededError",
]
