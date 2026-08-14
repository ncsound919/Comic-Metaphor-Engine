"""MCP server exposing the Comic Metaphor Engine as internal strategy tools.

Run: python mcp/server.py   (stdio transport — use with Claude/opencode/fleet agents)

Tools:
    list_protocols          — all comic metaphor protocols in the library
    search_protocols        — semantic search of the library for a topic
    generate_mapping        — map a real-world problem to a comic storyline (scored)
    generate_lesson         — compact learning lesson for a topic
    generate_insight_report — strategy insight report from narrative text
    strategy_brief          — full brief: mapping + scores + lesson + narrative
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

mcp = FastMCP("comic-metaphor-engine")

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from engine.codex_adapter import CodexAdapter
        from engine.index import MetaphorIndex
        from engine.metaphor_engine import MetaphorEngine

        index = MetaphorIndex(processed_dir=str(_ROOT / "processed"), lazy=True)
        _engine = MetaphorEngine(index, CodexAdapter(index))
    return _engine


def _enum(enum_cls, value: str, default):
    try:
        return enum_cls(value)
    except ValueError:
        return default


def _scores(mapping) -> Dict[str, float]:
    return {
        "trueness": round(mapping.trueness_score, 4),
        "flow": round(mapping.flow_score, 4),
        "pcs": round(mapping.pcs_score, 4),
        "overall_fit": round(mapping.overall_fit, 4),
        "tap": round(mapping.tap_score, 4),
    }


@mcp.tool()
def list_protocols() -> List[Dict[str, Any]]:
    """List every comic metaphor protocol in the library."""
    return [p.to_dict() for p in _get_engine().index.protocol_list]


@mcp.tool()
def search_protocols(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search the comic metaphor library for protocols matching a problem or topic."""
    results = _get_engine().index.search_protocols(
        query, top_k=top_k, return_scores=True
    )
    return [
        {
            "protocol_id": p.id,
            "similarity": round(float(s), 4),
            "archetype": p.archetype,
            "business_logic": p.business_logic,
            "themes": p.themes,
            "risk_categories": [r.value for r in p.risk_categories],
        }
        for p, s in results
    ]


@mcp.tool()
def generate_mapping(
    topic: str, format: str = "blog_post", tone: str = "hopeful", top_k: int = 3
) -> Dict[str, Any]:
    """Map a real-world problem to a comic book storyline, scored by the codex engine."""
    from engine.schema import FormatType, ToneType

    mapping = _get_engine().generate_mapping(
        topic=topic,
        target_format=_enum(FormatType, format, FormatType.BLOG_POST),
        target_tone=_enum(ToneType, tone, ToneType.HOPEFUL),
        top_k=top_k,
    )
    return mapping.to_dict()


@mcp.tool()
def generate_lesson(topic: str, format: str = "podcast_monologue", tone: str = "hopeful") -> Dict[str, Any]:
    """Generate a compact learning lesson for a topic via comic metaphor."""
    from engine.explainers import generate_lesson as explainer_lesson
    from engine.schema import FormatType, ToneType

    engine = _get_engine()
    mapping = engine.generate_mapping(
        topic=topic,
        target_format=_enum(FormatType, format, FormatType.PODCAST_MONOLOGUE),
        target_tone=_enum(ToneType, tone, ToneType.HOPEFUL),
    )
    protocol = engine.index.get_protocol_by_id(mapping.protocol_id)
    return explainer_lesson(mapping, protocol)


@mcp.tool()
def generate_insight_report(text: str, filename: str = "strategy.txt") -> Dict[str, Any]:
    """Generate a strategy insight report from narrative text: themes, characters,
    real-world metaphor mappings, codex scores, takeaways, and action items."""
    from engine.comic_insights import build_insight_report

    return build_insight_report(text, filename)


@mcp.tool()
def strategy_brief(topic: str, word_count: int = 600) -> Dict[str, Any]:
    """Full strategy brief for a topic: metaphor mapping + codex scores + lesson + narrative."""
    from engine.explainers import generate_lesson as explainer_lesson
    from engine.narrative_generator import NarrativeGenerator
    from engine.schema import FormatType, GenerationContext, ToneType

    engine = _get_engine()
    mapping = engine.generate_mapping(
        topic=topic,
        target_format=FormatType.BLOG_POST,
        target_tone=ToneType.HOPEFUL,
    )
    protocol = engine.index.get_protocol_by_id(mapping.protocol_id)
    lesson = explainer_lesson(mapping, protocol)
    ctx = GenerationContext(
        mapping=mapping, protocol=protocol, word_count_target=word_count
    )
    narrative = NarrativeGenerator().generate(ctx)
    return {
        "topic": topic,
        "protocol_id": mapping.protocol_id,
        "codex_scores": _scores(mapping),
        "mappings": mapping.to_dict().get("mappings", []),
        "lesson": lesson,
        "narrative": narrative.to_dict(),
    }


if __name__ == "__main__":
    mcp.run()
