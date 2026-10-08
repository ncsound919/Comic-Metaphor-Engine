"""Tests for the REST API (api.main) — health, search, map, explain, lesson,
narrative, protocol listing/detail, and the lesson/narrative/strategy
enrichment added for the Global Lens outlet."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture(scope="module")
def client(index, engine):
    """API test client backed by the session index/engine (so no model reload)."""
    import api.main as main

    main.get_index = lambda: index
    main.get_engine = lambda: engine
    return TestClient(main.app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["protocols_loaded"] >= 6


def test_list_protocols(client):
    r = client.get("/api/protocols")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] > 0
    first = body["protocols"][0]
    assert "id" in first and "archetype" in first and "themes" in first


def test_list_protocols_filtered(client):
    r = client.get("/api/protocols?protocol_type=custom&limit=5")
    assert r.status_code == 200
    body = r.json()
    assert len(body["protocols"]) <= 5
    for p in body["protocols"]:
        assert p["protocol_type"] == "custom"


def test_get_protocol_by_id(client, index):
    pid = index.protocol_list[0].id
    r = client.get(f"/api/protocols/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid


def test_get_protocol_404(client):
    r = client.get("/api/protocols/does_not_exist")
    assert r.status_code == 404


def test_search(client):
    r = client.post("/api/search", json={"query": "burnout", "top_k": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["results"]
    assert body["results"][0]["protocol_id"]


def test_search_rejects_short_query(client):
    r = client.post("/api/search", json={"query": "x"})
    assert r.status_code == 422


def test_map_returns_enriched_payload(client):
    r = client.post(
        "/api/map",
        json={
            "topic": "startup burnout",
            "format": "podcast_monologue",
            "tone": "hopeful",
            "top_k": 3,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["protocol_id"]
    # Enrichment added for the Global Lens outlet
    assert "lesson" in body
    assert "narrative" in body
    assert "strategy" in body


def test_map_seed_arc_carries_strategy(client):
    r = client.post(
        "/api/map",
        json={
            "topic": "ex-employees leaked the core algorithm to competitors",
            "format": "blog_post",
            "tone": "inspirational",
            "top_k": 5,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["protocol_id"] == "armor_wars"
    assert "Protect and audit your core IP" in body["lesson"]
    assert body["strategy"]["strategy_type"]


def test_map_invalid_enum_falls_back(client):
    r = client.post(
        "/api/map",
        json={"topic": "burnout", "format": "not_a_format", "tone": "not_a_tone"},
    )
    assert r.status_code == 200


def test_explain(client):
    r = client.post(
        "/api/explain",
        json={"topic": "technical debt", "format": "blog_post", "tone": "cautionary"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "mapping" in body and "explanation" in body


def test_lesson_endpoint(client):
    r = client.post(
        "/api/lesson",
        json={"topic": "impostor syndrome in founders", "format": "blog_post", "tone": "inspirational"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["lesson"]["lesson_id"].startswith("lesson_")
    assert body["lesson"]["takeaways"]


def test_narrative_endpoint(client):
    r = client.post(
        "/api/narrative",
        json={
            "topic": "leadership crisis",
            "format": "podcast_monologue",
            "tone": "gritty",
            "word_count_target": 400,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["narrative"]["title"]
    assert body["narrative"]["word_count"] > 0


def test_narrative_rejects_short_word_count(client):
    r = client.post(
        "/api/narrative",
        json={"topic": "burnout", "word_count_target": 50},
    )
    assert r.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])