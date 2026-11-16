"""Path sanitization, safe naming, and directory lifecycle helpers."""

import re
import unicodedata
from pathlib import Path

def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Normalize string into safe cross-platform filename without special chars or path traversals."""
    # Normalize unicode
    clean = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    # Replace non-alphanumeric chars with underscores
    clean = re.sub(r"[^\w\s-]", "", clean).strip()
    clean = re.sub(r"[-\s]+", "_", clean)
    if not clean:
        clean = "clipora_media"
    return clean[:max_length]

def ensure_directory(path: Path | str) -> Path:
    """Ensure directory exists with parent folders."""
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p
