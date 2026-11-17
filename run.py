"""Convenience launcher for Clipora FastAPI Gateway."""

import sys
from pathlib import Path
import uvicorn

_project_root = Path(__file__).resolve().parent
_src_dir = _project_root / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

if __name__ == "__main__":
    print("[Clipora] Starting Clipora / ClippyMe API Gateway...")
    print(f"[Clipora] Reload directory scoped to: {_src_dir}")
    print("[Clipora] Media and runtime folders (output, data, uploads) are excluded from hot-reload.")
    uvicorn.run(
        "clippyme.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(_src_dir)],
        reload_excludes=[
            "data",
            "output",
            "uploads",
            "*.log",
            "*.mp4",
            "*.m4a",
            "*.webm",
            "*.json",
            "*.part",
            "*.ytdl",
        ],
    )
