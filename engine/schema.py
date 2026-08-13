"""
Comic Book Metaphor Engine - Schema Definitions
================================================

Comprehensive data models for the metaphor intelligence system.
These schemas define the structure of:
- Comic universes, characters, arcs, and tropes
- Business/life mapping protocols
- Metaphor mappings and generation contexts
- Benchmark and scoring results

All models are designed to integrate with:
- TAP (10-metric weighted scoring) from IHS system
- Codex engine scoring (Trueness, Flow, PCS, RPS, CU)
- Cheetah v3 benchmarking framework
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# =============================================================================
# ENUMS
# =============================================================================


class UniverseType(Enum):
    """Classification of comic universe types."""

    SUPERHERO = "superhero"
    INDIE = "indie"
    SCIFI = "scifi"
    FANTASY = "fantasy"
    HORROR = "horror"
    SLICE_OF_LIFE = "slice_of_life"
    SATIRE = "satire"


class ToneType(Enum):
    """Narrative tone classifications."""

    DARK = "dark"
    HOPEFUL = "hopeful"
    GRITTY = "gritty"
    COMEDIC = "comedic"
    INSPIRATIONAL = "inspirational"
    CAUTIONARY = "cautionary"
    PHILOSOPHICAL = "philosophical"
    ACTION = "action"


class FormatType(Enum):
    """Output format types for generated content."""

    PODCAST_MONOLOGUE = "podcast_monologue"
    PODCAST_INTERVIEW = "podcast_interview"
    MARKETING_EMAIL = "marketing_email"
    MARKETING_LANDING = "marketing_landing"
    BLOG_POST = "blog_post"
    SOCIAL_THREAD = "social_thread"
    DIALOGUE_SCRIPT = "dialogue_script"
    PRESENTATION = "presentation"
    VIDEO_SCRIPT = "video_script"
    BOOK_CHAPTER = "book_chapter"


class RiskCategory(Enum):
    """Risk categories from storyline protocols."""

    OWNERSHIP = "ownership"  # Armor Wars: My tech is out there
    IDENTITY = "identity"  # Secret Invasion: Trust issues
    CONTROL = "control"  # Days of Future Past: Tools controlling me
    AVOIDANCE = "avoidance"  # Planet Hulk: Problems coming back
    TRANSFORMATION = "transformation"  # General change/growth arcs
    SACRIFICE = "sacrifice"  # Hero's journey sacrifice beats
    REDEMPTION = "redemption"  # Comeback/redemption arcs


class DimensionType(Enum):
    """The 4-dimensional analysis framework."""

    D1_BIO = "D1"  # Biological/Internal
    D2_TECH = "D2"  # Technological/External
    D3_ECO = "D3"  # Ecological/Resources
    D4_COSMIC = "D4"  # Cosmic/Limits


class ProtocolType(Enum):
    """Protocol classifications from storyline database."""

    ARMOR_WARS = "armor_wars"
    SECRET_INVASION = "secret_invasion"
    DAYS_OF_FUTURE_PAST = "days_of_future_past"
    PLANET_HULK = "planet_hulk"
    INFINITY_GAUNTLET = "infinity_gauntlet"
    CIVIL_WAR = "civil_war"
    KRAKOA = "krakoa"
    DAMAGE_CONTROL = "damage_control"
    COSMIC_ENTITY = "cosmic_entity"
    CLAREMONT_ARC = "claremont_arc"
    MODERN_XMEN = "modern_xmen"
    AVENGERS_COSMIC = "avengers_cosmic"
    CHARACTER_DEEP_DIVE = "character_deep_dive"
    CUSTOM = "custom"


# =============================================================================
# CORE DATA MODELS
# =============================================================================


@dataclass
class Dimension:
    """
    A single dimension in the 4D analysis framework.
    Maps to D1 (Bio), D2 (Tech), D3 (Eco), D4 (Cosmic).
    """

    id: DimensionType
    title: str
    science_concept: str
    character_anchor: str  # e.g., "Captain America vs Hulk"
    analysis: str
    lesson: str
    metric: str  # What this dimension measures

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id.value,
            "title": self.title,
            "science_concept": self.science_concept,
            "character_anchor": self.character_anchor,
            "analysis": self.analysis,
            "lesson": self.lesson,
            "metric": self.metric,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dimension":
        return cls(
            id=DimensionType(data["id"]),
            title=data["title"],
            science_concept=data["science_concept"],
            character_anchor=data["character_anchor"],
            analysis=data["analysis"],
            lesson=data["lesson"],
            metric=data["metric"],
        )


@dataclass
class BusinessVector:
    """
    Business/life translation of a comic concept.
    Bridges narrative elements to real-world applications.
    """

    id: str
    dimension: DimensionType
    logic: str  # The underlying business logic
    metric: str  # What it measures
    real_world_example: str  # Concrete application
    risk_level: float = 0.5  # 0-1 scale
    opportunity_level: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "dimension": self.dimension.value,
            "logic": self.logic,
            "metric": self.metric,
            "real_world_example": self.real_world_example,
            "risk_level": self.risk_level,
            "opportunity_level": self.opportunity_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessVector":
        return cls(
            id=data["id"],
            dimension=DimensionType(data["dimension"]),
            logic=data["logic"],
            metric=data["metric"],
            real_world_example=data["real_world_example"],
            risk_level=data.get("risk_level", 0.5),
            opportunity_level=data.get("opportunity_level", 0.5),
        )


@dataclass
class Character:
    """
    A character in a comic universe.
    Includes archetype information for metaphor mapping.
    """

    id: str
    name: str
    universe_id: str
    archetypes: List[str]  # e.g., ["reluctant_hero", "mentor"]
    motivations: List[str]
    traits: List[str]
    arc_ids: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(
        default_factory=dict
    )  # char_id -> relationship type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "universe_id": self.universe_id,
            "archetypes": self.archetypes,
            "motivations": self.motivations,
            "traits": self.traits,
            "arc_ids": self.arc_ids,
            "relationships": self.relationships,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        return cls(
            id=data["id"],
            name=data["name"],
            universe_id=data["universe_id"],
            archetypes=data.get("archetypes", []),
            motivations=data.get("motivations", []),
            traits=data.get("traits", []),
            arc_ids=data.get("arc_ids", []),
            relationships=data.get("relationships", {}),
        )


@dataclass
class Trope:
    """
    A narrative trope/pattern that can be mapped to life situations.
    """

    id: str
    name: str
    description: str
    canonical_structure: List[str]  # Beat-by-beat structure
    use_cases: List[str]  # When to apply this trope
    tone_compatibility: List[ToneType] = field(default_factory=list)
    format_compatibility: List[FormatType] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "canonical_structure": self.canonical_structure,
            "use_cases": self.use_cases,
            "tone_compatibility": [t.value for t in self.tone_compatibility],
            "format_compatibility": [f.value for f in self.format_compatibility],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trope":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            canonical_structure=data.get("canonical_structure", []),
            use_cases=data.get("use_cases", []),
            tone_compatibility=[
                ToneType(t) for t in data.get("tone_compatibility", [])
            ],
            format_compatibility=[
                FormatType(f) for f in data.get("format_compatibility", [])
            ],
        )


@dataclass
class Arc:
    """
    A story arc that can serve as a metaphor framework.
    """

    id: str
    title: str
    universe_id: str
    source_material: str  # e.g., "Iron Man: Armor Wars (1987)"
    narrative_summary: str
    stages: List[str]  # setup, conflict, climax, resolution
    themes: List[str]
    risk_category: RiskCategory
    character_ids: List[str] = field(default_factory=list)
    trope_ids: List[str] = field(default_factory=list)
    dimensions: List[Dimension] = field(default_factory=list)
    business_vectors: List[BusinessVector] = field(default_factory=list)

    # Scoring/metrics
    emotional_intensity: float = 0.5  # 0-1
    complexity: float = 0.5  # 0-1
    versatility: float = 0.5  # How many formats it works for

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "universe_id": self.universe_id,
            "source_material": self.source_material,
            "narrative_summary": self.narrative_summary,
            "stages": self.stages,
            "themes": self.themes,
            "risk_category": self.risk_category.value,
            "character_ids": self.character_ids,
            "trope_ids": self.trope_ids,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "business_vectors": [b.to_dict() for b in self.business_vectors],
            "emotional_intensity": self.emotional_intensity,
            "complexity": self.complexity,
            "versatility": self.versatility,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Arc":
        return cls(
            id=data["id"],
            title=data["title"],
            universe_id=data["universe_id"],
            source_material=data.get("source_material", ""),
            narrative_summary=data.get("narrative_summary", ""),
            stages=data.get("stages", []),
            themes=data.get("themes", []),
            risk_category=RiskCategory(data.get("risk_category", "transformation")),
            character_ids=data.get("character_ids", []),
            trope_ids=data.get("trope_ids", []),
            dimensions=[Dimension.from_dict(d) for d in data.get("dimensions", [])],
            business_vectors=[
                BusinessVector.from_dict(b) for b in data.get("business_vectors", [])
            ],
            emotional_intensity=data.get("emotional_intensity", 0.5),
            complexity=data.get("complexity", 0.5),
            versatility=data.get("versatility", 0.5),
        )


@dataclass
class Protocol:
    """
    A full protocol from the storyline database.
    This is the primary unit for metaphor retrieval.
    Integrates with the "Storylines for metaphor engine" data.
    """

    id: str
    protocol_type: ProtocolType
    archetype: str  # e.g., "Stark vs. The Market"
    business_logic: str  # Core business translation
    application: str  # When to use this protocol
    narrative: str  # The comic story summary
    business_translation: str  # How it maps to business
    dimensions: List[Dimension]
    vector_entry: Dict[str, Any]  # The JSON vector DB entry

    # Tags for retrieval
    risk_categories: List[RiskCategory] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    tone_compatibility: List[ToneType] = field(default_factory=list)
    format_compatibility: List[FormatType] = field(default_factory=list)

    # Embeddings for semantic search (populated by index module)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "protocol_type": self.protocol_type.value,
            "archetype": self.archetype,
            "business_logic": self.business_logic,
            "application": self.application,
            "narrative": self.narrative,
            "business_translation": self.business_translation,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "vector_entry": self.vector_entry,
            "risk_categories": [r.value for r in self.risk_categories],
            "themes": self.themes,
            "tone_compatibility": [t.value for t in self.tone_compatibility],
            "format_compatibility": [f.value for f in self.format_compatibility],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Protocol":
        def _enum_safe(enum_cls, value, default):
            if value is None:
                return default
            try:
                return enum_cls(value)
            except ValueError:
                return default

        return cls(
            id=data["id"],
            protocol_type=_enum_safe(ProtocolType, data.get("protocol_type"), ProtocolType.CUSTOM),
            archetype=data.get("archetype", ""),
            business_logic=data.get("business_logic", ""),
            application=data.get("application", ""),
            narrative=data.get("narrative", ""),
            business_translation=data.get("business_translation", ""),
            dimensions=[Dimension.from_dict(d) for d in data.get("dimensions", [])],
            vector_entry=data.get("vector_entry", {}),
            risk_categories=[
                _enum_safe(RiskCategory, r, RiskCategory.TRANSFORMATION)
                for r in data.get("risk_categories", [])
            ],
            themes=data.get("themes", []),
            tone_compatibility=[
                _enum_safe(ToneType, t, ToneType.PHILOSOPHICAL)
                for t in data.get("tone_compatibility", [])
            ],
            format_compatibility=[
                _enum_safe(FormatType, f, FormatType.PODCAST_MONOLOGUE)
                for f in data.get("format_compatibility", [])
            ],
        )

    def compute_cache_key(self) -> str:
        """Generate a deterministic cache key for this protocol."""
        content = f"{self.id}:{self.archetype}:{self.business_logic}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class Universe:
    """
    A comic universe containing characters, arcs, and protocols.
    """

    id: str
    name: str
    universe_type: UniverseType
    description: str
    themes: List[str]
    visual_motifs: List[str]
    moral_framework: str  # The ethical/philosophical basis
    tone: ToneType
    character_ids: List[str] = field(default_factory=list)
    arc_ids: List[str] = field(default_factory=list)
    protocol_ids: List[str] = field(default_factory=list)

    # For IP/safety considerations
    is_public_domain: bool = False
    requires_abstraction: bool = True  # Whether to use generic terms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "universe_type": self.universe_type.value,
            "description": self.description,
            "themes": self.themes,
            "visual_motifs": self.visual_motifs,
            "moral_framework": self.moral_framework,
            "tone": self.tone.value,
            "character_ids": self.character_ids,
            "arc_ids": self.arc_ids,
            "protocol_ids": self.protocol_ids,
            "is_public_domain": self.is_public_domain,
            "requires_abstraction": self.requires_abstraction,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Universe":
        return cls(
            id=data["id"],
            name=data["name"],
            universe_type=UniverseType(data.get("universe_type", "superhero")),
            description=data.get("description", ""),
            themes=data.get("themes", []),
            visual_motifs=data.get("visual_motifs", []),
            moral_framework=data.get("moral_framework", ""),
            tone=ToneType(data.get("tone", "hopeful")),
            character_ids=data.get("character_ids", []),
            arc_ids=data.get("arc_ids", []),
            protocol_ids=data.get("protocol_ids", []),
            is_public_domain=data.get("is_public_domain", False),
            requires_abstraction=data.get("requires_abstraction", True),
        )


# =============================================================================
# METAPHOR MAPPING & GENERATION
# =============================================================================


@dataclass
class MappingElement:
    """A single mapping between real-world and comic concepts."""

    real_world: str
    comic_analog: str
    explanation: str
    confidence: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "real_world": self.real_world,
            "comic_analog": self.comic_analog,
            "explanation": self.explanation,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MappingElement":
        return cls(
            real_world=data["real_world"],
            comic_analog=data["comic_analog"],
            explanation=data.get("explanation", ""),
            confidence=data.get("confidence", 0.8),
        )


@dataclass
class MetaphorMapping:
    """
    The core mapping between a real-world topic and comic metaphor.
    This is the primary output of the metaphor engine.
    """

    id: str
    topic: str  # User's input topic
    domain: str  # e.g., "startups", "mental_health"
    target_format: FormatType
    target_tone: ToneType

    # Selected comic elements
    protocol_id: str
    core_tension: str  # What conflict/struggle is being mapped
    target_emotion: str  # Desired emotional response

    # Optional comic elements
    arc_id: Optional[str] = None
    universe_id: Optional[str] = None

    # The actual mapping
    mappings: List[MappingElement] = field(default_factory=list)

    # Structural mapping
    narrative_pattern: str = ""  # e.g., "hero's journey"
    beat_structure: List[str] = field(default_factory=list)

    # Quality signals (from codex engine)
    trueness_score: float = 0.0
    flow_score: float = 0.0
    pcs_score: float = 0.0
    overall_fit: float = 0.0

    # TAP integration
    tap_weights: Dict[str, float] = field(default_factory=dict)
    tap_score: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    generation_source: str = ""  # Which model/prompt generated this

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "domain": self.domain,
            "target_format": self.target_format.value,
            "target_tone": self.target_tone.value,
            "protocol_id": self.protocol_id,
            "arc_id": self.arc_id,
            "universe_id": self.universe_id,
            "core_tension": self.core_tension,
            "target_emotion": self.target_emotion,
            "mappings": [m.to_dict() for m in self.mappings],
            "narrative_pattern": self.narrative_pattern,
            "beat_structure": self.beat_structure,
            "trueness_score": self.trueness_score,
            "flow_score": self.flow_score,
            "pcs_score": self.pcs_score,
            "overall_fit": self.overall_fit,
            "tap_weights": self.tap_weights,
            "tap_score": self.tap_score,
            "created_at": self.created_at.isoformat(),
            "generation_source": self.generation_source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetaphorMapping":
        return cls(
            id=data["id"],
            topic=data["topic"],
            domain=data.get("domain", ""),
            target_format=FormatType(data.get("target_format", "podcast_monologue")),
            target_tone=ToneType(data.get("target_tone", "hopeful")),
            protocol_id=data["protocol_id"],
            arc_id=data.get("arc_id"),
            universe_id=data.get("universe_id"),
            core_tension=data.get("core_tension", ""),
            target_emotion=data.get("target_emotion", ""),
            mappings=[MappingElement.from_dict(m) for m in data.get("mappings", [])],
            narrative_pattern=data.get("narrative_pattern", ""),
            beat_structure=data.get("beat_structure", []),
            trueness_score=data.get("trueness_score", 0.0),
            flow_score=data.get("flow_score", 0.0),
            pcs_score=data.get("pcs_score", 0.0),
            overall_fit=data.get("overall_fit", 0.0),
            tap_weights=data.get("tap_weights", {}),
            tap_score=data.get("tap_score", 0.0),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.utcnow(),
            generation_source=data.get("generation_source", ""),
        )

    def compute_cache_key(self) -> str:
        """Generate deterministic cache key for this mapping request."""
        content = f"{self.topic}:{self.target_format.value}:{self.target_tone.value}:{self.protocol_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class GenerationContext:
    """
    Full context for generating narrative content.
    Passed to the narrative generator.
    """

    mapping: MetaphorMapping
    protocol: Protocol
    arc: Optional[Arc] = None
    universe: Optional[Universe] = None

    # Style constraints
    word_count_target: int = 1000
    pov: str = "second"  # first, second, third
    style_notes: List[str] = field(default_factory=list)

    # Content constraints
    avoid_topics: List[str] = field(default_factory=list)
    required_elements: List[str] = field(default_factory=list)

    # Previous generations for continuity
    previous_outputs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mapping": self.mapping.to_dict(),
            "protocol": self.protocol.to_dict(),
            "arc": self.arc.to_dict() if self.arc else None,
            "universe": self.universe.to_dict() if self.universe else None,
            "word_count_target": self.word_count_target,
            "pov": self.pov,
            "style_notes": self.style_notes,
            "avoid_topics": self.avoid_topics,
            "required_elements": self.required_elements,
            "previous_outputs": self.previous_outputs,
        }


# =============================================================================
# OUTPUT MODELS
# =============================================================================


@dataclass
class OutlineBeat:
    """A single beat in a narrative outline."""

    number: int
    title: str
    description: str
    comic_reference: str  # What comic moment this maps to
    word_count_target: int = 100
    key_points: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "comic_reference": self.comic_reference,
            "word_count_target": self.word_count_target,
            "key_points": self.key_points,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutlineBeat":
        return cls(
            number=data["number"],
            title=data["title"],
            description=data.get("description", ""),
            comic_reference=data.get("comic_reference", ""),
            word_count_target=data.get("word_count_target", 100),
            key_points=data.get("key_points", []),
        )


@dataclass
class NarrativeOutline:
    """A complete outline for generated content."""

    mapping_id: str
    format_type: FormatType
    title: str
    hook: str  # Opening hook
    beats: List[OutlineBeat]
    conclusion: str
    total_word_count: int = 0
    story: str = ""  # The comic narrative driving the piece
    turn: str = ""  # The midpoint insight/lesson

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "format_type": self.format_type.value,
            "title": self.title,
            "hook": self.hook,
            "beats": [b.to_dict() for b in self.beats],
            "conclusion": self.conclusion,
            "total_word_count": self.total_word_count,
            "story": self.story,
            "turn": self.turn,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NarrativeOutline":
        return cls(
            mapping_id=data["mapping_id"],
            format_type=FormatType(data.get("format_type", "podcast_monologue")),
            title=data["title"],
            hook=data.get("hook", ""),
            beats=[OutlineBeat.from_dict(b) for b in data.get("beats", [])],
            conclusion=data.get("conclusion", ""),
            total_word_count=data.get("total_word_count", 0),
            story=data.get("story", ""),
            turn=data.get("turn", ""),
        )


@dataclass
class NarrativeOutput:
    """
    The final generated narrative content.
    """

    id: str
    mapping_id: str
    outline_id: Optional[str] = None
    format_type: FormatType = FormatType.PODCAST_MONOLOGUE

    # Content
    title: str = ""
    content: str = ""  # The full generated text
    sections: List[Dict[str, str]] = field(default_factory=list)  # Named sections

    # Metadata
    word_count: int = 0
    generation_model: str = ""
    generation_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Quality scores
    codex_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "mapping_id": self.mapping_id,
            "outline_id": self.outline_id,
            "format_type": self.format_type.value,
            "title": self.title,
            "content": self.content,
            "sections": self.sections,
            "word_count": self.word_count,
            "generation_model": self.generation_model,
            "generation_time_ms": self.generation_time_ms,
            "created_at": self.created_at.isoformat(),
            "codex_scores": self.codex_scores,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NarrativeOutput":
        return cls(
            id=data["id"],
            mapping_id=data["mapping_id"],
            outline_id=data.get("outline_id"),
            format_type=FormatType(data.get("format_type", "podcast_monologue")),
            title=data.get("title", ""),
            content=data.get("content", ""),
            sections=data.get("sections", []),
            word_count=data.get("word_count", 0),
            generation_model=data.get("generation_model", ""),
            generation_time_ms=data.get("generation_time_ms", 0),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.utcnow(),
            codex_scores=data.get("codex_scores", {}),
        )


@dataclass
class Explanation:
    """
    Plain-language explanation of a metaphor mapping.
    """

    mapping_id: str
    audience: str  # Who this explanation is for
    tone: ToneType

    # Content
    summary: str  # One-line summary
    detailed_explanation: str  # Full explanation
    key_takeaways: List[str] = field(default_factory=list)

    # The "translation" back to real life
    life_application: str = ""
    action_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "audience": self.audience,
            "tone": self.tone.value,
            "summary": self.summary,
            "detailed_explanation": self.detailed_explanation,
            "key_takeaways": self.key_takeaways,
            "life_application": self.life_application,
            "action_items": self.action_items,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Explanation":
        return cls(
            mapping_id=data["mapping_id"],
            audience=data.get("audience", "general"),
            tone=ToneType(data.get("tone", "hopeful")),
            summary=data.get("summary", ""),
            detailed_explanation=data.get("detailed_explanation", ""),
            key_takeaways=data.get("key_takeaways", []),
            life_application=data.get("life_application", ""),
            action_items=data.get("action_items", []),
        )


# =============================================================================
# BENCHMARK & METRICS
# =============================================================================


@dataclass
class PhaseMetrics:
    """Metrics for a single pipeline phase."""

    phase_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: int
    cache_hit_rate: float = 0.0
    tokens_used: int = 0
    memory_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_name": self.phase_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "cache_hit_rate": self.cache_hit_rate,
            "tokens_used": self.tokens_used,
            "memory_mb": self.memory_mb,
        }


@dataclass
class BenchmarkResult:
    """
    Complete benchmark result for a metaphor engine run.
    Integrates with Cheetah v3 tool_runs format.
    """

    id: str
    scenario_id: str
    timestamp: datetime

    # Input summary
    input_topic: str
    input_format: FormatType
    input_tone: ToneType

    # Output summary
    output_mapping_id: Optional[str] = None
    output_narrative_id: Optional[str] = None

    # Per-phase metrics
    phase_metrics: List[PhaseMetrics] = field(default_factory=list)

    # Aggregate metrics
    total_duration_ms: int = 0
    total_tokens: int = 0
    cache_hit_rate: float = 0.0

    # Quality scores
    codex_scores: Dict[str, float] = field(default_factory=dict)
    tap_score: float = 0.0

    # Status
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "timestamp": self.timestamp.isoformat(),
            "input_topic": self.input_topic,
            "input_format": self.input_format.value,
            "input_tone": self.input_tone.value,
            "output_mapping_id": self.output_mapping_id,
            "output_narrative_id": self.output_narrative_id,
            "phase_metrics": [p.to_dict() for p in self.phase_metrics],
            "total_duration_ms": self.total_duration_ms,
            "total_tokens": self.total_tokens,
            "cache_hit_rate": self.cache_hit_rate,
            "codex_scores": self.codex_scores,
            "tap_score": self.tap_score,
            "success": self.success,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkResult":
        return cls(
            id=data["id"],
            scenario_id=data["scenario_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            input_topic=data["input_topic"],
            input_format=FormatType(data.get("input_format", "podcast_monologue")),
            input_tone=ToneType(data.get("input_tone", "hopeful")),
            output_mapping_id=data.get("output_mapping_id"),
            output_narrative_id=data.get("output_narrative_id"),
            phase_metrics=[],  # Would need PhaseMetrics.from_dict
            total_duration_ms=data.get("total_duration_ms", 0),
            total_tokens=data.get("total_tokens", 0),
            cache_hit_rate=data.get("cache_hit_rate", 0.0),
            codex_scores=data.get("codex_scores", {}),
            tap_score=data.get("tap_score", 0.0),
            success=data.get("success", True),
            error_message=data.get("error_message", ""),
        )


# =============================================================================
# TAP INTEGRATION
# =============================================================================


@dataclass
class TAPMetric:
    """A single TAP (10-metric) measurement."""

    name: str
    weight: float
    raw_value: float
    normalized_value: float  # 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "weight": self.weight,
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
        }


@dataclass
class TAPScorecard:
    """
    Complete TAP scorecard for a metaphor/output.
    Integrates with IHS_* CSV scoring systems.
    """

    entity_id: str  # What this scores (mapping, output, etc.)
    entity_type: str  # "mapping", "output", "protocol"
    metrics: List[TAPMetric] = field(default_factory=list)
    weighted_total: float = 0.0
    percentile: float = 0.0  # Compared to historical scores

    def compute_weighted_total(self) -> float:
        """Calculate weighted sum of metrics."""
        if not self.metrics:
            return 0.0
        total_weight = sum(m.weight for m in self.metrics)
        if total_weight == 0:
            return 0.0
        self.weighted_total = (
            sum(m.weight * m.normalized_value for m in self.metrics) / total_weight
        )
        return self.weighted_total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "metrics": [m.to_dict() for m in self.metrics],
            "weighted_total": self.weighted_total,
            "percentile": self.percentile,
        }


# =============================================================================
# KNOWLEDGE BASE
# =============================================================================


@dataclass
class KnowledgeBase:
    """
    Container for the full metaphor knowledge base.
    This is the top-level data structure loaded by the engine.
    """

    universes: Dict[str, Universe] = field(default_factory=dict)
    characters: Dict[str, Character] = field(default_factory=dict)
    arcs: Dict[str, Arc] = field(default_factory=dict)
    protocols: Dict[str, Protocol] = field(default_factory=dict)
    tropes: Dict[str, Trope] = field(default_factory=dict)

    # Metadata
    version: str = "0.1.0"
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "universes": {k: v.to_dict() for k, v in self.universes.items()},
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "arcs": {k: v.to_dict() for k, v in self.arcs.items()},
            "protocols": {k: v.to_dict() for k, v in self.protocols.items()},
            "tropes": {k: v.to_dict() for k, v in self.tropes.items()},
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
        }

    def save(self, path: str) -> None:
        """Save knowledge base to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "KnowledgeBase":
        """Load knowledge base from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        kb = cls(
            version=data.get("version", "0.1.0"),
            last_updated=datetime.fromisoformat(data["last_updated"])
            if "last_updated" in data
            else datetime.utcnow(),
        )

        for uid, udata in data.get("universes", {}).items():
            kb.universes[uid] = Universe.from_dict(udata)

        for cid, cdata in data.get("characters", {}).items():
            kb.characters[cid] = Character.from_dict(cdata)

        for aid, adata in data.get("arcs", {}).items():
            kb.arcs[aid] = Arc.from_dict(adata)

        for pid, pdata in data.get("protocols", {}).items():
            kb.protocols[pid] = Protocol.from_dict(pdata)

        for tid, tdata in data.get("tropes", {}).items():
            kb.tropes[tid] = Trope.from_dict(tdata)

        return kb

    def get_stats(self) -> Dict[str, int]:
        """Get counts of all entities."""
        return {
            "universes": len(self.universes),
            "characters": len(self.characters),
            "arcs": len(self.arcs),
            "protocols": len(self.protocols),
            "tropes": len(self.tropes),
        }

    def __getitem__(self, key):
        """Support both dict and list access"""
        if isinstance(key, str):
            return self.protocols[key]
        elif isinstance(key, int):
            return list(self.protocols.values())[key]
        elif isinstance(key, slice):
            return list(self.protocols.values())[key]
        else:
            raise TypeError(f"Invalid key type: {type(key)}")

    def __len__(self):
        return len(self.protocols)

    def __iter__(self):
        return iter(self.protocols.values())

