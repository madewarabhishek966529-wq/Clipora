"""Clip domain logic, path resolution, and concurrency locks."""

from clipora.clips.clip_locks import clip_lock
from clipora.clips.clip_resolve import ClipPaths, resolve_clip_paths

__all__ = [
    "clip_lock",
    "ClipPaths",
    "resolve_clip_paths",
]
