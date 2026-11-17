"""Clipora / ClippyMe root package."""

import sys
import clippyme

__version__ = "1.0.0"

# Re-export clippyme packages for seamless dual compatibility
api = clippyme.api
jobs = clippyme.jobs
pipeline = clippyme.pipeline
editing = clippyme.editing
core = clippyme.core
media = clippyme.media
monitoring = clippyme.monitoring
publishing = clippyme.publishing
storage = clippyme.storage

