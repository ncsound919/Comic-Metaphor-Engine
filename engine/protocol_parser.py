#!/usr/bin/env python3
"""
Protocol Parser - Extracts structured protocol data from .txt content files.

This module bridges the gap between human-readable .txt protocol files
and the structured knowledge_base.json used by the metaphor engine.

Features:
- Parses comic_books/*.txt files
- Extracts protocols with full 4-dimension data
- Validates JSON vector entries
- Generates Protocol objects compatible with engine/schema.py
- Outputs to processed/knowledge_base.json

Usage:
    from engine.protocol_parser import ProtocolParser

    parser = ProtocolParser()
    protocols = parser.parse_all_files()
    parser.save_to_knowledge_base(protocols)

    # Or from command line:
    python -m engine.protocol_parser --validate
    python -m engine.protocol_parser --parse --output processed/knowledge_base.json
"""

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from engine.schema import (
        Dimension,
        DimensionType,
        FormatType,
        KnowledgeBase,
        Protocol,
        RiskCategory,
        ToneType,
    )

    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    print("Warning: schema module not available, using dict-based output")


# =============================================================================
# CONFIGURATION
# =============================================================================

COMIC_BOOKS_DIR = Path(__file__).parent.parent / "comic_books"
PROCESSED_DIR = Path(__file__).parent.parent / "processed"
KNOWLEDGE_BASE_PATH = PROCESSED_DIR / "knowledge_base.json"

# Regex patterns for parsing
PATTERNS = {
    # Match protocol headers like "### 1.1 Uatu's Paradox: The Observer Effect"
    "protocol_header": re.compile(
        r"^###?\s+(\d+\.?\d*)\s+(.+?):\s*(.+)$", re.MULTILINE
    ),
    # Match source material line
    "source_material": re.compile(
        r"\*\*Source Material\*\*:\s*(.+?)(?:\n|$)", re.IGNORECASE
    ),
    # Match narrative section
    "narrative": re.compile(
        r"\*\*The Narrative\*\*:\s*\n([\s\S]+?)(?=\n\*\*The Business Translation\*\*|\n\*\*Dimensions\*\*|\n\*\*Vector Entry\*\*)",
        re.IGNORECASE,
    ),
    # Match business translation section
    "business_translation": re.compile(
        r"\*\*The Business Translation\*\*:\s*(.+?)\n([\s\S]+?)(?=\n\*\*Dimensions\*\*|\n\*\*Vector Entry\*\*)",
        re.IGNORECASE,
    ),
    # Match dimension blocks
    "dimension": re.compile(
        r"\*\s*D(\d)\s*\(([^)]+)\):\s*([^\n]+)\n\s*\*\s*Logic:\s*([^\n]+)\n\s*\*\s*Metric:\s*([^\n]+)",
        re.IGNORECASE,
    ),
    # Match JSON vector entry
    "vector_json": re.compile(r"```json\s*\n(\{[\s\S]+?\})\s*\n```", re.MULTILINE),
    # Match protocol ID in JSON
    "protocol_id": re.compile(r'"id":\s*"(protocol_[^"]+)"'),
}

# Dimension type mapping
DIMENSION_MAP = {
    "1": DimensionType.D1_BIO if SCHEMA_AVAILABLE else "D1",
    "2": DimensionType.D2_TECH if SCHEMA_AVAILABLE else "D2",
    "3": DimensionType.D3_ECO if SCHEMA_AVAILABLE else "D3",
    "4": DimensionType.D4_COSMIC if SCHEMA_AVAILABLE else "D4",
}

# Cosmic tier to risk category mapping
TIER_TO_RISK = {
    "street": "ownership",
    "planetary": "control",
    "cosmic": "identity",
    "universal": "avoidance",
    "multiversal": "avoidance",
}


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ParsedDimension:
    """Parsed dimension data from text file."""

    dimension_id: str  # D1, D2, D3, D4
    label: str  # Bio/Internal, Tech/External, etc.
    title: str  # The dimension title
    logic: str  # The logic explanation
    metric: str  # The measurement metric

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.dimension_id,
            "title": self.title,
            "science_concept": self.label,
            "character_anchor": "",  # Will be extracted if present
            "analysis": self.logic,
            "lesson": "",  # Could be extracted from broader context
            "metric": self.metric,
        }


