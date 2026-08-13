"""
Comic Metaphor Engine - Skeuomorphic UI
========================================

A vintage-inspired interface for exploring comic book metaphors
and building a database of stories applicable to various sectors.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
from engine.codex_adapter import CodexAdapter

# Import engine components
from engine.index import MetaphorIndex, build_index
from engine.ingest import DataIngestionPipeline
from engine.metaphor_engine import MetaphorEngine
from engine.narrative_generator import GenerationContext, generate_narrative
from engine.schema import (
    FormatType,
    KnowledgeBase,
    MetaphorMapping,
    Protocol,
    ToneType,
)

# =============================================================================
# SKEUOMORPHIC CSS STYLING
# =============================================================================

SKEUOMORPHIC_CSS = """
/* Main container styling - vintage paper texture */
.gradio-container {
    background: linear-gradient(135deg, #f5f0e6 0%, #e8e0d0 50%, #f0e8d8 100%) !important;
    font-family: 'Georgia', 'Times New Roman', serif !important;
}

/* Vintage header styling */
.vintage-header {
    background: linear-gradient(180deg, #8B4513 0%, #654321 50%, #4a3218 100%);
    border: 4px solid #2c1810;
    border-radius: 12px;
    box-shadow:
        inset 0 2px 4px rgba(255,255,255,0.2),
        inset 0 -2px 4px rgba(0,0,0,0.3),
        0 8px 16px rgba(0,0,0,0.4);
    padding: 20px;
    margin-bottom: 20px;
    text-align: center;
}

.vintage-header h1 {
    color: #ffd700 !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5), 0 0 10px rgba(255,215,0,0.3);
    font-family: 'Impact', 'Arial Black', sans-serif !important;
    letter-spacing: 2px;
    margin: 0 !important;
}

.vintage-header p {
    color: #f0e6d2 !important;
    font-style: italic;
    margin-top: 8px !important;
}

/* Panel styling - leather-bound book look */
.panel {
    background: linear-gradient(145deg, #f8f4ec 0%, #efe8dc 100%);
    border: 3px solid #8B4513;
    border-radius: 8px;
    box-shadow:
        inset 0 1px 3px rgba(255,255,255,0.5),
        inset 0 -1px 3px rgba(0,0,0,0.1),
        4px 4px 12px rgba(0,0,0,0.2),
        -2px -2px 8px rgba(255,255,255,0.3);
    padding: 20px;
    margin: 10px 0;
}

/* Embossed section headers */
.section-header {
    background: linear-gradient(180deg, #654321 0%, #4a3218 100%);
    color: #ffd700 !important;
    padding: 12px 20px;
    border-radius: 6px;
    margin-bottom: 15px;
    box-shadow:
        inset 0 1px 2px rgba(255,255,255,0.2),
        0 3px 6px rgba(0,0,0,0.3);
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-size: 14px;
}

/* Vintage button styling */
.vintage-btn {
    background: linear-gradient(180deg, #cd853f 0%, #8B4513 50%, #654321 100%) !important;
    border: 2px solid #2c1810 !important;
    border-radius: 8px !important;
    color: #fff8dc !important;
    font-weight: bold !important;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
    box-shadow:
        inset 0 2px 4px rgba(255,255,255,0.3),
        inset 0 -2px 4px rgba(0,0,0,0.2),
        0 4px 8px rgba(0,0,0,0.3) !important;
    transition: all 0.2s ease !important;
}

.vintage-btn:hover {
    background: linear-gradient(180deg, #daa520 0%, #cd853f 50%, #8B4513 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow:
        inset 0 2px 4px rgba(255,255,255,0.4),
        0 6px 12px rgba(0,0,0,0.4) !important;
}

.vintage-btn:active {
    transform: translateY(1px) !important;
    box-shadow:
        inset 0 -2px 4px rgba(255,255,255,0.2),
        inset 0 2px 4px rgba(0,0,0,0.3),
        0 2px 4px rgba(0,0,0,0.2) !important;
}

/* Input fields - vintage paper look */
.vintage-input textarea, .vintage-input input {
    background: linear-gradient(180deg, #fffef8 0%, #f8f4e8 100%) !important;
    border: 2px solid #8B4513 !important;
    border-radius: 6px !important;
    box-shadow:
        inset 2px 2px 4px rgba(0,0,0,0.1),
        inset -1px -1px 2px rgba(255,255,255,0.5) !important;
    font-family: 'Courier New', monospace !important;
    color: #2c1810 !important;
}

/* Dropdown styling */
.vintage-dropdown select {
    background: linear-gradient(180deg, #fffef8 0%, #f8f4e8 100%) !important;
    border: 2px solid #8B4513 !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    font-family: 'Georgia', serif !important;
    color: #2c1810 !important;
    cursor: pointer !important;
}

/* Slider styling - brass knob look */
.vintage-slider input[type="range"] {
    -webkit-appearance: none !important;
    background: linear-gradient(180deg, #d4af37 0%, #b8860b 50%, #8b6914 100%) !important;
    border-radius: 10px !important;
    height: 12px !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3) !important;
}

.vintage-slider input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none !important;
    width: 24px !important;
    height: 24px !important;
    background: linear-gradient(145deg, #ffd700 0%, #daa520 50%, #b8860b 100%) !important;
    border: 2px solid #654321 !important;
    border-radius: 50% !important;
    box-shadow:
        inset 0 2px 4px rgba(255,255,255,0.5),
        0 2px 6px rgba(0,0,0,0.4) !important;
    cursor: pointer !important;
}

/* Output display - aged parchment */
.output-display {
    background: linear-gradient(135deg, #faf8f0 0%, #f0ebe0 50%, #e8e0d0 100%) !important;
    border: 3px double #8B4513 !important;
    border-radius: 8px !important;
    padding: 20px !important;
    box-shadow:
        inset 0 0 20px rgba(139,69,19,0.1),
        0 4px 12px rgba(0,0,0,0.2) !important;
    font-family: 'Georgia', serif !important;
    line-height: 1.8 !important;
    color: #2c1810 !important;
}

/* Comic panel cards */
.comic-card {
    background: linear-gradient(145deg, #fff 0%, #f8f4e8 100%);
    border: 3px solid #2c1810;
    border-radius: 4px;
    padding: 15px;
    margin: 10px 0;
    box-shadow:
        4px 4px 0 #654321,
        6px 6px 12px rgba(0,0,0,0.2);
    position: relative;
}

.comic-card::before {
    content: "";
    position: absolute;
    top: -3px;
    left: -3px;
    right: -3px;
    bottom: -3px;
    border: 2px solid #ffd700;
    border-radius: 6px;
    pointer-events: none;
}

/* Database table styling */
.database-table {
    background: #fffef8;
    border: 2px solid #8B4513;
    border-radius: 8px;
    overflow: hidden;
}

.database-table th {
    background: linear-gradient(180deg, #654321 0%, #4a3218 100%);
    color: #ffd700 !important;
    padding: 12px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.database-table td {
    padding: 10px;
    border-bottom: 1px solid #d4c4a8;
    color: #2c1810;
}

.database-table tr:nth-child(even) {
    background: #f8f4e8;
}

/* Tabs styling */
.tabs {
    border: none !important;
}

.tab-nav button {
    background: linear-gradient(180deg, #d4c4a8 0%, #c4b498 100%) !important;
    border: 2px solid #8B4513 !important;
    border-bottom: none !important;
    border-radius: 8px 8px 0 0 !important;
    color: #2c1810 !important;
    font-weight: bold !important;
    margin-right: 4px !important;
    padding: 12px 24px !important;
}

.tab-nav button.selected {
    background: linear-gradient(180deg, #f8f4ec 0%, #efe8dc 100%) !important;
    border-bottom: 2px solid #f8f4ec !important;
    color: #8B4513 !important;
}

/* Accordion styling */
.accordion {
    border: 2px solid #8B4513 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    margin: 10px 0 !important;
}

.accordion-header {
    background: linear-gradient(180deg, #d4c4a8 0%, #c4b498 100%) !important;
    padding: 12px 16px !important;
    cursor: pointer !important;
    font-weight: bold !important;
    color: #2c1810 !important;
}

/* Progress indicator */
.progress-bar {
    background: linear-gradient(180deg, #654321 0%, #4a3218 100%);
    border-radius: 10px;
    height: 20px;
    overflow: hidden;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
}

.progress-fill {
    background: linear-gradient(180deg, #ffd700 0%, #daa520 50%, #b8860b 100%);
    height: 100%;
    transition: width 0.3s ease;
    box-shadow: inset 0 2px 4px rgba(255,255,255,0.3);
}

/* Score displays */
.score-badge {
    display: inline-block;
    background: linear-gradient(145deg, #ffd700 0%, #daa520 100%);
    border: 2px solid #8B4513;
    border-radius: 20px;
    padding: 6px 16px;
    font-weight: bold;
    color: #2c1810;
    box-shadow:
        inset 0 2px 4px rgba(255,255,255,0.4),
        0 2px 4px rgba(0,0,0,0.2);
    margin: 4px;
}

/* File upload zone */
.file-upload {
    background: repeating-linear-gradient(
        45deg,
        #f8f4e8,
        #f8f4e8 10px,
        #efe8dc 10px,
        #efe8dc 20px
    ) !important;
    border: 3px dashed #8B4513 !important;
    border-radius: 12px !important;
    padding: 40px !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
}

.file-upload:hover {
    background: repeating-linear-gradient(
        45deg,
        #efe8dc,
        #efe8dc 10px,
        #e8e0d0 10px,
        #e8e0d0 20px
    ) !important;
    border-color: #654321 !important;
}

/* Tooltips */
.tooltip {
    background: linear-gradient(180deg, #2c1810 0%, #1a0f08 100%) !important;
    color: #ffd700 !important;
    border: 1px solid #8B4513 !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    font-size: 12px !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.4) !important;
}

/* Decorative elements */
.corner-decoration {
    position: absolute;
    width: 40px;
    height: 40px;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><path d="M0,0 Q20,20 40,0 Q20,20 40,40 Q20,20 0,40 Q20,20 0,0" fill="%238B4513"/></svg>');
}

/* Animation for loading states */
@keyframes vintage-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.loading {
    animation: vintage-pulse 1.5s ease-in-out infinite;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .vintage-header h1 {
        font-size: 24px !important;
    }

    .panel {
        padding: 12px;
    }
}
"""


# =============================================================================
# ENGINE INITIALIZATION
# =============================================================================


class ComicMetaphorUI:
    """Main UI controller for the Comic Metaphor Engine."""

    def __init__(self):
        self.processed_dir = Path(__file__).parent.parent / "processed"
        self.comic_books_dir = Path(__file__).parent.parent / "comic_books"
        self.philosophy_books_dir = Path(__file__).parent.parent / "philosophy_books"
        # Ensure companion directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.comic_books_dir.mkdir(parents=True, exist_ok=True)
        self.philosophy_books_dir.mkdir(parents=True, exist_ok=True)
        self.index: Optional[MetaphorIndex] = None
        self.kb: Optional[KnowledgeBase] = None
        self.engine: Optional[MetaphorEngine] = None
        self.codex_adapter: Optional[CodexAdapter] = None

        # Initialize engine
        self._load_engine()

    def _load_engine(self):
        """Load the metaphor engine and index."""
        try:
            kb_path = self.processed_dir / "knowledge_base.json"
            if kb_path.exists():
                self.kb = KnowledgeBase.load(str(kb_path))
                self.index = build_index(self.kb, str(self.processed_dir))
                self.codex_adapter = CodexAdapter(index=self.index)
                self.engine = MetaphorEngine(self.index, self.codex_adapter)
                print(f"[OK] Loaded {len(self.kb.protocols)} protocols")
            else:
                print("[WARN] Knowledge base not found. Run ingestion first.")
        except Exception as e:
            print(f"[ERROR] Failed to load engine: {e}")

    def get_protocol_list(self) -> List[str]:
        """Get list of available protocols for dropdown."""
        if self.kb:
            return [f"{p.archetype} ({p.id})" for p in self.kb.protocols.values()]
        return ["No protocols loaded"]

    def get_sectors(self) -> List[str]:
        """Get list of target sectors."""
        return [
            "Technology & Startups",
            "Healthcare & Wellness",
            "Finance & Investment",
            "Education & Training",
            "Marketing & Sales",
            "Leadership & Management",
            "Personal Development",
            "Crisis Management",
            "Innovation & R&D",
            "Organizational Culture",
        ]

    def search_metaphors(
        self,
        query: str,
        sector: str,
        format_type: str,
        tone: str,
        creativity: float,
        depth: int,
        weights_state: Optional[Dict[str, float]] = None,
    ) -> Tuple[str, str, str]:
        """Search for relevant metaphors based on user input."""
        if not self.engine or not self.index:
            return ("⚠️ Engine not initialized. Please run ingestion first.", "", "")

        try:
            # Map format and tone strings to enums
            format_map = {
                "Podcast Monologue": FormatType.PODCAST_MONOLOGUE,
                "Marketing Email": FormatType.MARKETING_EMAIL,
                "Blog Post": FormatType.BLOG_POST,
                "Dialogue Script": FormatType.DIALOGUE_SCRIPT,
                "Executive Summary": FormatType.EXECUTIVE_SUMMARY,
            }

            tone_map = {
                "Hopeful": ToneType.HOPEFUL,
                "Gritty": ToneType.GRITTY,
                "Cautionary": ToneType.CAUTIONARY,
                "Philosophical": ToneType.PHILOSOPHICAL,
                "Inspirational": ToneType.INSPIRATIONAL,
                "Action-Oriented": ToneType.ACTION,
            }

            target_format = format_map.get(format_type, FormatType.PODCAST_MONOLOGUE)
            target_tone = tone_map.get(tone, ToneType.HOPEFUL)

            # Generate mapping
            mapping = self.engine.generate_mapping(
                topic=f"{query} in {sector}",
                target_format=target_format,
                target_tone=target_tone,
                constraints={
                    "creativity": creativity,
                    "scoring_weights": weights_state or {},
                },
                top_k=depth,
            )

            # Get the protocol
            protocol = self.index.get_protocol_by_id(mapping.protocol_id)

            # Format results
            metaphor_result = self._format_metaphor_result(mapping, protocol)
            scores_result = self._format_scores(mapping)
            insights_result = self._format_insights(mapping, protocol, sector)

            return metaphor_result, scores_result, insights_result

        except Exception as e:
            return f"❌ Error: {str(e)}", "", ""

    def _format_metaphor_result(
        self, mapping: MetaphorMapping, protocol: Optional[Protocol]
    ) -> str:
        """Format the metaphor mapping result."""
        result = []
        result.append("# 📚 Comic Metaphor Found\n")
        result.append(
            f"**Protocol:** {protocol.archetype if protocol else 'Unknown'}\n"
        )
        result.append(f"**Core Tension:** {mapping.core_tension}\n")
        result.append(f"**Target Emotion:** {mapping.target_emotion}\n")
        result.append("\n---\n")

        if mapping.mappings:
            result.append("## 🔗 Mapping Elements\n")
            for elem in mapping.mappings:
                result.append(f"- **{elem.real_world}** → *{elem.comic_analog}*")
                result.append(f"  - {elem.explanation}")
                result.append(f"  - Confidence: {elem.confidence:.0%}\n")

        if mapping.beat_structure:
            result.append("\n## 🎬 Narrative Beats\n")
            for i, beat in enumerate(mapping.beat_structure, 1):
                result.append(f"{i}. {beat}\n")

        return "\n".join(result)

    def _format_scores(self, mapping: MetaphorMapping) -> str:
        """Format the codex scores."""
        result = []
        result.append("# 📊 Quality Scores\n")
        result.append(f"| Metric | Score | Rating |")
        result.append(f"|--------|-------|--------|")

        scores = [
            ("Trueness", mapping.trueness_score),
            ("Flow", mapping.flow_score),
            ("PCS", mapping.pcs_score),
            ("TAP", mapping.tap_score),
            ("Overall Fit", mapping.overall_fit),
        ]

        for name, score in scores:
            rating = self._get_rating(score)
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            result.append(f"| {name} | {bar} {score:.1%} | {rating} |")

        return "\n".join(result)

    def _get_rating(self, score: float) -> str:
        """Get a rating emoji based on score."""
        if score >= 0.8:
            return "⭐⭐⭐"
        elif score >= 0.6:
            return "⭐⭐"
        elif score >= 0.4:
            return "⭐"
        else:
            return "📈"

    def _format_insights(
        self, mapping: MetaphorMapping, protocol: Optional[Protocol], sector: str
    ) -> str:
        """Format strategic insights."""
        result = []
        result.append("# 💡 Strategic Insights\n")
        result.append(f"**Sector Application:** {sector}\n")

        if protocol:
            result.append(f"\n## Business Translation\n")
            result.append(f"{protocol.business_translation[:500]}...\n")

            if protocol.themes:
                result.append(f"\n## Key Themes\n")
                for theme in protocol.themes:
                    result.append(f"- {theme.title()}")

            if protocol.dimensions:
                result.append(f"\n\n## Dimensional Analysis\n")
                for dim in protocol.dimensions[:2]:
                    result.append(f"### {dim.title}\n")
                    result.append(f"*{dim.analysis[:200]}...*\n")

        return "\n".join(result)

    def upload_comic(self, file) -> str:
        """Handle comic book file upload."""

        if file is None:
            return "No file uploaded."

        try:
            # Ensure directory exists
            self.comic_books_dir.mkdir(parents=True, exist_ok=True)
            # Copy file to comic_books directory

            dest_path = self.comic_books_dir / Path(file.name).name

            with open(file.name, "rb") as src:
                with open(dest_path, "wb") as dst:
                    dst.write(src.read())

            return f"✅ Uploaded: {dest_path.name}\n\nRun ingestion to process the new comic book."

        except Exception as e:
            return f"❌ Upload failed: {str(e)}"

    def upload_philosophy_bulk(self, files) -> str:
        """Handle bulk philosophy book file upload."""
        if not files:
            return "No files uploaded."

        uploaded = []
        try:
            # Ensure directory exists
            self.philosophy_books_dir.mkdir(parents=True, exist_ok=True)

            for file in files:
                dest_path = self.philosophy_books_dir / Path(file.name).name
                with open(file.name, "rb") as src:
                    with open(dest_path, "wb") as dst:
                        dst.write(src.read())
                uploaded.append(dest_path.name)

            return f"✅ Uploaded {len(uploaded)} files: {', '.join(uploaded)}\n\nRun ingestion to process the new philosophy books."

        except Exception as e:
            return f"❌ Upload failed: {str(e)}"

    def quick_reindex(self) -> str:
        """Rebuild FAISS index without re-embedding (for metadata changes)."""
        try:
            if not self.index:
                return "Index not loaded. Run ingestion first."

            # Reload protocols and rebuild index
            kb_path = self.processed_dir / "knowledge_base.json"
            if kb_path.exists():
                self.kb = KnowledgeBase.load(str(kb_path))
                self.index = build_index(self.kb, str(self.processed_dir))
                return "✅ Quick reindex complete. Index rebuilt without re-embedding."
            else:
                return "Knowledge base not found. Run full ingestion."
        except Exception as e:
            return f"❌ Reindex failed: {str(e)}"

    def export_metaphor(self, topic: str, format_type: str) -> str:
        """Export a metaphor package."""
        if not self.engine:
            return "Engine not initialized."

        try:
            # Generate metaphor
            mapping = self.engine.generate_mapping(
                topic=topic,
                target_format=FormatType.PODCAST_MONOLOGUE,
                target_tone=ToneType.HOPEFUL,
            )

            if format_type == "Markdown":
                content = f"# Metaphor Export: {topic}\n\n{mapping}\n\n## Scores\n- Trueness: {mapping.trueness_score}\n- Flow: {mapping.flow_score}"
                # In real impl, save to file and return path
                return f"Markdown export generated for '{topic}'"
            elif format_type == "PDF":
                return f"PDF export generated for '{topic}' (placeholder)"
            elif format_type == "JSON":
                return f"JSON export generated for '{topic}' (placeholder)"
        except Exception as e:
            return f"Export failed: {str(e)}"

    def create_shelf(self, name: str, tags: str) -> str:
        """Create a new shelf/collection."""
        if not name:
            return "Shelf name required."

        try:
            shelf_data = {
                "name": name,
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
                "created": datetime.utcnow().isoformat(),
                "items": [],
            }
            # Placeholder: save to shelves.json
            shelves_path = self.processed_dir / "shelves.json"
            if shelves_path.exists():
                with open(shelves_path, "r") as f:
                    shelves = json.load(f)
            else:
                shelves = []
            shelves.append(shelf_data)
            with open(shelves_path, "w") as f:
                json.dump(shelves, f, indent=2)
            return f"✅ Shelf '{name}' created."
        except Exception as e:
            return f"❌ Failed to create shelf: {str(e)}"

    def get_shelves(self) -> str:
        """Get list of shelves."""
        try:
            shelves_path = self.processed_dir / "shelves.json"
            if shelves_path.exists():
                with open(shelves_path, "r") as f:
                    shelves = json.load(f)
                result = "# 📚 Your Shelves\n\n"
                for shelf in shelves:
                    result += f"- **{shelf['name']}**: {', '.join(shelf['tags'])}\n"
                return result
            else:
                return "No shelves created yet."
        except Exception as e:
            return f"Failed to load shelves: {str(e)}"

    def run_ingestion(self) -> str:
        """Run the data ingestion pipeline."""
        try:
            pipeline = DataIngestionPipeline(
                raw_dir=str(Path(__file__).parent.parent),
                processed_dir=str(self.processed_dir),
            )

            kb = pipeline.build_knowledge_base()
            pipeline.save_processed_data(kb)

            # Reload engine
            self._load_engine()

            stats = kb.get_stats()
            comic_count = len(
                [
                    p
                    for p in kb.protocols.values()
                    if "Comic Book:" in (p.application or "")
                ]
            )

            return (
                f"✅ Ingestion Complete!\n\n"
                f"**Protocols:** {stats['protocols']}\n"
                f"**Comic Books Parsed:** {comic_count}\n"
                f"**Universes:** {stats['universes']}\n"
                f"**Characters:** {stats['characters']}\n"
                f"**Arcs:** {stats['arcs']}"
            )

        except Exception as e:
            return f"❌ Ingestion failed: {str(e)}"

    def get_database_view(self) -> str:
        """Get a view of the current database."""
        if not self.kb:
            return "Database not loaded. Run ingestion first."

        result = []
        result.append("# 📖 Metaphor Database\n")
        result.append(f"**Total Protocols:** {len(self.kb.protocols)}\n")
        result.append("\n| Protocol | Archetype | Themes | Source |")
        result.append("|----------|-----------|--------|--------|")

        for pid, protocol in self.kb.protocols.items():
            themes = ", ".join(protocol.themes[:3]) if protocol.themes else "—"
            source = protocol.application or "Storylines"
            result.append(
                f"| {pid[:20]}... | {protocol.archetype[:25]} | {themes[:30]} | {source[:20]} |"
            )

        return "\n".join(result)

    def get_books_index(self) -> str:
        """Render the books_index.json manifest for archival/companion view."""
        index_path = self.processed_dir / "books_index.json"
        if not index_path.exists():
            return "No books index found. Upload and run ingestion to generate the archive manifest."

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return f"Failed to load books index: {e}"

        if not isinstance(data, list) or not data:
            return "Books index is empty."

        rows = []
        rows.append("# 📚 Books Index")
        rows.append("\n| File | Type | Pages | Characters | Added |")
        rows.append("|------|------|-------|------------|-------|")
        for entry in data[:500]:
            rows.append(
                f"| {Path(entry.get('filename', '')).name} | "
                f"{entry.get('source_type', '-')} | "
                f"{entry.get('page_count', 0)} | "
                f"{entry.get('text_chars', 0)} | "
                f"{entry.get('timestamp', '')} |"
            )
        if len(data) > 500:
            rows.append(f"\n… and {len(data) - 500} more entries.")
        return "\n".join(rows)


# =============================================================================
# GRADIO UI BUILDER
# =============================================================================


def create_ui():
    """Create the Gradio UI application."""
    controller = ComicMetaphorUI()

    with gr.Blocks(css=SKEUOMORPHIC_CSS, title="Comic Metaphor Engine") as app:
        # Shared state for scoring weights (updated from Settings tab)
        scoring_weights_state = gr.State(
            {
                "similarity": 0.55,
                "tone": 0.15,
                "format": 0.15,
                "theme": 0.10,
                "risk": 0.05,
            }
        )
        # Header
        gr.HTML("""
            <div class="vintage-header">
                <h1>📚 COMIC METAPHOR ENGINE 📚</h1>
                <p>Transform Business Challenges into Heroic Narratives</p>
            </div>
        """)

        with gr.Tabs() as tabs:
            # =================================================================
            # TAB 1: METAPHOR SEARCH
            # =================================================================
            with gr.Tab("🔍 Search Metaphors", elem_classes=["panel"]):
                gr.HTML('<div class="section-header">📝 Describe Your Challenge</div>')

                with gr.Row():
                    with gr.Column(scale=2):
                        query_input = gr.Textbox(
                            label="Your Topic or Challenge",
                            placeholder="e.g., 'Managing team burnout during rapid scaling'",
                            lines=3,
                            elem_classes=["vintage-input"],
                        )

                    with gr.Column(scale=1):
                        sector_dropdown = gr.Dropdown(
                            label="Target Sector",
                            choices=controller.get_sectors(),
                            value="Technology & Startups",
                            elem_classes=["vintage-dropdown"],
                        )

                gr.HTML('<div class="section-header">⚙️ Output Settings</div>')

                with gr.Row():
                    format_dropdown = gr.Dropdown(
                        label="Output Format",
                        choices=[
                            "Podcast Monologue",
                            "Marketing Email",
                            "Blog Post",
                            "Dialogue Script",
                            "Executive Summary",
                        ],
                        value="Podcast Monologue",
                        elem_classes=["vintage-dropdown"],
                    )

                    tone_dropdown = gr.Dropdown(
                        label="Narrative Tone",
                        choices=[
                            "Hopeful",
                            "Gritty",
                            "Cautionary",
                            "Philosophical",
                            "Inspirational",
                            "Action-Oriented",
                        ],
                        value="Hopeful",
                        elem_classes=["vintage-dropdown"],
                    )

                with gr.Row():
                    creativity_slider = gr.Slider(
                        label="🎨 Creativity Level",
                        minimum=0.1,
                        maximum=1.0,
                        value=0.7,
                        step=0.1,
                        elem_classes=["vintage-slider"],
                    )

                    depth_slider = gr.Slider(
                        label="📊 Analysis Depth",
                        minimum=1,
                        maximum=10,
                        value=5,
                        step=1,
                        elem_classes=["vintage-slider"],
                    )

                search_btn = gr.Button(
                    "🔮 Find Metaphors", variant="primary", elem_classes=["vintage-btn"]
                )

                gr.HTML('<div class="section-header">📜 Results</div>')

                with gr.Row():
                    with gr.Column(scale=2):
                        metaphor_output = gr.Markdown(
                            label="Metaphor Mapping", elem_classes=["output-display"]
                        )

                    with gr.Column(scale=1):
                        scores_output = gr.Markdown(
                            label="Quality Scores", elem_classes=["output-display"]
                        )

                insights_output = gr.Markdown(
                    label="Strategic Insights", elem_classes=["output-display"]
                )

                # Wire up search button
                search_btn.click(
                    fn=controller.search_metaphors,
                    inputs=[
                        query_input,
                        sector_dropdown,
                        format_dropdown,
                        tone_dropdown,
                        creativity_slider,
                        depth_slider,
                        scoring_weights_state,
                    ],
                    outputs=[metaphor_output, scores_output, insights_output],
                )

            # =================================================================
            # TAB 2: COMIC LIBRARY
            # =================================================================
            with gr.Tab("📖 Comic Library", elem_classes=["panel"]):
                gr.HTML('<div class="section-header">📚 Upload Comic Books</div>')

                with gr.Row():
                    with gr.Column():
                        file_upload = gr.File(
                            label="Upload Comic Book (PDF or TXT)",
                            file_types=[".pdf", ".txt"],
                            elem_classes=["file-upload"],
                        )
                        upload_status = gr.Markdown()

                        file_upload.change(
                            fn=controller.upload_comic,
                            inputs=[file_upload],
                            outputs=[upload_status],
                        )

                    with gr.Column():
                        gr.HTML("""

                            <div class="comic-card">

                                <h3>📋 Supported Formats</h3>

                                <ul>

                                    <li><strong>PDF:</strong> Comic or philosophy book scans with text</li>

                                    <li><strong>TXT:</strong> Comic scripts, summaries, or philosophy excerpts</li>
                                    <li><strong>MD:</strong> Markdown notes and structured metaphors</li>

                                </ul>
                                <p><em>Files should contain protocol definitions in standard format (The "X" Protocol sections with dimensions and vector entry JSON).</em></p>

                            </div>

                        """)

                gr.HTML('<div class="section-header">🔄 Process Library</div>')

                ingest_btn = gr.Button(
                    "⚡ Run Ingestion Pipeline (Comics + Philosophy)",
                    variant="primary",
                    elem_classes=["vintage-btn"],
                )

                ingest_output = gr.Markdown(elem_classes=["output-display"])

                ingest_btn.click(
                    fn=controller.run_ingestion, inputs=[], outputs=[ingest_output]
                )

            # =================================================================
            # TAB 3: PHILOSOPHY LIBRARY

            with gr.Tab("📚 Philosophy Library", elem_classes=["panel"]):
                gr.HTML('<div class="section-header">📥 Upload Philosophy Books</div>')

                with gr.Row():
                    with gr.Column():
                        phil_file_upload = gr.File(
                            label="Upload Philosophy (PDF/TXT/MD/EPUB)",
                            file_types=[".pdf", ".txt", ".md", ".epub"],
                            file_count="multiple",  # Support bulk upload
                            elem_classes=["file-upload"],
                        )
                        phil_upload_status = gr.Markdown()

                        phil_file_upload.change(
                            fn=controller.upload_philosophy_bulk,
                            inputs=[phil_file_upload],
                            outputs=[phil_upload_status],
                        )

                    with gr.Column():
                        gr.HTML("""
                            <div class="comic-card">
                                <h3>🧠 Supported Philosophy Sources</h3>
                                <ul>
                                    <li><strong>PDF:</strong> Book scans or exports</li>
                                    <li><strong>TXT/MD:</strong> Excerpts, notes, structured metaphors</li>
                                    <li><strong>EPUB:</strong> eBook chapters</li>
                                </ul>
                                <p><em>Use the standard protocol format (The "X" Protocol + dimensions + vector JSON).</em></p>
                            </div>
                        """)

                gr.HTML('<div class="section-header">🔄 Process Library</div>')
                phil_ingest_btn = gr.Button(
                    "⚡ Run Ingestion Pipeline (Philosophy + Comics)",
                    variant="primary",
                    elem_classes=["vintage-btn"],
                )
                phil_ingest_output = gr.Markdown(elem_classes=["output-display"])
                phil_ingest_btn.click(
                    fn=controller.run_ingestion, inputs=[], outputs=[phil_ingest_output]
                )

            # =================================================================
            # TAB 4: DATABASE VIEW
            # =================================================================
            with gr.Tab("🗄️ Database", elem_classes=["panel"]):
                gr.HTML('<div class="section-header">📊 Protocol Database</div>')

                refresh_btn = gr.Button("🔄 Refresh View", elem_classes=["vintage-btn"])

                database_view = gr.Markdown(
                    value=controller.get_database_view(),
                    elem_classes=["output-display", "database-table"],
                )

                refresh_btn.click(
                    fn=controller.get_database_view, inputs=[], outputs=[database_view]
                )

                gr.HTML('<div class="section-header">📚 Books Index</div>')
                with gr.Row():
                    books_refresh_btn = gr.Button(
                        "🔄 Refresh Books Index", elem_classes=["vintage-btn"]
                    )
                    quick_reindex_btn = gr.Button(
                        "⚡ Quick Reindex (Skip Embedding)",
                        elem_classes=["vintage-btn"],
                    )
                books_index_view = gr.Markdown(
                    value=controller.get_books_index(),
                    elem_classes=["output-display", "database-table"],
                )
                books_refresh_btn.click(
                    fn=controller.get_books_index, inputs=[], outputs=[books_index_view]
                )
                quick_reindex_btn.click(
                    fn=controller.quick_reindex, inputs=[], outputs=[books_index_view]
                )

                gr.HTML('<div class="section-header">📈 Statistics</div>')

                with gr.Row():
                    gr.HTML("""
                        <div class="comic-card">
                            <h3>📈 Usage Tips</h3>
                            <ul>
                                <li>Upload comic books to expand your metaphor library</li>
                                <li>Run ingestion after adding new comics</li>
                                <li>Use specific topics for better matches</li>
                                <li>Adjust creativity for more unique metaphors</li>
                            </ul>
                        </div>
                    """)

            # =================================================================
            # TAB 4: SETTINGS
            # =================================================================
            with gr.Tab("⚙️ Settings", elem_classes=["panel"]):
                gr.HTML('<div class="section-header">🔧 Engine Configuration</div>')

                with gr.Row():
                    with gr.Column():
                        gr.HTML("""
                            <div class="comic-card">
                                <h3>🧠 Embedding Model</h3>
                                <p><code>all-MiniLM-L6-v2</code></p>
                                <p>Lightweight sentence transformer for fast semantic search.</p>
                            </div>
                        """)

                    with gr.Column():
                        gr.HTML("""
                            <div class="comic-card">
                                <h3>🔍 Index Type</h3>
                                <p><code>FAISS IndexFlatIP</code></p>
                                <p>Inner product similarity for normalized vectors.</p>
                            </div>
                        """)

                gr.HTML('<div class="section-header">📁 Paths</div>')

                with gr.Row():
                    processed_path = gr.Textbox(
                        label="Processed Data Directory",
                        value=str(controller.processed_dir),
                        interactive=False,
                        elem_classes=["vintage-input"],
                    )

                    comics_path = gr.Textbox(
                        label="Comic Books Directory",
                        value=str(controller.comic_books_dir),
                        interactive=False,
                        elem_classes=["vintage-input"],
                    )

                gr.HTML('<div class="section-header">⚙️ Scoring Weights</div>')

                with gr.Row():
                    similarity_weight = gr.Slider(
                        label="Similarity Weight",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.55,
                        step=0.05,
                    )
                    tone_weight = gr.Slider(
                        label="Tone Weight",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.15,
                        step=0.05,
                    )
                    format_weight = gr.Slider(
                        label="Format Weight",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.15,
                        step=0.05,
                    )
                    theme_weight = gr.Slider(
                        label="Theme Weight",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.10,
                        step=0.05,
                    )

                # =================================================================
                # TAB 5: EXPORT
                # =================================================================
                with gr.Tab("📤 Export", elem_classes=["panel"]):
                    gr.HTML(
                        '<div class="section-header">📄 Export Metaphor Packages</div>'
                    )

                    export_topic = gr.Textbox(
                        label="Topic to Export",
                        placeholder="e.g., 'team burnout'",
                        elem_classes=["vintage-input"],
                    )
                    export_format = gr.Dropdown(
                        label="Export Format",
                        choices=["Markdown", "PDF", "JSON"],
                        value="Markdown",
                        elem_classes=["vintage-dropdown"],
                    )

                    export_btn = gr.Button(
                        "📤 Generate Export", elem_classes=["vintage-btn"]
                    )
                    export_output = gr.File(elem_classes=["output-display"])

                    export_btn.click(
                        fn=controller.export_metaphor,
                        inputs=[export_topic, export_format],
                        outputs=[export_output],
                    )

                # =================================================================
                # TAB 6: SHELVES
                # =================================================================
                with gr.Tab("📚 Shelves", elem_classes=["panel"]):
                    gr.HTML('<div class="section-header">🏷️ Collections & Tags</div>')

                    shelf_name = gr.Textbox(
                        label="Shelf Name",
                        placeholder="e.g., 'Leadership Metaphors'",
                        elem_classes=["vintage-input"],
                    )
                    shelf_tags = gr.Textbox(
                        label="Tags (comma-separated)",
                        placeholder="e.g., 'leadership, team, growth'",
                        elem_classes=["vintage-input"],
                    )

                    create_shelf_btn = gr.Button(
                        "➕ Create Shelf", elem_classes=["vintage-btn"]
                    )
                    shelf_status = gr.Markdown()

                    create_shelf_btn.click(
                        fn=controller.create_shelf,
                        inputs=[shelf_name, shelf_tags],
                        outputs=[shelf_status],
                    )

                    gr.HTML('<div class="section-header">📖 Your Shelves</div>')
                    shelves_refresh_btn = gr.Button(
                        "🔄 Refresh Shelves", elem_classes=["vintage-btn"]
                    )
                    shelves_view = gr.Markdown(elem_classes=["output-display"])

                    shelves_refresh_btn.click(
                        fn=controller.get_shelves, inputs=[], outputs=[shelves_view]
                    )

                # OCR settings
                ocr_toggle = gr.Checkbox(
                    label="Enable OCR for Image-Based Comics",
                    value=False,
                    elem_classes=["vintage-input"],
                )
                ocr_lang_dropdown = gr.Dropdown(
                    label="OCR Language",
                    choices=["eng", "fra", "deu", "spa", "ita", "por"],
                    value="eng",
                    elem_classes=["vintage-dropdown"],
                )

                # Wire sliders to update shared scoring weights state
                def _update_weights(sim, tone, fmt, theme):
                    # Risk remains default unless extended in Settings later
                    total = max(sim + tone + fmt + theme + 0.05, 1e-6)
                    return {
                        "similarity": sim / total,
                        "tone": tone / total,
                        "format": fmt / total,
                        "theme": theme / total,
                        "risk": 0.05 / total,
                    }

                similarity_weight.change(
                    fn=_update_weights,
                    inputs=[
                        similarity_weight,
                        tone_weight,
                        format_weight,
                        theme_weight,
                    ],
                    outputs=[scoring_weights_state],
                )
                tone_weight.change(
                    fn=_update_weights,
                    inputs=[
                        similarity_weight,
                        tone_weight,
                        format_weight,
                        theme_weight,
                    ],
                    outputs=[scoring_weights_state],
                )
                format_weight.change(
                    fn=_update_weights,
                    inputs=[
                        similarity_weight,
                        tone_weight,
                        format_weight,
                        theme_weight,
                    ],
                    outputs=[scoring_weights_state],
                )
                theme_weight.change(
                    fn=_update_weights,
                    inputs=[
                        similarity_weight,
                        tone_weight,
                        format_weight,
                        theme_weight,
                    ],
                    outputs=[scoring_weights_state],
                )

        # Footer
        gr.HTML("""
            <div style="text-align: center; padding: 20px; color: #654321; font-style: italic;">
                <p>Comic Metaphor Engine v1.0 • Powered by Cheetah v3</p>
                <p>Transform complexity into clarity through the power of storytelling.</p>
            </div>
        """)

    return app


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  COMIC METAPHOR ENGINE - Skeuomorphic UI")
    print("=" * 60)
    print()

    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, inbrowser=True)
