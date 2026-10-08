"""Tests for the business-Marvel seed ingestion and strategy-block parsing
added to engine/ingest.py — the Global Lens fusion work."""

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engine.ingest import DataIngestionPipeline
from engine.schema import (
    BusinessModelLever,
    MoatType,
    StrategyType,
    ValueChainStage,
)


@pytest.fixture()
def pipeline(tmp_path):
    """A pipeline whose embedding model is stubbed (we only test parsing)."""
    p = DataIngestionPipeline.__new__(DataIngestionPipeline)
    p.raw_dir = Path(tmp_path)
    return p


def _make_seed(tmp_path, entries=None, raw=None):
    if raw is None:
        raw = {"protocols": entries or []}
    p = tmp_path / "seed.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    return str(p)


def test_seed_missing_file_returns_empty(pipeline, tmp_path):
    out = pipeline.parse_marvel_seed_json(str(tmp_path / "nope.json"))
    assert out == []


def test_seed_malformed_json_returns_empty(pipeline, tmp_path):
    p = tmp_path / "seed.json"
    p.write_text("{not json", encoding="utf-8")
    assert pipeline.parse_marvel_seed_json(str(p)) == []


def test_seed_entry_uses_bare_id(pipeline, tmp_path):
    seed = _make_seed(
        tmp_path,
        [
            {
                "protocol_id": "armor_wars",
                "name": "Armor Wars",
                "domains": ["strategy", "innovation", "risk"],
                "core_tension": "Proprietary tech leaked.",
                "lesson": "Protect your IP.",
                "narrative": "Tony dismantles his own legacy.",
                "beat_structure": ["Discovery", "Escalation", "Containment"],
            }
        ],
    )
    protocols = pipeline.parse_marvel_seed_json(seed)
    assert len(protocols) == 1
    proto = protocols[0]
    # Bare ID (no protocol_ prefix) so the outlet's attachSeed finds it
    assert proto.id == "armor_wars"
    assert proto.business_translation == "Protect your IP."
    assert proto.narrative.startswith("Tony")
    assert proto.application.startswith("Business-Marvel Seed")
    assert proto.protocol_type.value == "custom"


def test_seed_strategy_derived_from_domains(pipeline, tmp_path):
    seed = _make_seed(
        tmp_path,
        [
            {
                "protocol_id": "armor_wars",
                "name": "Armor Wars",
                "domains": ["strategy", "innovation", "risk"],
                "core_tension": "Tension",
                "lesson": "Lesson",
                "narrative": "Narrative",
                "beat_structure": [],
            }
        ],
    )
    protocols = pipeline.parse_marvel_seed_json(seed)
    strat = protocols[0].strategy
    assert strat is not None
    # First known domain in the entry wins the strategy type
    assert strat.strategy_type.value == StrategyType.DIFFERENTIATION.value  # from "strategy"
    assert strat.moat.value == MoatType.BRAND.value
    assert strat.value_chain_stage.value == ValueChainStage.MARKETING_SALES.value
    assert strat.business_model_lever.value == BusinessModelLever.MARGIN.value
    assert strat.target_segment == "strategy / innovation / risk"
    assert strat.confidence == 0.6


def test_seed_unknown_domains_get_neutral_strategy(pipeline, tmp_path):
    seed = _make_seed(
        tmp_path,
        [
            {
                "protocol_id": "mystery_arc",
                "name": "Mystery",
                "domains": ["???"],
                "core_tension": "T",
                "lesson": "L",
                "narrative": "N",
                "beat_structure": ["A"],
            }
        ],
    )
    protocols = pipeline.parse_marvel_seed_json(seed)
    assert protocols[0].strategy is None
    assert protocols[0].risk_categories[0].value == "transformation"  # default


def test_seed_entry_without_protocol_id_skipped(pipeline, tmp_path):
    seed = _make_seed(tmp_path, [{"name": "No Id", "core_tension": "x"}])
    assert pipeline.parse_marvel_seed_json(seed) == []


