"""
Shared pytest fixtures.

The embedding model is loaded at most once per test session via the
engine's module-level singleton (engine.index.get_embedding_model), so a
session-scoped MetaphorIndex keeps the whole suite fast.
"""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture(scope="session")
def index():
    from engine.index import MetaphorIndex

    idx = MetaphorIndex(processed_dir=str(_ROOT / "processed"), lazy=True)
    assert len(idx.protocol_list) >= 6
    return idx


@pytest.fixture(scope="session")
def engine(index):
    from engine.codex_adapter import CodexAdapter
    from engine.metaphor_engine import MetaphorEngine

    return MetaphorEngine(index, CodexAdapter(index))


@pytest.fixture(scope="session")
def knowledge_base():
    from engine.schema import KnowledgeBase

    return KnowledgeBase.load(str(_ROOT / "processed" / "knowledge_base.json"))
