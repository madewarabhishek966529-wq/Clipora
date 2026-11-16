"""Computer vision vertical reframing, tripod camera math, and scene detection."""

from clipora.pipeline.reframe.reframe_ops import (
    compute_9_16_crop_dimensions,
    clamp_crop_x,
    classify_shot_type,
    collapse_scene_targets,
    OneEuroFilter,
)
from clipora.pipeline.reframe.reframe_track import Cameraman
from clipora.pipeline.reframe.scene_detection import detect_scenes
from clipora.pipeline.reframe.reframe import reframe_video_to_vertical

__all__ = [
    "compute_9_16_crop_dimensions",
    "clamp_crop_x",
    "classify_shot_type",
    "collapse_scene_targets",
    "OneEuroFilter",
    "Cameraman",
    "detect_scenes",
    "reframe_video_to_vertical",
]
