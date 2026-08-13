"""Tests for api.db (Supabase PostgREST data access)."""
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture(autouse=True)
def no_supabase(monkeypatch):
    from api import supabase as sbmod

    sbmod.get_sb.cache_clear()
    monkeypatch.setattr(sbmod, "get_sb", lambda: None)
    yield


def test_dev_mode_is_creator():
    from api.db import is_creator

    assert is_creator("any-user") is True


def test_dev_mode_get_user_defaults():
    from api.db import get_user

    user = get_user("any-user")
    assert user["plan"] == "creator"


def test_upsert_and_insert_are_noops():
    from api.db import insert_comic, insert_insight, upsert_user

    upsert_user("u1", "a@b.c")  # must not raise
    comic = insert_comic("u1", {"id": "c1"})
    assert comic["id"] == "c1"
    insert_insight("u1", "c1", {"x": 1})  # must not raise


class FakeTable:
    def __init__(self, result):
        self._result = result
        self.ops = []

    def select(self, *cols):
        self.ops.append(("select", cols))
        return self

    def eq(self, k, v):
        self.ops.append(("eq", k, v))
        return self

    def limit(self, n):
        self.ops.append(("limit", n))
        return self

    def order(self, col, desc=False):
        self.ops.append(("order", col, desc))
        return self

    def upsert(self, payload, on_conflict=None):
        self.ops.append(("upsert", payload, on_conflict))
        return self

    def insert(self, payload):
        self.ops.append(("insert", payload))
        return self

    def update(self, payload):
        self.ops.append(("update", payload))
        return self

    def execute(self):
        return type("Res", (), {"data": self._result})()


class FakeSB:
    def __init__(self, results=None):
        self._results = results or {}
        self.tables = []

    def table(self, name):
        t = FakeTable(self._results.get(name, []))
        self.tables.append((name, t))
        return t


def _patch_sb(monkeypatch, results=None):
    from api import supabase as sbmod

    fake = FakeSB(results)
    monkeypatch.setattr(sbmod, "get_sb", lambda: fake)
    return fake


def test_get_user_returns_row(monkeypatch):
    from api import db

    fake = _patch_sb(
        monkeypatch,
        {"users": [{"supabase_uid": "u1", "plan": "creator", "subscription_status": "active"}]},
    )
    user = db.get_user("u1")
    assert user["plan"] == "creator"
    assert fake.tables[0][0] == "users"


def test_get_user_none_when_empty(monkeypatch):
    from api import db

    _patch_sb(monkeypatch, {"users": []})
    assert db.get_user("u1") is None


def test_is_creator_core_logic(monkeypatch):
    from api import db

    _patch_sb(monkeypatch, {"users": [{"plan": "creator", "subscription_status": "active"}]})
    assert db.is_creator("u1") is True
    _patch_sb(monkeypatch, {"users": [{"plan": "creator", "subscription_status": "canceled"}]})
    assert db.is_creator("u1") is False
    _patch_sb(monkeypatch, {"users": []})
    assert db.is_creator("u1") is False


def test_get_insight_unwraps_report(monkeypatch):
    from api import db

    _patch_sb(monkeypatch, {"insights": [{"report": {"x": 1}}]})
    assert db.get_insight("c1") == {"x": 1}


def test_set_subscription_updates(monkeypatch):
    from api import db

    fake = _patch_sb(monkeypatch)
    db.set_subscription("u1", plan="creator", subscription_status="active")
    name, tbl = fake.tables[0]
    assert name == "users"
    assert ("update", {"plan": "creator", "subscription_status": "active"}) in tbl.ops
    assert ("eq", "supabase_uid", "u1") in tbl.ops


def test_postgrest_errors_propagate(monkeypatch):
    from api import db

    class Boom:
        def table(self, name):
            raise RuntimeError("boom")

    from api import supabase as sbmod

    monkeypatch.setattr(sbmod, "get_sb", lambda: Boom())
    with pytest.raises(RuntimeError):
        db.list_comics("u1")


def test_is_creator_denies_expired_period(monkeypatch):
    from api import db

    _patch_sb(
        monkeypatch,
        {"users": [{"plan": "creator", "subscription_status": "active", "current_period_end": 1_000_000}]},
    )
    assert db.is_creator("u1") is False


def test_is_creator_grants_with_no_period(monkeypatch):
    from api import db

    _patch_sb(
        monkeypatch,
        {"users": [{"plan": "creator", "subscription_status": "active"}]},
    )
    assert db.is_creator("u1") is True
