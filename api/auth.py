"""Supabase JWT auth dependency for the FastAPI app.

When Supabase is unconfigured (dev mode) the dependency returns a synthetic
dev user with plan=creator so local development and CI are frictionless.
"""

from __future__ import annotations

from typing import Dict

from fastapi import HTTPException, Request

from api import supabase as sbmod


def get_current_user(request: Request) -> Dict[str, str]:
    sb = sbmod.get_sb()
    if sb is None:
        return {"id": "dev-user", "email": "dev@example.com", "plan": "creator"}

    header = request.headers.get("Authorization", "")
    token = header[len("Bearer "):].strip() if header.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        res = sb.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"id": res.user.id, "email": res.user.email or "", "plan": ""}
