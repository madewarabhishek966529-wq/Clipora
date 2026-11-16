"""Atomic file writing primitives with durability guarantees."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

def atomic_write_bytes(dest_path: str | Path, content: bytes, permissions: int = 0o600) -> None:
    """Atomically write binary content to destination path with fsync durability."""
    dest_path = Path(dest_path).resolve()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    target_dir = dest_path.parent

    fd, temp_file_path = tempfile.mkstemp(prefix=".tmp-", dir=target_dir)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        # Set restrictive permissions (best-effort on Windows)
        try:
            os.chmod(temp_file_path, permissions)
        except OSError:
            pass

        # Atomic commit
        os.replace(temp_file_path, dest_path)
    except Exception:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass
        raise

def atomic_write_text(dest_path: str | Path, content: str, encoding: str = "utf-8", permissions: int = 0o600) -> None:
    """Atomically write text content to destination path with fsync durability."""
    atomic_write_bytes(dest_path, content.encode(encoding), permissions=permissions)

def atomic_write_json(dest_path: str | Path, data: Any, indent: int = 2, permissions: int = 0o600) -> None:
    """Atomically write JSON data to destination path."""
    json_str = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write_text(dest_path, json_str, permissions=permissions)

def read_json_safe(path: str | Path, default: Any = None) -> Any:
    """Read JSON from file safely; returns default if missing or invalid."""
    p = Path(path)
    if not p.is_file():
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default
