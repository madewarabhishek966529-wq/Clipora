"""Unit tests for FastAPI REST routes."""

import pytest
from fastapi.testclient import TestClient
from clipora.api.app import app

client = TestClient(app)

def test_get_config_endpoint():
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "host" in data
    assert "port" in data
    assert "max_concurrent_jobs" in data

def test_update_config_endpoint():
    res = client.post("/api/config", json={"max_concurrent_jobs": 4})
    assert res.status_code == 200
    data = res.json()
    assert data["max_concurrent_jobs"] == 4

def test_create_job_validation_error():
    # Neither source_url nor input_file provided
    res = client.post("/api/jobs", json={})
    assert res.status_code in (400, 422)

def test_create_job_ssrf_shield():
    # Loopback or private IP target
    res = client.post("/api/jobs", json={"source_url": "http://127.0.0.1:8000/test.mp4"})
    assert res.status_code == 403
    assert "blocked" in res.json().get("error", "").lower()

def test_list_jobs_endpoint():
    res = client.get("/api/jobs")
    assert res.status_code == 200
    assert "jobs" in res.json()

def test_monitors_crud():
    # 1. Add monitor
    res_add = client.post(
        "/api/monitors",
        json={"platform": "kick", "channel_id": "streamer123", "enabled": True},
    )
    assert res_add.status_code == 200
    mon = res_add.json()["monitor"]
    assert mon["id"] == "kick_streamer123"

    # 2. List monitors
    res_list = client.get("/api/monitors")
    assert res_list.status_code == 200
    assert any(m["id"] == "kick_streamer123" for m in res_list.json()["monitors"])

    # 3. Delete monitor
    res_del = client.delete("/api/monitors/kick_streamer123")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"

def test_path_traversal_forbidden():
    res = client.get("/videos/../../etc/passwd")
    assert res.status_code in (403, 404)
