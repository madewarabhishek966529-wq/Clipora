"""Root namespace shim forwarding to src/clipora."""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
_src_dir = _project_root / "src"

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

__path__ = [str(_src_dir / "clipora")]
