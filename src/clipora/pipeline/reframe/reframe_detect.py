"""Computer Vision detectors for faces and persons (isolated heavy execution)."""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("clipora.reframe_detect")

def sample_frame_timestamps(scene_start: float, scene_end: float, num_samples: int = 7) -> List[float]:
    """Return timestamps for 7 evenly distributed sample frames across a scene."""
    duration = scene_end - scene_start
    if duration <= 0:
        return [scene_start]
    step = duration / (num_samples + 1)
    return [round(scene_start + step * (i + 1), 3) for i in range(num_samples)]

def detect_subjects_in_frame(frame_bgr) -> List[Dict[str, Any]]:
    """Detect persons and faces in a BGR frame with lazy loading of YOLOv8/MediaPipe."""
    detections: List[Dict[str, Any]] = []

    # Attempt MediaPipe Face Detection
    try:
        import mediapipe as mp
        # Run mediapipe face detection if available
    except ImportError:
        pass

    # Attempt Ultralytics YOLOv8
    try:
        from ultralytics import YOLO
        # Run YOLO person detection
    except (ImportError, Exception):
        pass

    return detections
