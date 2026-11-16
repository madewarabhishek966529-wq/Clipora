"""Zernio Social API client & SmartScheduler prime-time algorithm."""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from clipora.core.errors import PublishError
from clipora.core.netutil import validate_url_ssrf_safe

class SmartScheduler:
    """Calculates peak viral prime-time slots with minimum spacing guarantees."""

    @staticmethod
    def calculate_prime_time_slot(
        existing_slots: List[datetime],
        base_time: Optional[datetime] = None,
        min_gap_seconds: int = 5400,  # 90 minutes minimum spacing
        batch_day_offset: int = 0,
    ) -> datetime:
        """Find the earliest optimal prime-time posting window (18:00-21:00 UTC)."""
        now = base_time or datetime.now(timezone.utc)
        # Offset for batch scheduling (e.g. 1 clip per day)
        target_date = (now + timedelta(days=batch_day_offset)).date()

        # Target prime-time start: 18:00 UTC
        candidate = datetime(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
            hour=18,
            minute=0,
            second=0,
            tzinfo=timezone.utc,
        )

        # If candidate is already in the past, push to next day or later tonight
        if candidate < now:
            if now.hour < 21:
                candidate = now + timedelta(minutes=15)
            else:
                candidate += timedelta(days=1)

        # Ensure min_gap_seconds from all existing scheduled slots
        sorted_existing = sorted(existing_slots)
        while True:
            conflict = False
            for slot in sorted_existing:
                gap = abs((candidate - slot).total_seconds())
                if gap < min_gap_seconds:
                    candidate = slot + timedelta(seconds=min_gap_seconds)
                    conflict = True
                    break
            if not conflict:
                break

        return candidate

class ZernioClient:
    """REST client for Zernio multi-platform social media distribution."""

    def __init__(self, api_key: str, base_url: str = "https://api.zernio.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def get_presigned_upload_url(self, filename: str = "clip.mp4") -> Dict[str, Any]:
        """Request presigned upload URL from Zernio and validate host for SSRF safety."""
        if not self.api_key:
            raise PublishError("Zernio API key is not configured.")

        url = f"{self.base_url}/v1/media/upload-url"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"filename": filename, "content_type": "video/mp4"}

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    raise PublishError(f"Zernio upload URL error ({res.status_code}): {res.text}")
                data = res.json()
                upload_url = data.get("upload_url", "")

                # SSRF Shield: ensure presigned URL target host is public
                validate_url_ssrf_safe(upload_url)
                return data
        except httpx.RequestError as e:
            raise PublishError(f"Failed to reach Zernio media API: {e}") from e

    def upload_video_bytes(self, presigned_url: str, video_path: Path | str) -> None:
        """Upload raw MP4 bytes to presigned storage endpoint."""
        p = Path(video_path).resolve()
        if not p.is_file():
            raise PublishError(f"Video file not found for upload: {video_path}")

        validate_url_ssrf_safe(presigned_url)

        try:
            with open(p, "rb") as f:
                with httpx.Client(timeout=300.0) as client:
                    res = client.put(presigned_url, content=f.read(), headers={"Content-Type": "video/mp4"})
                    if res.status_code not in (200, 201, 204):
                        raise PublishError(f"Storage upload failed ({res.status_code}): {res.text}")
        except httpx.RequestError as e:
            raise PublishError(f"Failed to upload video bytes to presigned URL: {e}") from e

    def create_post(
        self,
        idempotency_key: str,
        media_id: str,
        platforms: List[str],
        caption: str,
        title: Optional[str] = None,
        scheduled_for: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit post intent with Idempotency-Key header to prevent duplicate publishes."""
        if not self.api_key:
            raise PublishError("Zernio API key is not configured.")

        url = f"{self.base_url}/v1/posts"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": idempotency_key,
        }
        payload: Dict[str, Any] = {
            "media_id": media_id,
            "platforms": platforms,
            "caption": caption,
        }
        if title:
            payload["title"] = title
        if scheduled_for:
            payload["scheduled_for"] = scheduled_for

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code in (200, 201):
                    return res.json()
                elif res.status_code == 409:
                    # Idempotency conflict / currently processing
                    retry_after = int(res.headers.get("Retry-After", "5"))
                    time.sleep(retry_after)
                    # Retry once with same Idempotency-Key
                    res_retry = client.post(url, json=payload, headers=headers)
                    if res_retry.status_code in (200, 201):
                        return res_retry.json()
                    raise PublishError(f"Zernio publish conflict ({res_retry.status_code}): {res_retry.text}")
                else:
                    raise PublishError(f"Zernio post creation error ({res.status_code}): {res.text}")
        except httpx.RequestError as e:
            raise PublishError(f"Zernio publish network error: {e}") from e
