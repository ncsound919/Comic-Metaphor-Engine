import pytest

from engine.schema import FormatType, ToneType


def test_end_to_end_pipeline(engine, index):
    """Test complete pipeline from query to mapping"""
    mapping = engine.generate_mapping(
        topic="startup scaling",
        target_format=FormatType.PODCAST_MONOLOGUE,
        target_tone=ToneType.HOPEFUL,
    )
    assert mapping is not None
    protocol = index.get_protocol_by_id(mapping.protocol_id)
    assert protocol is not None
    assert mapping.trueness_score > 0.0


def test_all_modules_import():
    """Test that all modules can be imported"""
    from engine import schema
    from engine import ingest
    from engine import index
    from engine import metaphor_engine
    from engine import narrative_generator
    from engine import explainers
    from engine import codex_adapter

    assert True


def test_knowledge_base_to_search(knowledge_base, index):
    """Test knowledge base to search pipeline"""
    results = index.search_protocols("burnout", top_k=3, return_scores=True)
    kb_ids = set(knowledge_base.protocols.keys())
    for protocol, _ in results:
        assert protocol.id in kb_ids


def test_mapping_to_narrative(engine, index):
    """Test search -> mapping -> narrative pipeline"""
    mapping = engine.generate_mapping(
        topic="leadership crisis",
        target_format=FormatType.PODCAST_MONOLOGUE,
        target_tone=ToneType.GRITTY,
    )
    protocol = index.get_protocol_by_id(mapping.protocol_id)
    from engine.narrative_generator import NarrativeGenerator

    ctx = __import__("engine.schema", fromlist=["GenerationContext"]).GenerationContext(
        mapping=mapping, protocol=protocol, word_count_target=600
    )
    output = NarrativeGenerator().generate(ctx)
    assert output.title
    assert output.word_count > 0
    assert "Story" in output.title


def test_lesson_generation(engine, index):
    """Test the learning module produces a usable lesson"""
    from engine.explainers import generate_lesson

    mapping = engine.generate_mapping(
        topic="impostor syndrome in founders",
        target_format=FormatType.BLOG_POST,
        target_tone=ToneType.INSPIRATIONAL,
    )
    protocol = index.get_protocol_by_id(mapping.protocol_id)
    lesson = generate_lesson(mapping, protocol)
    assert lesson["lesson_id"].startswith("lesson_")
    assert len(lesson["takeaways"]) > 0
    assert len(lesson["actions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
