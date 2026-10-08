"""
TEMPLATE_01: Data Ingestion Module
===================================

Purpose: Parse existing files into structured KnowledgeBase
- Parse 'Storylines for metaphor engine' text file
- Parse IHS_*.csv files for TAP metrics
- Convert to JSONL in processed/ directory
- Generate embeddings for semantic search

CHEETAH IMPLEMENTATION NOTES:
- Read from '../Storylines for metaphor engine' file
- Parse 4 protocols: Armor Wars, Secret Invasion, Days of Future Past, Planet Hulk
- Each protocol has 4 dimensions (D1-D4) with business vectors
- Output to '../processed/' directory
- Create embeddings using sentence-transformers
"""

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import schema from sibling module
from schema import (
    Arc,
    BusinessVector,
    Character,
    Dimension,
    DimensionType,
    FormatType,
    KnowledgeBase,
    Protocol,
    ProtocolType,
    RiskCategory,
    ToneType,
    Trope,
    Universe,
    UniverseType,
)
from sentence_transformers import SentenceTransformer


class DataIngestionPipeline:
    """Main ingestion pipeline for comic metaphor data."""

    def __init__(self, raw_dir: str = ".", processed_dir: str = "./processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(exist_ok=True)

        # Initialize embedding model (lightweight for speed)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def parse_storylines_file(self, filepath: str) -> List[Protocol]:
        """
        Parse the 'Storylines for metaphor engine' text file.

        Expected structure:
        1. The "Armor Wars" Protocol
        2. The "Secret Invasion" Protocol
        3. The "Days of Future Past" Protocol
        4. The "Planet Hulk" Protocol

        Each has:
        - Source Material
        - The Narrative
        - The Business Translation
        - D1-D4 (Bio, Tech, Eco, Cosmic) dimensions
        - Vector Entry (JSON)
        """
        protocols = []

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by protocol headers (1., 2., 3., 4.)
        protocol_blocks = re.split(r'\n\d+\.\s+The\s+"([^"]+)"\s+Protocol', content)

        # protocol_blocks[0] is intro text, then alternates name, content
        for i in range(1, len(protocol_blocks), 2):
            if i + 1 >= len(protocol_blocks):
                break

            protocol_name = protocol_blocks[i]
            protocol_content = protocol_blocks[i + 1]

            protocol = self._parse_protocol_block(protocol_name, protocol_content)
            if protocol:
                protocols.append(protocol)

        return protocols

    def _parse_protocol_block(self, name: str, content: str) -> Optional[Protocol]:
        """Parse a single protocol block."""
        # Extract sections
        source_match = re.search(r"Source Material:\s*(.+?)(?=\n)", content)
        narrative_match = re.search(
            r"The Narrative:\s*(.+?)(?=The Business Translation:)", content, re.DOTALL
        )
        business_match = re.search(
            r"The Business Translation:\s*(.+?)(?=\* D1)", content, re.DOTALL
        )
        vector_match = re.search(
            r"Vector Entry \(JSON\):\s*```?\s*({.+?})\s*```?", content, re.DOTALL
        )

        # Parse dimensions D1-D4
        dimensions = []
        for dim_num in range(1, 5):
            dim_pattern = rf"\* D{dim_num} \(([^)]+)\):\s+\* Logic:\s*(.+?)\s+\* Metric:\s*(.+?)(?=\n\s*\* D{dim_num + 1}|\n\s*Vector Entry|\Z)"
            dim_match = re.search(dim_pattern, content, re.DOTALL)

            if dim_match:
                dim_type = dim_match.group(1).strip()
                logic = dim_match.group(2).strip()
                metric = dim_match.group(3).strip()

                dimension = Dimension(
                    id=DimensionType(f"D{dim_num}"),
                    title=dim_type,
                    science_concept=self._extract_science_concept(dim_type),
                    character_anchor=self._get_character_anchor(name, dim_num),
                    analysis=logic,
                    lesson=self._extract_lesson(logic),
                    metric=metric,
                )
                dimensions.append(dimension)

                # Create business vector from dimension
                # (In real implementation, extract more details)

        # Map protocol name to type
        protocol_type_map = {
            "Armor Wars": ProtocolType.ARMOR_WARS,
            "Secret Invasion": ProtocolType.SECRET_INVASION,
            "Days of Future Past": ProtocolType.DAYS_OF_FUTURE_PAST,
            "Planet Hulk": ProtocolType.PLANET_HULK,
        }

        protocol_type = protocol_type_map.get(name, ProtocolType.CUSTOM)

        # Map to risk categories
        risk_map = {
            "Armor Wars": [RiskCategory.OWNERSHIP],
            "Secret Invasion": [RiskCategory.IDENTITY],
            "Days of Future Past": [RiskCategory.CONTROL],
            "Planet Hulk": [RiskCategory.AVOIDANCE],
        }

        # Extract vector entry JSON
        vector_entry = {}
        if vector_match:
            try:
                vector_entry = json.loads(vector_match.group(1))
            except json.JSONDecodeError:
                vector_entry = {
                    "id": f"protocol_{name.lower().replace(' ', '_')}",
                    "archetype": f"{name} Pattern",
                    "business_logic": business_match.group(1).strip()
                    if business_match
                    else "",
                    "application": "Strategic analysis",
                }

        protocol = Protocol(
            id=f"protocol_{name.lower().replace(' ', '_')}",
            protocol_type=protocol_type,
            archetype=vector_entry.get("archetype", f"{name} Pattern"),
            business_logic=vector_entry.get("business_logic", ""),
            application=vector_entry.get("application", ""),
            narrative=narrative_match.group(1).strip() if narrative_match else "",
            business_translation=business_match.group(1).strip()
            if business_match
            else "",
            dimensions=dimensions,
            vector_entry=vector_entry,
            risk_categories=risk_map.get(name, []),
            themes=self._extract_themes(name),
            tone_compatibility=self._get_tone_compatibility(name),
            format_compatibility=[
                FormatType.PODCAST_MONOLOGUE,
                FormatType.MARKETING_EMAIL,
                FormatType.BLOG_POST,
            ],
        )

        return protocol

    def _extract_science_concept(self, dim_type: str) -> str:
        """Map dimension type to science concept."""
        mapping = {
            "Bio/Internal": "Evolutionary Mismatch",
            "Tech/External": "The Alignment Problem",
            "Eco/Resources": "Carrying Capacity",
            "Cosmic/Limit": "Entropy & Decay",
        }
        return mapping.get(dim_type, "Unknown")

    def _get_character_anchor(self, protocol_name: str, dim_num: int) -> str:
        """Get character anchor for dimension."""
        # Simplified mapping
        anchors = {
            ("Armor Wars", 1): "Iron Man vs. Guilt",
            ("Armor Wars", 2): "Tech Proliferation",
            ("Secret Invasion", 1): "Trust Breakdown",
            ("Secret Invasion", 2): "Identity Verification",
            ("Days of Future Past", 1): "Sentinel Control",
            ("Days of Future Past", 2): "AI Optimization",
            ("Planet Hulk", 1): "Exile and Return",
            ("Planet Hulk", 2): "Externalization Failure",
        }
        return anchors.get((protocol_name, dim_num), f"{protocol_name} D{dim_num}")

    def _extract_lesson(self, logic: str) -> str:
        """Extract lesson from logic text."""
        # Take first sentence or first 100 chars
        sentences = logic.split(".")
        return sentences[0].strip() + "." if sentences else logic[:100]

    def _extract_themes(self, protocol_name: str) -> List[str]:
        """Extract themes from protocol name."""
        theme_map = {
            "Armor Wars": ["ownership", "responsibility", "consequences", "control"],
            "Secret Invasion": ["trust", "identity", "paranoia", "infiltration"],
            "Days of Future Past": [
                "control",
                "optimization",
                "freedom",
                "determinism",
            ],
            "Planet Hulk": ["avoidance", "externalization", "return", "blowback"],
        }
        return theme_map.get(protocol_name, ["transformation"])

    def _get_tone_compatibility(self, protocol_name: str) -> List[ToneType]:
        """Get compatible tones for protocol."""
        tone_map = {
            "Armor Wars": [ToneType.GRITTY, ToneType.CAUTIONARY],
            "Secret Invasion": [ToneType.DARK, ToneType.CAUTIONARY],
            "Days of Future Past": [ToneType.PHILOSOPHICAL, ToneType.CAUTIONARY],
            "Planet Hulk": [ToneType.ACTION, ToneType.CAUTIONARY],
        }
        return tone_map.get(protocol_name, [ToneType.HOPEFUL])

    def parse_ihs_csv(self, filepath: str) -> Dict[str, Any]:
        """
        Parse IHS CSV files for TAP metrics and scoring frameworks.

        Expected files:
        - IHS_Unified_Flow.csv
        - IHS_System_Foundations.json (already JSON)
        - IHS_Execution_Tools.json (already JSON)
        """
        if filepath.endswith(".json"):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)

        # Parse CSV
        df = pd.read_csv(filepath)

        # Convert to dict structure
        data = {
            "columns": df.columns.tolist(),
            "rows": df.to_dict("records"),
            "metadata": {"row_count": len(df), "column_count": len(df.columns)},
        }

        return data

    def build_knowledge_base(self) -> KnowledgeBase:
        """
        Build complete knowledge base from all raw files.

        Returns:
            KnowledgeBase with protocols, universes, etc.
        """
        kb = KnowledgeBase()

        # Parse storylines file
        storylines_path = self.raw_dir / "Storylines for metaphor engine"
        if storylines_path.exists():
            protocols = self.parse_storylines_file(str(storylines_path))
            for protocol in protocols:
                kb.protocols[protocol.id] = protocol

        # Create a default Marvel universe
        marvel_universe = Universe(
            id="universe_marvel",
            name="Marvel Universe",
            universe_type=UniverseType.SUPERHERO,
            description="Primary superhero universe for metaphor protocols",
            themes=["responsibility", "power", "sacrifice", "redemption"],
            visual_motifs=["heroic imagery", "transformation", "conflict"],
            moral_framework="With great power comes great responsibility",
            tone=ToneType.HOPEFUL,
            protocol_ids=[p.id for p in protocols],
            is_public_domain=False,
            requires_abstraction=True,
        )
        kb.universes[marvel_universe.id] = marvel_universe

        # Parse IHS system files for TAP integration
        ihs_files = [
            "IHS_System_Foundations.json",
            "IHS_Execution_Tools.json",
            "IHS_Unified_Flow.csv",
        ]

        kb_metadata = {}
        for filename in ihs_files:
            filepath = self.raw_dir / filename
            if filepath.exists():
                try:
                    data = self.parse_ihs_csv(str(filepath))
                    kb_metadata[filename] = data
                except Exception as e:
                    print(f"Warning: Could not parse {filename}: {e}")

        # Store TAP configuration in KB metadata (not in schema but useful)
        # This would be used by codex_adapter later

        return kb

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for text using sentence-transformers.

        Args:
            texts: List of text strings to embed

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings

    def save_processed_data(self, kb: KnowledgeBase) -> None:
        """
        Save processed knowledge base to disk.

        Outputs:
            - processed/knowledge_base.json (full KB)
            - processed/protocols.jsonl (one per line)
            - processed/universes.jsonl
            - processed/embeddings.npy (protocol embeddings)
        """
        # Save full knowledge base
        kb_path = self.processed_dir / "knowledge_base.json"
        kb.save(str(kb_path))
        print(f"✓ Saved knowledge base to {kb_path}")

        # Save protocols as JSONL
        protocols_path = self.processed_dir / "protocols.jsonl"
        with open(protocols_path, "w", encoding="utf-8") as f:
            for protocol in kb.protocols.values():
                f.write(json.dumps(protocol.to_dict()) + "\n")
        print(f"✓ Saved {len(kb.protocols)} protocols to {protocols_path}")

        # Save universes as JSONL
        universes_path = self.processed_dir / "universes.jsonl"
        with open(universes_path, "w", encoding="utf-8") as f:
            for universe in kb.universes.values():
                f.write(json.dumps(universe.to_dict()) + "\n")
        print(f"✓ Saved {len(kb.universes)} universes to {universes_path}")

        # Generate and save embeddings for protocols
        protocol_texts = []
        for protocol in kb.protocols.values():
            # Combine key fields for embedding
            text = (
                f"{protocol.archetype} {protocol.business_logic} {protocol.narrative}"
            )
            protocol_texts.append(text)

        if protocol_texts:
            embeddings = self.generate_embeddings(protocol_texts)
            embeddings_path = self.processed_dir / "embeddings.npy"
            np.save(embeddings_path, embeddings)
            print(f"✓ Saved {embeddings.shape[0]} embeddings to {embeddings_path}")

        # Save metadata
        metadata = {
            "version": kb.version,
            "last_updated": kb.last_updated.isoformat(),
            "stats": kb.get_stats(),
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dim": embeddings.shape[1] if protocol_texts else 0,
        }
        metadata_path = self.processed_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Saved metadata to {metadata_path}")


def main():
    """Main ingestion pipeline entry point."""
    print("=" * 60)
    print("Comic Book Metaphor Engine - Data Ingestion Pipeline")
    print("=" * 60)

    # Initialize pipeline
    pipeline = DataIngestionPipeline(raw_dir=".", processed_dir="./processed")

    # Build knowledge base
    print("\n📚 Building knowledge base...")
    kb = pipeline.build_knowledge_base()

    # Print stats
    stats = kb.get_stats()
    print(f"\n✓ Knowledge Base built successfully:")
    print(f"  - Universes: {stats['universes']}")
    print(f"  - Protocols: {stats['protocols']}")
    print(f"  - Characters: {stats['characters']}")
    print(f"  - Arcs: {stats['arcs']}")
    print(f"  - Tropes: {stats['tropes']}")

    # Save processed data
    print("\n💾 Saving processed data...")
    pipeline.save_processed_data(kb)

    print("\n✅ Ingestion complete!")
    print(f"   Output directory: {pipeline.processed_dir}")

    return kb


if __name__ == "__main__":
    kb = main()
