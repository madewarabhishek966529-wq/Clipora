"""Kick live stream checker with TLS/browser impersonation."""

from typing import Dict, Any, Optional
import httpx

KICK_API_BASE = "https://kick.com/api/v2"

def check_kick_stream_status(channel_slug: str) -> Dict[str, Any]:
    """Query Kick channel API to determine if channel is actively livestreaming."""
    slug = channel_slug.strip().lower()
    url = f"{KICK_API_BASE}/channels/{slug}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    # Attempt with curl_cffi if installed for TLS fingerprinting
    try:
        from curl_cffi import requests as cffi_requests
        res = cffi_requests.get(url, headers=headers, impersonate="chrome120", timeout=10)
        if res.status_code == 200:
            data = res.json()
            livestream = data.get("livestream")
            is_live = livestream is not None and livestream.get("is_live", False)
            return {
                "is_live": is_live,
                "title": livestream.get("session_title", "") if livestream else "",
                "duration_seconds": livestream.get("duration", 0) if livestream else 0,
                "viewer_count": livestream.get("viewer_count", 0) if livestream else 0,
            }
    except (ImportError, Exception):
        pass

    # Fallback to standard httpx
    try:
        with httpx.Client(timeout=10.0, headers=headers) as client:
            res = client.get(url)
            if res.status_code == 200:
                data = res.json()
                livestream = data.get("livestream")
                is_live = livestream is not None
                return {
                    "is_live": is_live,
                    "title": livestream.get("session_title", "") if livestream else "",
                    "duration_seconds": livestream.get("duration", 0) if livestream else 0,
                }
    except Exception:
        pass

    return {"is_live": False, "title": "", "duration_seconds": 0}
