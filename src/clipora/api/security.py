"""API security: token bucket rate limiter and path traversal prevention."""

import time
import threading
from pathlib import Path
from fastapi import Request, HTTPException
from clipora.core.errors import RateLimitExceededError

class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter per client IP."""

    def __init__(self, requests_per_minute: int = 60):
        self.capacity = float(requests_per_minute)
        self.refill_rate = self.capacity / 60.0
        self.tokens: dict[str, float] = {}
        self.last_refill: dict[str, float] = {}
        self._lock = threading.Lock()

    def check_request(self, client_ip: str) -> bool:
        with self._lock:
            now = time.time()
            if client_ip not in self.tokens:
                self.tokens[client_ip] = self.capacity
                self.last_refill[client_ip] = now

            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill[client_ip]
            self.tokens[client_ip] = min(self.capacity, self.tokens[client_ip] + elapsed * self.refill_rate)
            self.last_refill[client_ip] = now

            if self.tokens[client_ip] >= 1.0:
                self.tokens[client_ip] -= 1.0
                return True
            return False

_global_limiter = TokenBucketRateLimiter()

def rate_limit_dependency(request: Request) -> None:
    """FastAPI dependency enforcing client request rate limit."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not _global_limiter.check_request(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before submitting additional requests.",
        )

def assert_safe_path(requested_path: Path | str, base_directory: Path | str) -> Path:
    """Validate that requested path is strictly contained within base_directory (no path traversals)."""
    base = Path(base_directory).resolve()
    target = (base / requested_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Path traversal forbidden.")
    return target
