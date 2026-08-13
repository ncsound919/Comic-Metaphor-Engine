import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import faiss
import numpy as np
from schema import KnowledgeBase, Protocol

# Lazy, process-wide singleton embedding model. Loading sentence-transformers
# takes ~90s, so we load it at most once and share it across every index,
# adapter, and API request.
_EMBEDDING_MODEL = None
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def get_embedding_model():
    """Return the shared SentenceTransformer model, loading it on first use."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer

        _EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _EMBEDDING_MODEL


class MetaphorIndex:
    def __init__(self, processed_dir: str = "./processed", lazy: bool = False):
        self.processed_dir = Path(processed_dir)
        self.protocols: Dict[str, Protocol] = {}
        self.protocol_list: List[Protocol] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index: Optional[faiss.Index] = None
        # Model is loaded lazily on first encode so constructing an index
        # (and every component that owns one) is fast.
        self.embedding_model = None if lazy else get_embedding_model()

        # Cache for search results
        self.search_cache = {}
        self.cache_hits = 0
        self.total_searches = 0

        # Load existing data
        self._load_data()
        self._build_faiss_index()

    def _load_data(self) -> None:
        """Load protocols, embeddings, and FAISS index from processed directory."""
        # Load protocols
        protocols_path = self.processed_dir / "protocols.json"
        if protocols_path.exists():
            with open(protocols_path, "r", encoding="utf-8") as f:
                protocols_data = json.load(f)
            for pid, p_data in protocols_data.items():
                protocol = Protocol.from_dict(p_data)
                self.protocols[pid] = protocol
                self.protocol_list.append(protocol)
        else:
            print(f"Warning: {protocols_path} not found. Index will be empty.")

        # Load embeddings
        embeddings_path = self.processed_dir / "embeddings.npy"
        if embeddings_path.exists():
            self.embeddings = np.load(embeddings_path)
            print(f"Loaded embeddings: {self.embeddings.shape}")
        else:
            print(
                f"Warning: {embeddings_path} not found. Cannot perform similarity search."
            )

        # Load FAISS index if available
        index_path = self.processed_dir / "index.faiss"
        if index_path.exists() and self.embeddings is not None:
            self.index = faiss.read_index(str(index_path))
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
        else:
            self._build_faiss_index()

    def _build_faiss_index(self) -> None:
        """Build FAISS index from embeddings."""
        if self.embeddings is not None and len(self.embeddings) > 0:
            dim = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)  # Inner product for cosine similarity
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(self.embeddings)
            self.index.add(self.embeddings)
            print(f"Built FAISS index with {self.index.ntotal} vectors")
        else:
            print("No embeddings available, FAISS index not built.")

    def _embed(self, texts, show_progress_bar: bool = False):
        if self.embedding_model is None:
            self.embedding_model = get_embedding_model()
        return self.embedding_model.encode(texts, show_progress_bar=show_progress_bar)

    def build_index(self, kb: KnowledgeBase) -> None:
        """Build index from KnowledgeBase (alternative to loading from disk)."""
        self.protocols = kb.protocols.copy()
        self.protocol_list = list(self.protocols.values())

        # Generate embeddings if not loaded or if the count no longer matches
        # the protocol list (e.g. a stale index on disk from an older build).
        if self.embeddings is None or len(self.embeddings) != len(self.protocol_list):
            # Dense, topic-focused text (not the long narrative) gives better
            # retrieval signal for short user queries.
            protocol_texts = [
                f"{p.archetype} {p.business_logic} {p.business_translation} "
                f"{' '.join(p.themes)} {p.application}"
                for p in self.protocol_list
            ]
            self.embeddings = self._embed(
                protocol_texts, show_progress_bar=True
            )
            self._build_faiss_index()

        print(f"Built index with {len(self.protocols)} protocols")

    def search_protocols(
        self,
        query: str,
        filters: Optional[Dict] = None,
        top_k: int = 5,
        return_scores: bool = False,
    ) -> Union[List[Protocol], List[Tuple[Protocol, float]]]:
        """Search protocols using FAISS similarity search."""

        self.total_searches += 1

        # Create cache key
        cache_key = (query, str(filters) if filters else None, top_k, return_scores)

        if cache_key in self.search_cache:
            self.cache_hits += 1
            return self.search_cache[cache_key]

        if self.index is None or self.embeddings is None:
            print("FAISS index not available, falling back to keyword search.")
            results = self._keyword_search(query, top_k, return_scores=return_scores)
            self.search_cache[cache_key] = results
            return results

        # Encode query
        query_embedding = self._embed([query])
        faiss.normalize_L2(query_embedding)

        # Search
        distances, indices = self.index.search(query_embedding, top_k)

        results: List[Union[Protocol, Tuple[Protocol, float]]] = []

        scores = distances[0]
        for position, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.protocol_list):
                protocol = self.protocol_list[idx]

                # Apply filters if any (placeholder for future)

                if filters:
                    # Implement filter logic here

                    pass

                similarity = float(scores[position])
                results.append((protocol, similarity) if return_scores else protocol)

        self.search_cache[cache_key] = results
        return results

    def compute_similarity(self, query: str, protocol: Protocol) -> float:
        """Compute semantic similarity between query and protocol."""
        if self.embeddings is None or protocol not in self.protocol_list:
            return 0.0
        idx = self.protocol_list.index(protocol)
        query_emb = self._embed([query])
        faiss.normalize_L2(query_emb)
        similarity = np.dot(query_emb[0], self.embeddings[idx])
        return float(similarity)

    def _keyword_search(
        self, query: str, top_k: int = 5, return_scores: bool = False
    ) -> Union[List[Protocol], List[Tuple[Protocol, float]]]:
        """Fallback keyword search."""

        results: List[Union[Protocol, Tuple[Protocol, float]]] = []

        query_lower = query.lower()

        for protocol in self.protocols.values():
            if (
                query_lower in protocol.business_logic.lower()
                or query_lower in protocol.narrative.lower()
            ):
                entry = (protocol, 1.0) if return_scores else protocol
                results.append(entry)
                if len(results) >= top_k:
                    break

        return results

    def get_protocol_by_id(self, protocol_id: str) -> Optional[Protocol]:
        return self.protocols.get(protocol_id)

    def get_cache_stats(self) -> Dict[str, float]:
        """Get cache hit statistics."""
        hit_rate = (
            self.cache_hits / self.total_searches if self.total_searches > 0 else 0.0
        )
        return {
            "cache_hit_rate": hit_rate,
            "cache_hits": self.cache_hits,
            "total_searches": self.total_searches,
        }

    def save(self, directory: str) -> None:
        """Save index data to directory."""
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)

        # Save protocols
        protocols_data = {pid: p.to_dict() for pid, p in self.protocols.items()}
        with open(dir_path / "protocols.json", "w", encoding="utf-8") as f:
            json.dump(protocols_data, f, indent=2)

        # Save embeddings if available
        if self.embeddings is not None:
            np.save(dir_path / "embeddings.npy", self.embeddings)

        # Save FAISS index if available
        if self.index is not None:
            faiss.write_index(self.index, str(dir_path / "index.faiss"))

        print(f"Saved index to {directory}")


def build_index(
    kb: Optional[KnowledgeBase] = None, processed_dir: str = "./processed"
) -> MetaphorIndex:
    """Factory function to build or load index."""
    index = MetaphorIndex(processed_dir)
    if kb:
        index.build_index(kb)
    return index


if __name__ == "__main__":
    # Test the index
    index = build_index()
    results = index.search_protocols("burnout", top_k=3)
    print(f"Found {len(results)} protocols for 'burnout'")
    for r in results:
        print(f"- {r.id}: {r.archetype}")
    index.save("processed")
