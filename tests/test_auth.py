"""Tests for api.auth (Supabase JWT auth dependency)."""
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


def test_dev_user_when_unconfigured(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    from api import supabase as sbmod
    from api.auth import get_current_user

    sbmod.get_sb.cache_clear()
    user = get_current_user(FakeRequest({}))
    assert user["id"] == "dev-user"
    assert user["plan"] == "creator"


def test_missing_token_raises(monkeypatch):
    from api import supabase as sbmod
    from api.auth import get_current_user

    monkeypatch.setattr(sbmod, "get_sb", lambda: object())
    with pytest.raises(HTTPException) as exc:
        get_current_user(FakeRequest({}))
    assert exc.value.status_code == 401


def test_invalid_token_raises(monkeypatch):
    from api import supabase as sbmod
    from api.auth import get_current_user

    class FakeAuth:
        def get_user(self, token):
            raise Exception("bad token")

    class FakeSB:
        auth = FakeAuth()

    monkeypatch.setattr(sbmod, "get_sb", lambda: FakeSB())
    with pytest.raises(HTTPException) as exc:
        get_current_user(FakeRequest({"Authorization": "Bearer bad.token.here"}))
    assert exc.value.status_code == 401


def test_valid_token_returns_user(monkeypatch):
    from api import supabase as sbmod
    from api.auth import get_current_user

    class FakeUser:
        id = "abc-123"
        email = "writer@example.com"

    class FakeAuth:
        def get_user(self, token):
            return type("Res", (), {"user": FakeUser()})()

    class FakeSB:
        auth = FakeAuth()

    monkeypatch.setattr(sbmod, "get_sb", lambda: FakeSB())
    user = get_current_user(FakeRequest({"Authorization": "Bearer ok.token"}))
    assert user["id"] == "abc-123"
    assert user["email"] == "writer@example.com"


def test_partial_config_raises(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    from api import supabase as sbmod

    sbmod.get_sb.cache_clear()
    with pytest.raises(RuntimeError):
        sbmod.get_sb()
