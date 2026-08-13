"""Tests for api.uploads validation helpers."""
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from api.uploads import _validate_upload  # noqa: E402


def test_accepts_supported_extensions():
    for name in ("comic.pdf", "script.txt", "story.md", "book.epub"):
        assert _validate_upload(name, b"x") == Path(name).suffix.lower()


def test_rejects_unsupported_extension():
    with pytest.raises(HTTPException) as exc:
        _validate_upload("malware.exe", b"x")
    assert exc.value.status_code == 400


def test_rejects_oversized_file():
    big = b"0" * (25 * 1024 * 1024 + 1)
    with pytest.raises(HTTPException) as exc:
        _validate_upload("comic.pdf", big)
    assert exc.value.status_code == 400


def test_rejects_missing_filename():
    with pytest.raises(HTTPException) as exc:
        _validate_upload(None, b"x")
    assert exc.value.status_code == 400


def test_guard_creator_402(monkeypatch):
    from api import uploads as uploads_mod

    monkeypatch.setattr(uploads_mod, "is_creator", lambda uid: False)
    with pytest.raises(HTTPException) as exc:
        uploads_mod._guard_creator({"id": "u1"})
    assert exc.value.status_code == 402


def test_upload_happy_path(monkeypatch, tmp_path):
    import asyncio
    import io

    import engine.comic_insights as ci
    from api import uploads as uploads_mod
    from starlette.datastructures import Headers, UploadFile
    from starlette.requests import Request

    monkeypatch.setattr(uploads_mod, "get_sb", lambda: None)
    monkeypatch.setattr(uploads_mod, "is_creator", lambda uid: True)
    monkeypatch.setattr(uploads_mod, "insert_comic", lambda uid, comic: comic)
    monkeypatch.setattr(uploads_mod, "insert_insight", lambda uid, cid, report: None)
    monkeypatch.setattr(uploads_mod, "update_comic_status", lambda cid, status, error="": None)

    monkeypatch.setattr(
        ci,
        "extract_text_from_file",
        lambda path, filename: {
            "text": "Peter Parker lost everything when his invention was stolen.",
            "page_count": 1,
            "status": "ready",
        },
    )
    monkeypatch.setattr(
        ci,
        "build_insight_report",
        lambda text, filename: {
            "report_id": "insight_abc",
            "source_file": filename,
            "themes": ["trust"],
            "codex_scores": {"trueness": 0.7},
            "takeaways": ["t"],
            "action_items": ["a"],
        },
    )

    file = UploadFile(
        filename="comic.txt",
        file=io.BytesIO(b"comic data"),
        headers=Headers({"content-type": "text/plain"}),
    )
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/upload",
            "headers": [],
        }
    )
    result = asyncio.run(uploads_mod.upload(request, file, {"id": "u1"}))
    assert result["comic"]["status"] == "ready"
    assert result["comic"]["page_count"] == 1
    assert result["insight"]["report_id"] == "insight_abc"


def test_upload_rejects_large_content_length(monkeypatch):
    import asyncio
    import io

    from api import uploads as uploads_mod
    from starlette.datastructures import Headers, UploadFile
    from starlette.requests import Request

    monkeypatch.setattr(uploads_mod, "is_creator", lambda uid: True)

    file = UploadFile(
        filename="comic.txt",
        file=io.BytesIO(b"small"),
        headers=Headers({"content-type": "text/plain"}),
    )
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/upload",
            "headers": [(b"content-length", str(25 * 1024 * 1024 + 1).encode())],
        }
    )
    with pytest.raises(HTTPException) as exc:
        asyncio.run(uploads_mod.upload(request, file, {"id": "u1"}))
    assert exc.value.status_code == 400
