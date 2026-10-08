#!/usr/bin/env python3
"""
FIX EXECUTOR - Automated Priority Fixes for Comic Metaphor Engine
================================================================

Executes critical fixes identified in ISSUES_AND_FIXES.md
Priority order: Critical > High > Medium > Low

Usage:
    python FIX_EXECUTOR.py --run critical
    python FIX_EXECUTOR.py --run all
    python FIX_EXECUTOR.py --dry-run
    python FIX_EXECUTOR.py --status
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("fix_marathon.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Paths
ROOT = Path(__file__).parent
ENGINE_DIR = ROOT / "engine"
TESTS_DIR = ROOT / "tests"
COMIC_BOOKS_DIR = ROOT / "comic_books"
PROCESSED_DIR = ROOT / "processed"
KB_PATH = PROCESSED_DIR / "knowledge_base.json"

# ============================================================================
# FIX #1: PROTOCOL PARSER - txt to JSON
# ============================================================================


@dataclass
class ParsedDimension:
    """Represents a parsed dimension from protocol text"""

    id: str  # D1, D2, D3, D4
    title: str
    logic: str
    metric: str


@dataclass
class ParsedProtocol:
    """Represents a parsed protocol from .txt file"""

    id: str
    archetype: str
    source_material: str
    narrative_summary: str
    business_logic: str
    application: str
    dimensions: List[ParsedDimension]
    vector_json: Dict
    key_characters: List[str]
    related_protocols: List[str]
    cosmic_tier: str


class ProtocolParser:
    """Parse protocols from markdown .txt files"""

    def __init__(self):
        self.protocols = []

    def parse_file(self, file_path: Path) -> List[ParsedProtocol]:
        """Parse all protocols from a single file"""
        logger.info(f"Parsing {file_path.name}...")

        try:
            content = file_path.read_text(encoding="utf-8")
            protocols = []

            # Find all protocol sections (they start with ### and have protocol_)
            protocol_sections = self._split_into_protocols(content)

            for section in protocol_sections:
                try:
                    protocol = self._parse_protocol_section(section)
                    if protocol:
                        protocols.append(protocol)
                except Exception as e:
                    logger.error(f"Error parsing protocol section: {e}")
                    continue

            logger.info(f"  ✓ Parsed {len(protocols)} protocols from {file_path.name}")
            return protocols

        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return []

    def _split_into_protocols(self, content: str) -> List[str]:
        """Split content into individual protocol sections"""
        # Protocols typically start with ### N.N or ## N. pattern
        sections = []
        current_section = []

        for line in content.split("\n"):
            # Check if this is a protocol header (contains "protocol_" in nearby JSON)
            if line.startswith("###") or line.startswith("## "):
                if current_section:
                    section_text = "\n".join(current_section)
                    if "protocol_" in section_text or '"id":' in section_text:
                        sections.append(section_text)
                current_section = [line]
            else:
                current_section.append(line)

        # Add last section
        if current_section:
            section_text = "\n".join(current_section)
            if "protocol_" in section_text or '"id":' in section_text:
                sections.append(section_text)

        return sections

    def _parse_protocol_section(self, section: str) -> Optional[ParsedProtocol]:
        """Parse a single protocol section"""

        # Extract protocol ID from JSON block
        protocol_id = self._extract_protocol_id(section)
        if not protocol_id:
            return None

        # Extract vector JSON block
        vector_json = self._extract_json_block(section)
        if not vector_json:
            logger.warning(f"No JSON block found for {protocol_id}")
            vector_json = {}

        # Extract dimensions
        dimensions = self._extract_dimensions(section)

        # Extract other fields from JSON or text
        archetype = vector_json.get("archetype", "Unknown Pattern")
        source_material = vector_json.get("source_material", "")
        narrative_summary = vector_json.get("narrative_summary", "")
        business_logic = vector_json.get("business_logic", "")
        application = vector_json.get("application", "")
        key_characters = vector_json.get("key_characters", [])
        related_protocols = vector_json.get("related_protocols", [])
        cosmic_tier = vector_json.get("cosmic_tier", "street")

        return ParsedProtocol(
            id=protocol_id,
            archetype=archetype,
            source_material=source_material,
            narrative_summary=narrative_summary,
            business_logic=business_logic,
            application=application,
            dimensions=dimensions,
            vector_json=vector_json,
            key_characters=key_characters,
            related_protocols=related_protocols,
            cosmic_tier=cosmic_tier,
        )

    def _extract_protocol_id(self, section: str) -> Optional[str]:
        """Extract protocol ID from section"""
        # Look for "id": "protocol_something"
        match = re.search(r'"id"\s*:\s*"(protocol_[^"]+)"', section)
        if match:
            return match.group(1)
        return None

    def _extract_json_block(self, section: str) -> Dict:
        """Extract and parse JSON vector entry block"""
        # Find JSON block between ```json and ```
        json_match = re.search(r"```json\s*\n(.*?)\n```", section, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return {}
        return {}

    def _extract_dimensions(self, section: str) -> List[ParsedDimension]:
        """Extract D1-D4 dimensions from text"""
        dimensions = []

        # Pattern: * D1 (Bio/Internal): Title
        #          * Logic: ...
        #          * Metric: ...

        dimension_blocks = re.finditer(
            r"\* (D[1-4]) \([^)]+\):\s*([^\n]+)\s*\*\s*Logic:\s*([^\n]+)\s*\*\s*Metric:\s*([^\n]+)",
            section,
            re.MULTILINE,
        )

        for match in dimension_blocks:
            dim_id = match.group(1)
            title = match.group(2).strip()
            logic = match.group(3).strip()
            metric = match.group(4).strip()

            dimensions.append(
                ParsedDimension(id=dim_id, title=title, logic=logic, metric=metric)
            )

        return dimensions


# ============================================================================
# FIX #2: KNOWLEDGE BASE SYNC
# ============================================================================


class KnowledgeBaseUpdater:
    """Update knowledge_base.json with parsed protocols"""

    def __init__(self, kb_path: Path):
        self.kb_path = kb_path
        self.kb_data = self._load_kb()

    def _load_kb(self) -> Dict:
        """Load existing knowledge base or create new"""
        if self.kb_path.exists():
            try:
                with open(self.kb_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading KB: {e}")

        return {
            "universes": {},
            "characters": {},
            "arcs": {},
            "protocols": {},
            "tropes": {},
            "version": "0.2.0",
            "last_updated": datetime.utcnow().isoformat(),
        }

    def add_protocols(self, protocols: List[ParsedProtocol]):
        """Add parsed protocols to knowledge base"""
        for protocol in protocols:
            self.kb_data["protocols"][protocol.id] = {
                "id": protocol.id,
                "protocol_type": protocol.id.replace("protocol_", ""),
                "archetype": protocol.archetype,
                "business_logic": protocol.business_logic,
                "application": protocol.application,
                "narrative": protocol.narrative_summary,
                "business_translation": protocol.business_logic,
                "dimensions": [
                    {
                        "id": d.id,
                        "title": d.title,
                        "logic": d.logic,
                        "metric": d.metric,
                        "science_concept": "",
                        "character_anchor": "",
                        "analysis": d.logic,
                        "lesson": "",
                    }
                    for d in protocol.dimensions
                ],
                "vector_entry": protocol.vector_json,
                "risk_categories": [],
                "themes": [],
                "tone_compatibility": ["analytical"],
                "format_compatibility": ["podcast_monologue", "blog_post"],
            }

    def save(self):
        """Save updated knowledge base"""
        self.kb_path.parent.mkdir(parents=True, exist_ok=True)
        self.kb_data["last_updated"] = datetime.utcnow().isoformat()

        with open(self.kb_path, "w", encoding="utf-8") as f:
            json.dump(self.kb_data, f, indent=2)

        logger.info(
            f"✓ Saved knowledge base with {len(self.kb_data['protocols'])} protocols"
        )


# ============================================================================
# FIX #3: PROGRESS TRACKER INITIALIZATION
# ============================================================================


def fix_progress_tracker_init():
    """Fix progress tracker to count existing protocols"""

    logger.info("Fixing progress tracker initialization...")

    orchestrator_path = ROOT / "CHEETAH_MARATHON_ORCHESTRATOR.py"

    if not orchestrator_path.exists():
        logger.error("Orchestrator file not found")
        return False

    content = orchestrator_path.read_text(encoding="utf-8")

    # Find and update the _load_progress method
    old_pattern = r'"total_protocols":\s*0,'
    new_value = '"total_protocols": sum(MARATHON_CONFIG["completed"].values()),'

    if old_pattern in content:
        content = re.sub(old_pattern, new_value, content)
        orchestrator_path.write_text(content, encoding="utf-8")
        logger.info("✓ Updated progress tracker initialization")
        return True
    else:
        logger.warning("Progress tracker pattern not found - may already be fixed")
        return True


# ============================================================================
# FIX #4: ADD LOGGING
# ============================================================================


def add_logging_config():
    """Create logging configuration"""

    logger.info("Adding logging configuration...")

    logging_config = '''"""
