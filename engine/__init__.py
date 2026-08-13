"""
Comic Book Metaphor Engine
==========================

A system for mapping comic book storylines to real-world concepts
for use in podcasts, marketing, dialogue coaching, and life advice.

Modules:
    - schema: Data models for universes, characters, arcs, protocols, and mappings
    - ingest: Data ingestion and parsing pipelines
    - index: Search and retrieval over the metaphor knowledge base
    - metaphor_engine: Core mapping logic from topics to comic metaphors
    - narrative_generator: Outline, script, and content generation
    - explainers: Plain-language explanations of metaphor mappings
    - tools_interface: Cheetah v3 tool wrappers for benchmarking
    - codex_adapter: Integration with codex_engine scoring system
"""

from .schema import (
    Arc,
    BenchmarkResult,
    BusinessVector,
    Character,
    Dimension,
    GenerationContext,
    MetaphorMapping,
    NarrativeOutput,
    Protocol,
    Trope,
    Universe,
)

__version__ = "0.1.0"
__author__ = "Book Writing Assistant"

__all__ = [
    # Core data models
    "Universe",
    "Character",
    "Arc",
    "Protocol",
    "Trope",
    "BusinessVector",
    "MetaphorMapping",
    "Dimension",
    "NarrativeOutput",
    "GenerationContext",
    "BenchmarkResult",
    # Version info
    "__version__",
    "__author__",
]
