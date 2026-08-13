"""Comic upload + insight generation endpoints."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from api.auth import get_current_user
from api.db import (
    get_insight,
    get_user,
    insert_comic,
    insert_insight,
    is_creator,
    list_comics,
    update_comic_status,
)
from api.supabase import get_sb

router = APIRouter(prefix="/api")

_ALLOWED_EXTS = {".pdf", ".txt", ".md", ".epub", ".cbz", ".cbr", ".cb7"}
_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _validate_upload(filename: Optional[str], data: bytes) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    suffix = Path(filename).suffix.lower()
    if suffix not in _ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix or 'unknown'}'. Allowed: {', '.join(sorted(_ALLOWED_EXTS))}",
        )
    if len(data) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 25 MB limit")
    return suffix


def _guard_creator(user: Dict[str, Any]) -> None:
    if not is_creator(user["id"]):
        raise HTTPException(
            status_code=402,
            detail="Creator plan required — subscribe to upload comics",
        )


@router.get("/me")
def me(user: Dict[str, Any] = Depends(get_current_user)):
    return {"user": get_user(user["id"]) or {"plan": "free"}}


@router.post("/upload")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
):
    _guard_creator(user)

    try:
        content_length = int(request.headers.get("content-length") or 0)
    except (TypeError, ValueError):
        content_length = 0
    if content_length > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 25 MB limit")

    data = await file.read()
    suffix = _validate_upload(file.filename, data)

    comic_id = str(uuid.uuid4())
    storage_path = f"comics/{user['id']}/{comic_id}{suffix}"
    sb = get_sb()
    if sb is not None:
        try:
            sb.storage.from_("comics").upload(
                storage_path,
                data,
                {"content-type": file.content_type or "application/octet-stream"},
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Storage upload failed: {exc}")

    comic: Dict[str, Any] = {
        "id": comic_id,
        "user_id": user["id"],
        "filename": file.filename or "untitled",
        "storage_path": storage_path,
        "size_bytes": len(data),
        "page_count": 0,
        "status": "processing",
    }
    insert_comic(user["id"], comic)

    tmp = Path(tempfile.gettempdir()) / f"{comic_id}{suffix}"
    try:
        tmp.write_bytes(data)
        from engine.comic_insights import build_insight_report, extract_text_from_file

        extracted = extract_text_from_file(tmp, comic["filename"])
        comic["page_count"] = extracted["page_count"]

        if extracted["status"] == "unsupported":
            comic["status"] = "unsupported"
            update_comic_status(comic_id, "unsupported")
            return {
                "comic": comic,
                "insight": None,
                "message": "OCR for image-based comics (CBZ/CBR) is coming soon.",
            }

        if extracted["status"] == "failed" or not extracted["text"].strip():
            comic["status"] = "failed"
            update_comic_status(comic_id, "failed", "No readable text could be extracted.")
            return {
                "comic": comic,
                "insight": None,
                "message": "No readable text could be extracted from this file.",
            }

        report = build_insight_report(extracted["text"], comic["filename"])
        insert_insight(user["id"], comic_id, report)
        comic["status"] = "ready"
        update_comic_status(comic_id, "ready")
        return {"comic": comic, "insight": report}
    except Exception as exc:
        comic["status"] = "failed"
        update_comic_status(comic_id, "failed", str(exc))
        return {"comic": comic, "insight": None, "message": str(exc)}
    finally:
        tmp.unlink(missing_ok=True)


@router.get("/comics")
def comics(user: Dict[str, Any] = Depends(get_current_user)):
    _guard_creator(user)
    return {"comics": list_comics(user["id"])}


@router.get("/comics/{comic_id}/insights")
def comic_insights(comic_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    _guard_creator(user)
    insight = get_insight(comic_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="No insight report found for this comic")
    return {"insight": insight}