Logging configuration for Comic Metaphor Engine
"""

import logging
import sys
from pathlib import Path

def setup_logging(log_level=logging.INFO, log_file="marathon.log"):
    """Configure logging for marathon system"""

    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
'''

    config_path = ROOT / "logging_config.py"
    config_path.write_text(logging_config, encoding="utf-8")
    logger.info(f"✓ Created {config_path}")
    return True


# ============================================================================
# MAIN EXECUTION
# ============================================================================


class FixExecutor:
    """Main fix execution coordinator"""

    def __init__(self):
        self.fixes_run = []
        self.fixes_failed = []

    def run_critical_fixes(self, dry_run=False):
        """Execute critical priority fixes"""

        logger.info("=" * 80)
        logger.info("EXECUTING CRITICAL FIXES")
        logger.info("=" * 80)

        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            return

        # Fix #1: Parse protocols and sync to knowledge base
        success = self._fix_protocol_parsing()
        if success:
            self.fixes_run.append("Fix #1: Protocol Parser")
        else:
            self.fixes_failed.append("Fix #1: Protocol Parser")

        # Fix #3: Progress tracker initialization
        success = fix_progress_tracker_init()
        if success:
            self.fixes_run.append("Fix #3: Progress Tracker")
        else:
            self.fixes_failed.append("Fix #3: Progress Tracker")

        # Fix #4: Add logging
        success = add_logging_config()
        if success:
            self.fixes_run.append("Fix #4: Logging Config")
        else:
            self.fixes_failed.append("Fix #4: Logging Config")

        self._print_summary()

    def _fix_protocol_parsing(self) -> bool:
        """Execute Fix #1: Parse protocols and update knowledge base"""

        try:
            logger.info("\n--- Fix #1: Protocol Parser & Knowledge Base Sync ---")

            parser = ProtocolParser()
            all_protocols = []

            # Parse existing protocol files
            protocol_files = [
                COMIC_BOOKS_DIR / "cosmic_entities_complete.txt",
                COMIC_BOOKS_DIR / "claremont_xmen_complete.txt",
                COMIC_BOOKS_DIR / "xmen_modern_era_complete.txt",
            ]

            for file_path in protocol_files:
                if file_path.exists():
                    protocols = parser.parse_file(file_path)
                    all_protocols.extend(protocols)
                else:
                    logger.warning(f"File not found: {file_path}")

            logger.info(f"\nTotal protocols parsed: {len(all_protocols)}")

            # Update knowledge base
            kb_updater = KnowledgeBaseUpdater(KB_PATH)
            kb_updater.add_protocols(all_protocols)
            kb_updater.save()

            # Validate
            protocols_with_dimensions = sum(
                1 for p in all_protocols if len(p.dimensions) == 4
            )
            logger.info(
                f"Protocols with complete dimensions (D1-D4): {protocols_with_dimensions}/{len(all_protocols)}"
            )

            return True

        except Exception as e:
            logger.error(f"Error in protocol parsing: {e}")
            return False

    def _print_summary(self):
        """Print execution summary"""

        logger.info("\n" + "=" * 80)
        logger.info("FIX EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Fixes Successful: {len(self.fixes_run)}")
        for fix in self.fixes_run:
            logger.info(f"  ✓ {fix}")

        if self.fixes_failed:
            logger.info(f"\nFixes Failed: {len(self.fixes_failed)}")
            for fix in self.fixes_failed:
                logger.info(f"  ✗ {fix}")

        logger.info("=" * 80 + "\n")

    def show_status(self):
        """Show current system status"""

        logger.info("\n" + "=" * 80)
        logger.info("SYSTEM STATUS")
        logger.info("=" * 80)

        # Check knowledge base
        if KB_PATH.exists():
            kb_data = json.loads(KB_PATH.read_text())
            protocol_count = len(kb_data.get("protocols", {}))

            protocols_with_dims = sum(
                1
                for p in kb_data["protocols"].values()
                if len(p.get("dimensions", [])) > 0
            )

            logger.info(f"\nKnowledge Base:")
            logger.info(f"  Protocols: {protocol_count}")
            logger.info(f"  With Dimensions: {protocols_with_dims}")
        else:
            logger.info("\nKnowledge Base: NOT FOUND")

        # Check protocol files
        logger.info(f"\nProtocol Files:")
        for file in COMIC_BOOKS_DIR.glob("*.txt"):
            if file.name != "sample_comic.txt":
                size_kb = file.stat().st_size / 1024
                logger.info(f"  {file.name}: {size_kb:.1f} KB")

        logger.info("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Execute priority fixes for Comic Metaphor Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--run", choices=["critical", "all"], help="Run fixes of specified priority"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    parser.add_argument(
        "--status", action="store_true", help="Show current system status"
    )

    args = parser.parse_args()

    executor = FixExecutor()

    if args.status:
        executor.show_status()
    elif args.run == "critical":
        executor.run_critical_fixes(dry_run=args.dry_run)
    elif args.run == "all":
        logger.info("Running all fixes (not yet implemented)")
        executor.run_critical_fixes(dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
