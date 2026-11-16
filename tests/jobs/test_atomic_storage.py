"""Unit tests for atomic file storage operations."""

import json
import pytest
from pathlib import Path
from clipora.storage.atomic import atomic_write_text, atomic_write_json, read_json_safe

def test_atomic_write_text(tmp_path: Path):
    target = tmp_path / "test.txt"
    atomic_write_text(target, "Hello Clipora")
    assert target.is_file()
    assert target.read_text(encoding="utf-8") == "Hello Clipora"

def test_atomic_write_json(tmp_path: Path):
    target = tmp_path / "test.json"
    data = {"status": "ok", "count": 42}
    atomic_write_json(target, data)
    assert target.is_file()
    assert read_json_safe(target) == data

def test_read_json_safe_missing_or_corrupt(tmp_path: Path):
    missing = tmp_path / "nonexistent.json"
    assert read_json_safe(missing, default={"fallback": True}) == {"fallback": True}

    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{invalid json", encoding="utf-8")
    assert read_json_safe(corrupt, default=None) is None
