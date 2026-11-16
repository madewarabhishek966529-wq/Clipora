"""Scene boundary detection using PySceneDetect with graceful heuristic fallback."""

from pathlib import Path
from typing import List, Tuple
import logging

logger = logging.getLogger("clipora.scenes")

def detect_scenes(
    video_path: Path | str,
    threshold: float = 27.0,
    min_scene_len_sec: float = 2.0,
    fallback_window_sec: float = 5.0,
) -> List[Tuple[float, float]]:
    """Detect visual shot cuts in video. Falls back to fixed windows if PySceneDetect is absent."""
    path = Path(video_path).resolve()
    if not path.is_file():
        return []

    try:
        from scenedetect import open_video, SceneManager, ContentDetector

        video = open_video(str(path))
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=int(min_scene_len_sec * video.frame_rate)))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        scenes: List[Tuple[float, float]] = []
        for start_time, end_time in scene_list:
            scenes.append((start_time.get_seconds(), end_time.get_seconds()))

        if scenes:
            return scenes
    except (ImportError, Exception) as e:
        logger.debug(f"PySceneDetect unavailable ({e}), using fallback fixed window segmentation.")

    # Heuristic fallback: segment every fallback_window_sec
    from clipora.media.media_probe import probe_media
    try:
        info = probe_media(path)
        total_dur = info.duration
    except Exception:
        total_dur = 60.0

    scenes: List[Tuple[float, float]] = []
    curr = 0.0
    while curr < total_dur:
        nxt = min(curr + fallback_window_sec, total_dur)
        scenes.append((round(curr, 3), round(nxt, 3)))
        curr = nxt

    return scenes
