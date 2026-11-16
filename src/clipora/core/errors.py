"""Core errors and exceptions for Clipora."""

class CliporaError(Exception):
    """Base exception for all Clipora domain errors."""
    def __init__(self, message: str, status_code: int = 500, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class ValidationError(CliporaError):
    """Raised when input validation fails."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=400, details=details)

class SSRFError(CliporaError):
    """Raised when an untrusted or non-routable URL is rejected for security."""
    def __init__(self, message: str = "Invalid or restricted URL target.", details: dict | None = None):
        super().__init__(message, status_code=403, details=details)

class JobNotFoundError(CliporaError):
    """Raised when a requested job does not exist."""
    def __init__(self, job_id: str):
        super().__init__(f"Job '{job_id}' not found.", status_code=404, details={"job_id": job_id})

class JobAlreadyExistsError(CliporaError):
    """Raised when attempting to create a job that already exists."""
    def __init__(self, job_id: str):
        super().__init__(f"Job '{job_id}' already exists.", status_code=409, details={"job_id": job_id})

class JobCancelledError(CliporaError):
    """Raised when an operation is aborted because the job was cancelled."""
    def __init__(self, job_id: str):
        super().__init__(f"Job '{job_id}' was cancelled.", status_code=410, details={"job_id": job_id})

class JobExecutionError(CliporaError):
    """Raised when a subprocess or execution pipeline fails."""
    def __init__(self, message: str, exit_code: int | None = None, details: dict | None = None):
        d = details or {}
        if exit_code is not None:
            d["exit_code"] = exit_code
        super().__init__(message, status_code=500, details=d)

class SubprocessCrashError(JobExecutionError):
    """Raised when the pipeline orchestrator subprocess unexpectedly crashes."""
    def __init__(self, job_id: str, exit_code: int, details: dict | None = None):
        super().__init__(
            f"Subprocess for job '{job_id}' crashed with exit code {exit_code}.",
            exit_code=exit_code,
            details=details,
        )

class ConfigError(CliporaError):
    """Raised when configuration loading or updating fails."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=500, details=details)

class TranscriptionError(CliporaError):
    """Raised when ASR audio transcription fails across all providers."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=502, details=details)

class ViralityAnalysisError(CliporaError):
    """Raised when AI virality scoring or moment detection fails."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=502, details=details)

class PublishError(CliporaError):
    """Raised when social publishing or scheduling fails."""
    def __init__(self, message: str, status_code: int = 502, details: dict | None = None):
        super().__init__(message, status_code=status_code, details=details)

class RateLimitExceededError(CliporaError):
    """Raised when client request rate exceeds the allowed bucket."""
    def __init__(self, message: str = "Rate limit exceeded. Please wait before retrying."):
        super().__init__(message, status_code=429)
