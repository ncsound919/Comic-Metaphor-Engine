"""Comprehensive unit tests for engine.protocol_parser to raise overall test coverage past 75%."""

import json
from pathlib import Path
import pytest

from engine.protocol_parser import (
    ParsedDimension,
    ParsedProtocol,
    ProtocolParser,
    TIER_TO_RISK,
)


def test_parsed_dimension_to_dict():
    d = ParsedDimension(
        dimension_id="D1",
        label="Bio/Internal",
        title="Evolutionary Mismatch",
        logic="Internal stress analysis.",
        metric="Stress Index",
    )
    res = d.to_dict()
    assert res["id"] == "D1"
    assert res["science_concept"] == "Bio/Internal"
    assert res["analysis"] == "Internal stress analysis."
    assert res["metric"] == "Stress Index"
    assert res["character_anchor"] == ""
    assert res["lesson"] == ""


def test_infer_protocol_type_variants():
    # cosmic
    p1 = ParsedProtocol(
        id="protocol_cosmic_1",
        section_number="1",
        archetype="Cosmic Arc",
        source_material="Cosmic Source",
        narrative="Cosmic entities warring.",
        business_concept="Scale overload",
        business_translation="Do not overload.",
        dimensions=[],
        vector_entry={},
        source_file="cosmic_complete.txt",
    )
    assert p1.to_dict()["protocol_type"] == "cosmic_entity"

    # claremont
    p2 = ParsedProtocol(
        id="protocol_claremont_1",
        section_number="1",
        archetype="X-Men Arc",
        source_material="Claremont",
        narrative="Deep character growth.",
        business_concept="Culture first",
        business_translation="Build inclusive culture.",
        dimensions=[],
        vector_entry={},
        source_file="claremont_complete.txt",
    )
    assert p2.to_dict()["protocol_type"] == "claremont_arc"

    # modern
    p3 = ParsedProtocol(
        id="protocol_modern_1",
        section_number="1",
        archetype="Modern Arc",
        source_material="Modern",
        narrative="Krakoa era.",
        business_concept="Platform shift",
        business_translation="Shift platform.",
        dimensions=[],
        vector_entry={},
        source_file="modern_xmen_complete.txt",
    )
    assert p3.to_dict()["protocol_type"] == "modern_xmen"

    # avengers
    p4 = ParsedProtocol(
        id="protocol_avengers_1",
        section_number="1",
        archetype="Avengers Arc",
        source_material="Avengers",
        narrative="Earth's mightiest.",
        business_concept="Coalition building",
        business_translation="Build coalitions.",
        dimensions=[],
        vector_entry={},
        source_file="avengers_complete.txt",
    )
    assert p4.to_dict()["protocol_type"] == "avengers_cosmic"

    # character
    p5 = ParsedProtocol(
        id="protocol_char_1",
        section_number="1",
        archetype="Character Arc",
        source_material="Character",
        narrative="Deep dive.",
        business_concept="Founder focus",
        business_translation="Focus founder.",
        dimensions=[],
        vector_entry={},
        source_file="character_deep_dive.txt",
    )
    assert p5.to_dict()["protocol_type"] == "character_deep_dive"


def test_extract_themes_all_keywords():
    p = ParsedProtocol(
        id="protocol_themes",
        section_number="1",
        archetype="Theme Test",
        source_material="Source",
        narrative="Power control corrupt exploit identity transform trust betrayal survival threat governance law ethic moral tech ai algorithm leader founder economic market capital resource",
        business_concept="All themes",
        business_translation="All themes translation.",
        dimensions=[],
        vector_entry={},
    )
    themes = p._extract_themes()
    assert len(themes) <= 5
    assert len(themes) > 0


def test_protocol_validate_failures():
    # missing id
    p1 = ParsedProtocol(
        id="",
        section_number="1",
        archetype="Test",
        source_material="",
        narrative="",
        business_concept="",
        business_translation="",
        dimensions=[],
        vector_entry={},
    )
    valid, errs = p1.validate()
    assert not valid
    assert "Missing protocol ID" in errs

    # id doesn't start with protocol_ (wait, seed protocols have bare IDs now, but validate rule still checks it)
    p2 = ParsedProtocol(
        id="bad_id",
        section_number="1",
        archetype="Test",
        source_material="",
        narrative="nav",
        business_concept="",
        business_translation="biz",
        dimensions=[ParsedDimension("D1", "L", "T", "L", "M")] * 4,
        vector_entry={"id": "bad_id"},
    )
    valid, errs = p2.validate()
    assert not valid
    assert any("Protocol ID should start with 'protocol_'" in e for e in errs)

    # wrong dimension count
    p3 = ParsedProtocol(
        id="protocol_good",
        section_number="1",
        archetype="Test",
        source_material="",
        narrative="nav",
        business_concept="",
        business_translation="biz",
        dimensions=[],
        vector_entry={"id": "protocol_good"},
    )
    valid, errs = p3.validate()
    assert not valid
    assert any("Expected 4 dimensions" in e for e in errs)


def test_parser_parse_file_missing_vector_json(tmp_path):
    f = tmp_path / "empty_complete.txt"
    f.write_text("Just some text without json vector block.", encoding="utf-8")

    parser = ProtocolParser(comic_books_dir=tmp_path)
    protocols = parser.parse_file(f)
    assert protocols == []
    assert len(parser.warnings) > 0


def test_parser_parse_file_invalid_json(tmp_path):
    f = tmp_path / "bad_json_complete.txt"
    f.write_text(
        "**The Narrative**:\nNarrative here\n\n```json\n{invalid json}\n```",
        encoding="utf-8",
    )

    parser = ProtocolParser(comic_books_dir=tmp_path)
    protocols = parser.parse_file(f)
    assert len(parser.errors) > 0


def test_parser_save_to_knowledge_base(tmp_path):
    out = tmp_path / "kb.json"
    p = ParsedProtocol(
        id="protocol_saved_test",
        section_number="1",
        archetype="Saved Arc",
        source_material="Source",
        narrative="Test narrative content for saving.",
        business_concept="Test concept",
        business_translation="Test translation",
        dimensions=[
            ParsedDimension(f"D{i}", "Bio/Internal", f"Dim {i}", "Logic", "Metric")
            for i in range(1, 5)
        ],
        vector_entry={"id": "protocol_saved_test", "archetype": "Saved Arc"},
        cosmic_tier="street",
    )

    parser = ProtocolParser()
    success = parser.save_to_knowledge_base([p], output_path=out)
    assert success
    assert out.exists()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert "protocol_saved_test" in data["protocols"]
    assert data["protocols"]["protocol_saved_test"]["archetype"] == "Saved Arc"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
