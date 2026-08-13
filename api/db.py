"""Data access for users, comics, and insights via Supabase PostgREST.

Every function is a no-op / dev default when Supabase is unconfigured so
local dev and CI never require a running Supabase project.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from api import supabase as sbmod

_ACTIVE_STATUSES = ("active", "trialing")


def upsert_user(user_id: str, email: str) -> None:
    sb = sbmod.get_sb()
    if sb is None:
        return
    sb.table("users").upsert(
        {"supabase_uid": user_id, "email": email, "plan": "free"},
        on_conflict="supabase_uid",
    ).execute()


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    sb = sbmod.get_sb()
    if sb is None:
        return {"supabase_uid": user_id, "plan": "creator", "subscription_status": "active"}
    rows = (
        sb.table("users")
        .select("*")
        .eq("supabase_uid", user_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def is_creator(user_id: str) -> bool:
    user = get_user(user_id)
    if user is None:
        return False
    if user.get("plan") != "creator" or user.get("subscription_status") not in _ACTIVE_STATUSES:
        return False
    period_end = user.get("current_period_end")
    if period_end is None:
        return True  # dev default row has no period end
    return isinstance(period_end, (int, float)) and period_end > time.time()


def insert_comic(user_id: str, comic: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a comic. In dev (Supabase unconfigured) returns the input dict
    unchanged; in prod returns the DB row, which may include generated fields."""
    sb = sbmod.get_sb()
    if sb is None:
        return comic
    return sb.table("comics").insert(comic).execute().data[0]


def list_comics(user_id: str) -> List[Dict[str, Any]]:
    sb = sbmod.get_sb()
    if sb is None:
        return []
    return (
        sb.table("comics")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )


def insert_insight(user_id: str, comic_id: str, report: Dict[str, Any]) -> None:
    sb = sbmod.get_sb()
    if sb is None:
        return
    sb.table("insights").insert(
        {"comic_id": comic_id, "user_id": user_id, "report": report}
    ).execute()


def get_insight(comic_id: str) -> Optional[Any]:
    sb = sbmod.get_sb()
    if sb is None:
        return None
    rows = (
        sb.table("insights")
        .select("report")
        .eq("comic_id", comic_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    return rows[0]["report"] if rows else None


def update_comic_status(comic_id: str, status: str, error: str = "") -> None:
    sb = sbmod.get_sb()
    if sb is None:
        return
    payload: Dict[str, Any] = {"status": status}
    if error:
        payload["error"] = error
    sb.table("comics").update(payload).eq("id", comic_id).execute()


def set_subscription(user_id: str, **fields: Any) -> None:
    sb = sbmod.get_sb()
    if sb is None:
        return
    sb.table("users").update(fields).eq("supabase_uid", user_id).execute()