@dataclass
class ParsedProtocol:
    """Parsed protocol data from text file."""

    id: str
    section_number: str
    archetype: str
    source_material: str
    narrative: str
    business_concept: str
    business_translation: str
    dimensions: List[ParsedDimension]
    vector_entry: Dict[str, Any]
    cosmic_tier: str = "planetary"
    themes: List[str] = field(default_factory=list)
    key_characters: List[str] = field(default_factory=list)
    related_protocols: List[str] = field(default_factory=list)

    # Source file for debugging
    source_file: str = ""
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "protocol_type": self._infer_protocol_type(),
            "archetype": self.archetype,
            "business_logic": self.business_concept,
            "application": self.vector_entry.get("application", ""),
            "narrative": self.narrative,
            "business_translation": self.business_translation,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "vector_entry": self.vector_entry,
            "risk_categories": [TIER_TO_RISK.get(self.cosmic_tier, "ownership")],
            "themes": self.themes or self._extract_themes(),
            "tone_compatibility": ["philosophical", "cautionary"],
            "format_compatibility": [
                "podcast_monologue",
                "marketing_email",
                "blog_post",
            ],
            "source_material": self.source_material,
            "cosmic_tier": self.cosmic_tier,
            "key_characters": self.key_characters,
            "related_protocols": self.related_protocols,
        }

    def _infer_protocol_type(self) -> str:
        """Infer protocol type from source file name."""
        if "cosmic" in self.source_file.lower():
            return "cosmic_entity"
        elif "claremont" in self.source_file.lower():
            return "claremont_arc"
        elif "modern" in self.source_file.lower():
            return "modern_xmen"
        elif "avengers" in self.source_file.lower():
            return "avengers_cosmic"
        elif "character" in self.source_file.lower():
            return "character_deep_dive"
        return "custom"

    def _extract_themes(self) -> List[str]:
        """Extract themes from narrative and business translation."""
        themes = set()
        text = f"{self.narrative} {self.business_translation}".lower()

        theme_keywords = {
            "power": ["power", "control", "authority", "dominance"],
            "corruption": ["corrupt", "decay", "abuse", "exploit"],
            "identity": ["identity", "self", "transformation", "change"],
            "trust": ["trust", "betrayal", "loyalty", "faith"],
            "survival": ["survival", "extinction", "threat", "crisis"],
            "governance": ["governance", "regulation", "law", "policy"],
            "ethics": ["ethic", "moral", "value", "principle"],
            "technology": ["tech", "ai", "algorithm", "system"],
            "leadership": ["leader", "founder", "ceo", "executive"],
            "economics": ["economic", "market", "capital", "resource"],
        }

        for theme, keywords in theme_keywords.items():
            if any(kw in text for kw in keywords):
                themes.add(theme)

        return list(themes)[:5]  # Limit to 5 themes

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the parsed protocol."""
        errors = []

        if not self.id:
            errors.append("Missing protocol ID")
        if not self.id.startswith("protocol_"):
            errors.append(f"Protocol ID should start with 'protocol_': {self.id}")
        if len(self.dimensions) != 4:
            errors.append(f"Expected 4 dimensions, got {len(self.dimensions)}")
        if not self.narrative:
            errors.append("Missing narrative")
        if not self.business_translation:
            errors.append("Missing business translation")
        if not self.vector_entry:
            errors.append("Missing or invalid vector entry JSON")

        return len(errors) == 0, errors


# =============================================================================
# PARSER CLASS
# =============================================================================


class ProtocolParser:
    """Parses protocol .txt files into structured data."""

    def __init__(self, comic_books_dir: Optional[Path] = None):
        self.comic_books_dir = comic_books_dir or COMIC_BOOKS_DIR
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.stats = {
            "files_processed": 0,
            "protocols_found": 0,
            "protocols_valid": 0,
            "protocols_invalid": 0,
            "dimensions_parsed": 0,
        }

    def parse_all_files(self) -> List[ParsedProtocol]:
        """Parse all .txt files in comic_books directory."""
        all_protocols = []

        txt_files = list(self.comic_books_dir.glob("*_complete.txt"))
        if not txt_files:
            # Also check for any .txt files
            txt_files = list(self.comic_books_dir.glob("*.txt"))

        print(f"Found {len(txt_files)} protocol files to parse")

        for file_path in txt_files:
            print(f"  Parsing: {file_path.name}")
            protocols = self.parse_file(file_path)
            all_protocols.extend(protocols)
            self.stats["files_processed"] += 1

        print(f"\nParsing complete:")
        print(f"  Files processed: {self.stats['files_processed']}")
        print(f"  Protocols found: {self.stats['protocols_found']}")
        print(f"  Protocols valid: {self.stats['protocols_valid']}")
        print(f"  Protocols invalid: {self.stats['protocols_invalid']}")
        print(f"  Dimensions parsed: {self.stats['dimensions_parsed']}")

        return all_protocols

    def parse_file(self, file_path: Path) -> List[ParsedProtocol]:
        """Parse a single .txt file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(
                {
                    "file": str(file_path),
                    "error": f"Failed to read file: {e}",
                }
            )
            return []

        protocols = self._extract_protocols(content, file_path.name)
        return protocols

    def _extract_protocols(
        self, content: str, source_file: str
    ) -> List[ParsedProtocol]:
        """Extract all protocols from file content."""
        protocols = []

        # Split content by JSON vector entries (each protocol ends with one)
        json_matches = list(PATTERNS["vector_json"].finditer(content))

        if not json_matches:
            self.warnings.append(
                {
                    "file": source_file,
                    "warning": "No JSON vector entries found",
                }
            )
            return protocols

        # Process each protocol section (text before each JSON block)
        for i, json_match in enumerate(json_matches):
            # Find the section of text for this protocol
            start = json_matches[i - 1].end() if i > 0 else 0
            end = json_match.end()
            section = content[start:end]

            protocol = self._parse_protocol_section(section, source_file, i + 1)
            if protocol:
                is_valid, errors = protocol.validate()
                if is_valid:
                    protocols.append(protocol)
                    self.stats["protocols_valid"] += 1
                else:
                    self.stats["protocols_invalid"] += 1
                    self.errors.append(
                        {
                            "file": source_file,
                            "protocol": protocol.id,
                            "errors": errors,
                        }
                    )
                    # Still add if it has an ID (partial data is better than none)
                    if protocol.id:
                        protocols.append(protocol)

                self.stats["protocols_found"] += 1
                self.stats["dimensions_parsed"] += len(protocol.dimensions)

        return protocols

    def _parse_protocol_section(
        self, section: str, source_file: str, index: int
    ) -> Optional[ParsedProtocol]:
        """Parse a single protocol section."""
        # Extract JSON first to get protocol ID
        json_match = PATTERNS["vector_json"].search(section)
        if not json_match:
            return None

        try:
            vector_entry = json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            self.errors.append(
                {
                    "file": source_file,
                    "section": index,
                    "error": f"Invalid JSON: {e}",
                }
            )
            vector_entry = {}

        protocol_id = vector_entry.get("id", f"protocol_unknown_{index}")
        archetype = vector_entry.get("archetype", "")

        # Extract source material
        source_match = PATTERNS["source_material"].search(section)
        source_material = source_match.group(1).strip() if source_match else ""

        # Extract narrative
        narrative_match = PATTERNS["narrative"].search(section)
        narrative = narrative_match.group(1).strip() if narrative_match else ""

        # Extract business translation
        biz_match = PATTERNS["business_translation"].search(section)
        if biz_match:
            business_concept = biz_match.group(1).strip()
            business_translation = biz_match.group(2).strip()
        else:
            business_concept = vector_entry.get("business_logic", "")
            business_translation = ""

        # Extract dimensions
        dimensions = self._parse_dimensions(section)

        # Extract from vector entry
        cosmic_tier = vector_entry.get("cosmic_tier", "planetary")
        key_characters = vector_entry.get("key_characters", [])
        related_protocols = vector_entry.get("related_protocols", [])

        return ParsedProtocol(
            id=protocol_id,
            section_number=str(index),
            archetype=archetype,
            source_material=source_material or vector_entry.get("source_material", ""),
            narrative=narrative or vector_entry.get("narrative_summary", ""),
            business_concept=business_concept,
            business_translation=business_translation,
            dimensions=dimensions,
            vector_entry=vector_entry,
            cosmic_tier=cosmic_tier,
            key_characters=key_characters,
            related_protocols=related_protocols,
            source_file=source_file,
        )

    def _parse_dimensions(self, section: str) -> List[ParsedDimension]:
        """Parse dimension blocks from section."""
        dimensions = []

        for match in PATTERNS["dimension"].finditer(section):
            dim_num, dim_label, dim_title, dim_logic, dim_metric = match.groups()

            dimension = ParsedDimension(
                dimension_id=f"D{dim_num}",
                label=dim_label.strip(),
                title=dim_title.strip(),
                logic=dim_logic.strip(),
                metric=dim_metric.strip(),
            )
            dimensions.append(dimension)

        return dimensions

    def save_to_knowledge_base(
        self, protocols: List[ParsedProtocol], output_path: Optional[Path] = None
    ) -> bool:
        """Save parsed protocols to knowledge_base.json."""
        output_path = output_path or KNOWLEDGE_BASE_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing knowledge base if it exists
        if output_path.exists():
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    kb_data = json.load(f)
            except Exception:
                kb_data = self._create_empty_knowledge_base()
        else:
            kb_data = self._create_empty_knowledge_base()

        # Add/update protocols
        for protocol in protocols:
            protocol_dict = protocol.to_dict()
            kb_data["protocols"][protocol.id] = protocol_dict

            # Add to universe protocol list if not present
            universe_id = "universe_marvel"
            if universe_id in kb_data["universes"]:
                if protocol.id not in kb_data["universes"][universe_id]["protocol_ids"]:
                    kb_data["universes"][universe_id]["protocol_ids"].append(
                        protocol.id
                    )

        # Update metadata
        kb_data["version"] = "0.2.0"
        kb_data["last_updated"] = datetime.utcnow().isoformat()
        kb_data["stats"] = {
            "total_protocols": len(kb_data["protocols"]),
            "protocols_by_type": self._count_by_type(protocols),
            "dimensions_count": sum(len(p.dimensions) for p in protocols),
        }

        # Save
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(kb_data, f, indent=2, ensure_ascii=False)
            print(f"\nSaved {len(protocols)} protocols to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving knowledge base: {e}")
            return False

    def _create_empty_knowledge_base(self) -> Dict[str, Any]:
        """Create empty knowledge base structure."""
        return {
            "universes": {
                "universe_marvel": {
                    "id": "universe_marvel",
                    "name": "Marvel Universe",
                    "universe_type": "superhero",
                    "description": "Primary superhero universe for metaphor protocols",
                    "themes": ["responsibility", "power", "sacrifice", "redemption"],
                    "visual_motifs": ["heroic imagery", "transformation", "conflict"],
                    "moral_framework": "With great power comes great responsibility",
                    "tone": "hopeful",
                    "character_ids": [],
                    "arc_ids": [],
                    "protocol_ids": [],
                    "is_public_domain": False,
                    "requires_abstraction": True,
                }
            },
            "characters": {},
            "arcs": {},
            "protocols": {},
            "tropes": {},
            "version": "0.2.0",
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _count_by_type(self, protocols: List[ParsedProtocol]) -> Dict[str, int]:
        """Count protocols by type."""
        counts: Dict[str, int] = {}
        for p in protocols:
            ptype = p.to_dict()["protocol_type"]
            counts[ptype] = counts.get(ptype, 0) + 1
        return counts

    def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate all protocol files without saving."""
        protocols = self.parse_all_files()

        validation_report = {
            "total_files": self.stats["files_processed"],
            "total_protocols": self.stats["protocols_found"],
            "valid_protocols": self.stats["protocols_valid"],
            "invalid_protocols": self.stats["protocols_invalid"],
            "errors": self.errors,
            "warnings": self.warnings,
            "is_valid": self.stats["protocols_invalid"] == 0 and len(self.errors) == 0,
        }

        return validation_report["is_valid"], validation_report

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 60)
        print("PROTOCOL PARSER VALIDATION REPORT")
        print("=" * 60)

        print(f"\nFiles processed: {self.stats['files_processed']}")
        print(f"Protocols found: {self.stats['protocols_found']}")
        print(f"  Valid: {self.stats['protocols_valid']}")
        print(f"  Invalid: {self.stats['protocols_invalid']}")
        print(f"Dimensions parsed: {self.stats['dimensions_parsed']}")

        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for err in self.errors[:10]:  # Limit to first 10
                print(
                    f"  - {err.get('file', 'unknown')}: {err.get('error', err.get('errors', 'unknown'))}"
                )
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warn in self.warnings[:5]:
                print(
                    f"  - {warn.get('file', 'unknown')}: {warn.get('warning', 'unknown')}"
                )

        print("\n" + "=" * 60)


# =============================================================================
# CLI
# =============================================================================


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse protocol .txt files into knowledge_base.json"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate files without saving",
    )
    parser.add_argument(
        "--parse",
        action="store_true",
        help="Parse and save to knowledge base",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(KNOWLEDGE_BASE_PATH),
        help="Output path for knowledge base JSON",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(COMIC_BOOKS_DIR),
        help="Input directory containing .txt files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Create parser
    proto_parser = ProtocolParser(
        comic_books_dir=Path(args.input_dir) if args.input_dir else None
    )

    if args.validate:
        is_valid, report = proto_parser.validate_all()
        proto_parser.print_report()

        if is_valid:
            print("\n✅ All protocols are valid!")
            sys.exit(0)
        else:
            print("\n❌ Validation failed - see errors above")
            sys.exit(1)

    elif args.parse:
        protocols = proto_parser.parse_all_files()
        proto_parser.print_report()

        if protocols:
            success = proto_parser.save_to_knowledge_base(
                protocols, Path(args.output) if args.output else None
            )
            if success:
                print(f"\n✅ Successfully saved {len(protocols)} protocols")
                sys.exit(0)
            else:
                print("\n❌ Failed to save knowledge base")
                sys.exit(1)
        else:
            print("\n❌ No protocols parsed")
            sys.exit(1)

    else:
        # Default: validate and report
        protocols = proto_parser.parse_all_files()
        proto_parser.print_report()

        print("\nTo save to knowledge base, run with --parse flag")
        print(
            f"Example: python -m engine.protocol_parser --parse --output {args.output}"
        )


if __name__ == "__main__":
    main()
