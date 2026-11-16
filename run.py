"""Convenience launcher for Clipora FastAPI Gateway."""

import sys
from pathlib import Path
import uvicorn

_src_dir = Path(__file__).resolve().parent / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

if __name__ == "__main__":
    uvicorn.run("clipora.api.app:app", host="0.0.0.0", port=8000, reload=True)