def test_seed_dimensions_from_beats(pipeline, tmp_path):
    seed = _make_seed(
        tmp_path,
        [
            {
                "protocol_id": "planet_hulk",
                "name": "Planet Hulk",
                "domains": ["leadership"],
                "core_tension": "Exile.",
                "lesson": "L",
                "narrative": "N",
                "beat_structure": ["Exile", "Arena", "Rebellion", "Return", "Blowback"],
            }
        ],
    )
    proto = pipeline.parse_marvel_seed_json(seed)[0]
    assert len(proto.dimensions) == 4  # capped at 4 beats
    assert proto.dimensions[0].id.value == "D1"
    assert proto.dimensions[0].lesson == "L"


def test_seed_empty_beats_gets_core_conflict_dimension(pipeline, tmp_path):
    seed = _make_seed(
        tmp_path,
        [
            {
                "protocol_id": "no_beats",
                "name": "No Beats",
                "domains": ["risk"],
                "core_tension": "Single tension.",
                "lesson": "L",
                "narrative": "N",
            }
        ],
    )
    proto = pipeline.parse_marvel_seed_json(seed)[0]
    assert len(proto.dimensions) == 1
    assert proto.dimensions[0].title == "Core Conflict"
    assert proto.dimensions[0].analysis == "Single tension."


def test_seed_risk_categories_deduplicated(pipeline, tmp_path):
    seed = _make_seed(
        tmp_path,
        [
            {
                "protocol_id": "arc",
                "name": "Arc",
                "domains": ["strategy", "strategy"],
                "core_tension": "T",
                "lesson": "L",
                "narrative": "N",
                "beat_structure": ["A"],
            }
        ],
    )
    proto = pipeline.parse_marvel_seed_json(seed)[0]
    assert len(proto.risk_categories) == 1


# =============================================================================
# _parse_strategy_block (business-book compiler output)
# =============================================================================


def test_parse_strategy_block_full(pipeline):
    block = """* Strategy:
  * Strategy Type: differentiation
  * Moat: proprietary_tech
  * Value Chain Stage: r_and_d
  * Business Model Lever: expansion
  * Target Segment: SaaS founders
  * Strategic Risk: commoditization
  * Key Principle: Own the stack.
  * Strategy Tags: platform, algorithm, scale
"""
    strat = pipeline._parse_strategy_block(block)
    assert strat is not None
    assert strat.strategy_type.value == StrategyType.DIFFERENTIATION.value
    assert strat.moat.value == MoatType.PROPRIETARY_TECH.value
    assert strat.value_chain_stage.value == ValueChainStage.R_D.value
    assert strat.business_model_lever.value == BusinessModelLever.EXPANSION.value
    assert strat.target_segment == "SaaS founders"
    assert strat.strategy_tags == ["platform", "algorithm", "scale"]
    assert strat.confidence == 0.7


def test_parse_strategy_block_empty(pipeline):
    assert pipeline._parse_strategy_block("") is None
    assert pipeline._parse_strategy_block("   \n  ") is None


def test_parse_strategy_block_missing_keys_defaults(pipeline):
    block = "* Strategy:\n  * Strategy Type: focus\n"
    strat = pipeline._parse_strategy_block(block)
    assert strat.strategy_type.value == StrategyType.FOCUS.value
    assert strat.moat.value == MoatType.NONE_NA.value
    assert strat.value_chain_stage.value == ValueChainStage.OPERATIONS.value
    assert strat.business_model_lever.value == BusinessModelLever.MARGIN.value
    assert strat.strategy_tags == []


def test_parse_strategy_block_invalid_enum_defaults(pipeline):
    block = (
        "* Strategy:\n  * Strategy Type: not_a_type\n"
        "  * Moat: nope\n  * Value Chain Stage: x\n  * Business Model Lever: y\n"
    )
    strat = pipeline._parse_strategy_block(block)
    assert strat.strategy_type.value == StrategyType.DIFFERENTIATION.value
    assert strat.moat.value == MoatType.NONE_NA.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])