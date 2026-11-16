"""24/7 Autonomous live stream and VOD monitor registry."""

import asyncio
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from clipora.storage.atomic import atomic_write_json, read_json_safe
from clipora.storage.config_store import get_config_store
from clipora.jobs.job_submission import get_job_queue
from clipora.integrations.kick_client import check_kick_stream_status
from clipora.integrations.twitch_client import TwitchClient
from clipora.integrations.youtube_client import get_latest_youtube_uploads

logger = logging.getLogger("clipora.live_monitor")
MONITOR_PATH = Path("data/live_monitor.json")
_MONITOR_LOCK = threading.Lock()

class LiveMonitorRegistry:
    """Manages channel monitoring configs, poll cycles, and automated job submissions."""

    def __init__(self, state_path: Path | str = MONITOR_PATH):
        self.state_path = Path(state_path)
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._publish_lock = asyncio.Lock() # Lock serializing automated publish slots

    def _load(self) -> Dict[str, Any]:
        return read_json_safe(self.state_path, default={"monitors": []})

    def _save(self, data: Dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.state_path, data)

    def list_monitors(self) -> List[Dict[str, Any]]:
        with _MONITOR_LOCK:
            return self._load().get("monitors", [])

    def add_monitor(
        self,
        platform: str,
        channel_id: str,
        enabled: bool = True,
        prelive_skip_minutes: int = 30,
        segment_slice_minutes: int = 30,
        min_viral_score: int = 70,
        auto_publish: bool = False,
    ) -> Dict[str, Any]:
        """Register a creator channel for 24/7 autonomous monitoring."""
        with _MONITOR_LOCK:
            data = self._load()
            monitors = data.setdefault("monitors", [])
            entry = {
                "id": f"{platform.lower()}_{channel_id.lower()}",
                "platform": platform.lower(),
                "channel_id": channel_id,
                "enabled": enabled,
                "prelive_skip_minutes": prelive_skip_minutes,
                "segment_slice_minutes": segment_slice_minutes,
                "min_viral_score": min_viral_score,
                "auto_publish": auto_publish,
                "last_checked_at": None,
                "last_detected_url": None,
                "is_active_live": False,
            }
            # Replace if already exists
            monitors = [m for m in monitors if m["id"] != entry["id"]]
            monitors.append(entry)
            data["monitors"] = monitors
            self._save(data)
            return entry

    def remove_monitor(self, monitor_id: str) -> bool:
        with _MONITOR_LOCK:
            data = self._load()
            before = len(data.get("monitors", []))
            data["monitors"] = [m for m in data.get("monitors", []) if m["id"] != monitor_id]
            self._save(data)
            return len(data["monitors"]) < before

    async def check_channel_once(self, monitor: Dict[str, Any]) -> None:
        """Poll platform for live status or new uploads."""
        platform = monitor["platform"]
        channel = monitor["channel_id"]
        cfg = get_config_store().get_config()

        detected_url: Optional[str] = None
        is_live = False

        if platform == "kick":
            res = check_kick_stream_status(channel)
            is_live = res.get("is_live", False)
            if is_live:
                detected_url = f"https://kick.com/{channel}"

        elif platform == "twitch":
            client = TwitchClient(cfg.twitch_client_id, cfg.twitch_client_secret)
            res = client.check_stream_status(channel)
            is_live = res.get("is_live", False)
            if is_live:
                detected_url = f"https://twitch.tv/{channel}"

        elif platform == "youtube":
            uploads = get_latest_youtube_uploads(channel)
            if uploads:
                latest = uploads[0]
                if latest["url"] != monitor.get("last_detected_url"):
                    detected_url = latest["url"]

        monitor["last_checked_at"] = datetime.now(timezone.utc).isoformat()
        monitor["is_active_live"] = is_live

        if detected_url and detected_url != monitor.get("last_detected_url"):
            monitor["last_detected_url"] = detected_url
            logger.info(f"Monitor {monitor['id']} detected new stream/video: {detected_url}. Auto-queuing...")
            try:
                queue = get_job_queue()
                await queue.submit_job(
                    source_url=detected_url,
                    reframe_mode=cfg.reframe_mode,
                )
            except Exception as e:
                logger.error(f"Failed to auto-queue job for {detected_url}: {e}")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                monitors = self.list_monitors()
                for m in monitors:
                    if m.get("enabled", True):
                        await self.check_channel_once(m)
                with _MONITOR_LOCK:
                    data = self._load()
                    data["monitors"] = monitors
                    self._save(data)
            except Exception as e:
                logger.error(f"Error during live monitor poll cycle: {e}")

            await asyncio.sleep(60.0) # Check every 60 seconds

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

_global_monitor_registry = LiveMonitorRegistry()

def get_live_monitor_registry() -> LiveMonitorRegistry:
    return _global_monitor_registry
