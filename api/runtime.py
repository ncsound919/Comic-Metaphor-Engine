"""
Engine Runtime
==============

Shared, lazily-initialized engine instances for the API server.

The embedding model is loaded on first use (see engine.index.get_embedding_model)
so the process boots fast and every request shares one model + one index.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engine.index import MetaphorIndex  # noqa: E402
from engine.metaphor_engine import MetaphorEngine  # noqa: E402
from engine.codex_adapter import CodexAdapter  # noqa: E402

_INDEX: Optional[MetaphorIndex] = None
_ENGINE: Optional[MetaphorEngine] = None
_ADAPTER: Optional[CodexAdapter] = None


def get_index() -> MetaphorIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = MetaphorIndex(processed_dir=str(_ROOT / "processed"), lazy=True)
    return _INDEX


def get_adapter() -> CodexAdapter:
    global _ADAPTER
    if _ADAPTER is None:
        _ADAPTER = CodexAdapter(get_index())
    return _ADAPTER


def get_engine() -> MetaphorEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = MetaphorEngine(get_index(), get_adapter())
    return _ENGINE
