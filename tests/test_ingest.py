import json
from pathlib import Path

import pytest


def test_knowledge_base_loads(knowledge_base):
    """Test that knowledge base loads successfully"""
    assert knowledge_base is not None
    assert len(knowledge_base.protocols) > 0


def test_knowledge_base_has_protocols(knowledge_base):
    """Test knowledge base contains the full parsed protocol corpus"""
    assert len(knowledge_base.protocols) >= 55


def test_embeddings_exist():
    """Test that embeddings were generated and cover all protocols"""
    import numpy as np

    embeddings_path = Path("processed/embeddings.npy")
    assert embeddings_path.exists()
    embeddings = np.load(str(embeddings_path))
    assert embeddings.shape[0] >= 55
    assert embeddings.shape[1] == 384


def test_faiss_index_persisted():
    """Test that the FAISS index was saved to disk"""
    assert Path("processed/index.faiss").exists()


def test_metadata_complete():
    """Test that metadata was generated"""
    metadata_path = Path("processed/metadata.json")
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert isinstance(metadata, dict)


def test_protocol_parser_roundtrip():
    """Test the full text->protocol pipeline"""
    from engine.protocol_parser import ProtocolParser

    parser = ProtocolParser()
    protocols = parser.parse_all_files()
    assert len(protocols) >= 55
    for protocol in protocols[:5]:
        assert len(protocol.dimensions) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
