import pytest

from engine.schema import FormatType, ToneType


def test_engine_loads(engine):
    """Test that engine loads successfully"""
    assert engine is not None


def test_engine_generates_mappings(engine):
    """Test engine can generate mappings"""
    mapping = engine.generate_mapping(
        topic="startup burnout",
        target_format=FormatType.PODCAST_MONOLOGUE,
        target_tone=ToneType.HOPEFUL,
    )
    assert mapping is not None
    assert mapping.topic == "startup burnout"
    assert mapping.protocol_id.startswith("protocol_")


def test_engine_mapping_quality(engine):
    """Test engine generates quality mappings"""
    mapping = engine.generate_mapping(
        topic="technical debt",
        target_format=FormatType.BLOG_POST,
        target_tone=ToneType.CAUTIONARY,
    )
    # Codex scoring runs through the adapter and populates scores.
    assert mapping.trueness_score >= 0.0
    assert mapping.trueness_score <= 1.0
    assert mapping.core_tension  # The engine always derives a core tension
    assert mapping.mappings  # At least one mapping element


def test_engine_honors_format(engine):
    """Test the mapping reflects the requested format/tone"""
    mapping = engine.generate_mapping(
        topic="leadership crisis",
        target_format=FormatType.DIALOGUE_SCRIPT,
        target_tone=ToneType.GRITTY,
    )
    assert mapping.target_format == FormatType.DIALOGUE_SCRIPT
    assert mapping.target_tone == ToneType.GRITTY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
