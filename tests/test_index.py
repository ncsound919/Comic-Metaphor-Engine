import pytest

from engine.schema import FormatType, ToneType


def test_index_loads(index):
    """Test that index loads successfully"""
    assert index is not None
    assert index.index is not None
    assert index.index.ntotal > 0


def test_index_has_vectors(index):
    """Test index contains vectors"""
    assert index.embeddings is not None
    assert len(index.embeddings) == len(index.protocol_list)


def test_search_works(index):
    """Test that search returns results"""
    results = index.search_protocols("burnout", top_k=3, return_scores=True)
    assert len(results) > 0
    protocol, score = results[0]
    assert protocol.id.startswith("protocol_")
    assert score >= 0


def test_search_scoring(index):
    """Test that search returns scored results"""
    results = index.search_protocols("technical debt", top_k=3, return_scores=True)
    for protocol, score in results:
        assert score >= 0.0
        assert score <= 1.0


def test_get_protocol_by_id(index):
    """Test protocol lookup by id"""
    protocol_id = index.protocol_list[0].id
    protocol = index.get_protocol_by_id(protocol_id)
    assert protocol is not None
    assert protocol.id == protocol_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
