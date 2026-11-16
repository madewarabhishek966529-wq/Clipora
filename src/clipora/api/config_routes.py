"""Configuration and credential vault routes."""

from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from clipora.api.schemas import ConfigPatchRequest
from clipora.storage.config_store import get_config_store
from clipora.storage.atomic import atomic_write_bytes

router = APIRouter(prefix="/api/config", tags=["Configuration"])

@router.get("")
def get_configuration():
    """Retrieve application configuration with masked secrets for UI display."""
    return get_config_store().get_redacted_config()

@router.post("")
def update_configuration(patch: ConfigPatchRequest):
    """Atomically update application configuration parameters."""
    updates = patch.model_dump(exclude_unset=True)
    get_config_store().update_config(updates)
    return get_config_store().get_redacted_config()

@router.post("/cookies")
async def upload_cookies_file(file: UploadFile = File(...)):
    """Upload Netscape-formatted cookies.txt to authenticate yt-dlp against YouTube."""
    content = await file.read()
    dest = Path("data/cookies.txt")
    atomic_write_bytes(dest, content)
    return {"status": "success", "message": "cookies.txt uploaded successfully."}

@router.post("/logo")
async def upload_logo_watermark(file: UploadFile = File(...)):
    """Upload brand PNG watermark logo."""
    content = await file.read()
    dest = Path("data/logo.png")
    atomic_write_bytes(dest, content)
    return {"status": "success", "message": "Brand watermark logo uploaded successfully."}

@router.post("/fonts")
async def upload_font_file(file: UploadFile = File(...)):
    """Upload user TrueType or OpenType font for subtitle rendering."""
    filename = Path(file.filename or "custom_font.ttf").name
    if not (filename.endswith(".ttf") or filename.endswith(".otf")):
        raise HTTPException(status_code=400, detail="Only .ttf or .otf font files are supported.")
    content = await file.read()
    dest = Path("data/fonts") / filename
    atomic_write_bytes(dest, content)
    return {"status": "success", "filename": filename, "message": "Font installed successfully."}
