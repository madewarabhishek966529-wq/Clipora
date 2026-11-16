"""Twitch Helix API client for monitoring creator live streams."""

import time
from typing import Dict, Any, Optional
import httpx

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_HELIX_STREAMS_URL = "https://api.twitch.tv/helix/streams"

class TwitchClient:
    """Twitch API client using app credentials for Helix queries."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        with httpx.Client(timeout=10.0) as client:
            res = client.post(TWITCH_TOKEN_URL, params=params)
            if res.status_code != 200:
                raise RuntimeError(f"Twitch token authentication failed: {res.text}")
            data = res.json()
            self._access_token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600)
            return self._access_token

    def check_stream_status(self, channel_login: str) -> Dict[str, Any]:
        """Check if a Twitch channel is actively streaming live."""
        if not self.client_id or not self.client_secret:
            return {"is_live": False, "title": ""}

        token = self._ensure_token()
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
        }
        params = {"user_login": channel_login.strip().lower()}

        with httpx.Client(timeout=10.0) as client:
            res = client.get(TWITCH_HELIX_STREAMS_URL, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json().get("data", [])
                if data:
                    stream = data[0]
                    return {
                        "is_live": stream.get("type") == "live",
                        "title": stream.get("title", ""),
                        "started_at": stream.get("started_at", ""),
                        "viewer_count": stream.get("viewer_count", 0),
                    }
        return {"is_live": False, "title": ""}
