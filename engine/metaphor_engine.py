"""
Metaphor Engine
===============

Builds rich metaphor mappings by combining semantic protocol search with
domain heuristics. The engine retrieves candidate protocols from the index,
scores them against user intent (format, tone, themes), and constructs a
`MetaphorMapping` that downstream stages (codex scoring, narrative generation)
can consume.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from schema import (
    FormatType,
    MappingElement,
    MetaphorMapping,
    Protocol,
    RiskCategory,
    ToneType,
)


@dataclass(frozen=True)
class ProtocolCandidate:
    """Container that captures ranking details for a protocol option."""

    protocol: Protocol
    similarity: float
    tone_fit: float
    format_fit: float
    theme_alignment: float
    risk_alignment: float
    blended_score: float


class MetaphorEngine:
    """Public facade for generating metaphor mappings."""

    def __init__(self, index: Any, codex_adapter: Optional[Any] = None) -> None:
        self.index = index
        self.codex_adapter = codex_adapter

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def generate_mapping(
        self,
        topic: str,
        target_format: FormatType,
        target_tone: ToneType,
        constraints: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> MetaphorMapping:
        """
        Produce the highest scoring mapping for the supplied topic.

        Args:
            topic: User request or problem to map into comic logic.
            target_format: Desired output format.
            target_tone: Desired narrative tone.
            constraints: Optional knobs (exclude lists, risk preferences).
            top_k: How many candidates to evaluate from semantic search.

        Returns:
            A populated MetaphorMapping, optionally enriched by codex scoring.
        """
        constraints = constraints or {}

        candidates = self.generate_candidates(
            topic=topic,
            target_format=target_format,
            target_tone=target_tone,
            constraints=constraints,
            top_k=top_k,
        )
        if not candidates:
            raise ValueError(
                "MetaphorEngine: no viable protocols were found for this topic."
            )

        best = candidates[0]
        mapping = self._build_mapping(
            topic=topic,
            protocol=best.protocol,
            target_format=target_format,
            target_tone=target_tone,
            similarity=best.similarity,
            constraints=constraints,
        )

        if self.codex_adapter:
            mapping = self.codex_adapter.score_mapping(mapping, best.protocol)

        return mapping

    def generate_candidates(
        self,
        topic: str,
        target_format: FormatType,
        target_tone: ToneType,
        constraints: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[ProtocolCandidate]:
        """
        Retrieve and score protocol options for debugging or custom selection.

        Returns:
            A list of ProtocolCandidate objects, sorted by blended score (desc).
        """
        constraints = constraints or {}
        raw_candidates = self._query_index(topic, top_k=max(3, top_k * 2))
        filtered = self._filter_candidates(raw_candidates, constraints)

        scored: List[ProtocolCandidate] = []
        for protocol, similarity in filtered:
            candidate = self._score_candidate(
                topic=topic,
                protocol=protocol,
                similarity=similarity,
                target_format=target_format,
                target_tone=target_tone,
                constraints=constraints,
            )
            if candidate.blended_score > 0:
                scored.append(candidate)

        scored.sort(key=lambda c: c.blended_score, reverse=True)
        return scored

    # ------------------------------------------------------------------ #
    # Candidate retrieval & scoring
    # ------------------------------------------------------------------ #
    def _query_index(self, topic: str, top_k: int) -> List[Tuple[Protocol, float]]:
        """
        Ask the index for relevant protocols.

        Supports indexes that can optionally return similarity scores.
        If scores are unavailable the similarity defaults to 0.
        """
        results: List[Any] = []
        try:
            results = self.index.search_protocols(
                topic, top_k=top_k, return_scores=True
            )
        except TypeError:
            # Older index signature without return_scores flag.
            results = self.index.search_protocols(topic, top_k=top_k)

        formatted: List[Tuple[Protocol, float]] = []
        for item in results:
            if isinstance(item, tuple) and len(item) == 2:
                protocol, similarity = item
                formatted.append((protocol, float(similarity)))
            else:
                formatted.append((item, 0.0))
        return formatted

    def _filter_candidates(
        self,
        candidates: Sequence[Tuple[Protocol, float]],
        constraints: Dict[str, Any],
    ) -> List[Tuple[Protocol, float]]:
        exclude_ids = {
            pid.lower()
            for pid in constraints.get("exclude_protocol_ids", [])
            if isinstance(pid, str)
        }
        min_similarity = float(constraints.get("min_similarity", 0.0))

        filtered: List[Tuple[Protocol, float]] = []
        for protocol, similarity in candidates:
            if protocol.id.lower() in exclude_ids:
                continue
            if similarity < min_similarity:
                continue
            filtered.append((protocol, similarity))
        return filtered

    def _score_candidate(
        self,
        topic: str,
        protocol: Protocol,
        similarity: float,
        target_format: FormatType,
        target_tone: ToneType,
        constraints: Dict[str, Any],
    ) -> ProtocolCandidate:
        tone_fit = self._compatibility_score(target_tone, protocol.tone_compatibility)
        format_fit = self._compatibility_score(
            target_format, protocol.format_compatibility
        )
        theme_alignment = self._theme_alignment(topic, protocol.themes)
        risk_alignment = self._risk_alignment(
            protocol.risk_categories,
            constraints.get("preferred_risk_categories"),
        )

        # Allow external override of scoring weights via constraints["scoring_weights"]
        # Merge with defaults and normalize to sum to 1.0
        default_weights = {
            "similarity": 0.55,
            "tone": 0.15,
            "format": 0.15,
            "theme": 0.10,
            "risk": 0.05,
        }
        incoming = constraints.get("scoring_weights", {})
        if not isinstance(incoming, dict):
            incoming = {}
        weights = {
            **default_weights,
            **{k: float(v) for k, v in incoming.items() if k in default_weights},
        }
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {k: v / total_w for k, v in weights.items()}

        blended_score = (
            similarity * weights["similarity"]
            + tone_fit * weights["tone"]
            + format_fit * weights["format"]
            + theme_alignment * weights["theme"]
            + risk_alignment * weights["risk"]
        )

        return ProtocolCandidate(
            protocol=protocol,
            similarity=similarity,
            tone_fit=tone_fit,
            format_fit=format_fit,
            theme_alignment=theme_alignment,
            risk_alignment=risk_alignment,
            blended_score=blended_score,
        )

    # ------------------------------------------------------------------ #
    # Mapping construction
    # ------------------------------------------------------------------ #
    def _build_mapping(
        self,
        topic: str,
        protocol: Protocol,
        target_format: FormatType,
        target_tone: ToneType,
        similarity: float,
        constraints: Dict[str, Any],
    ) -> MetaphorMapping:
        mapping = MetaphorMapping(
            id=self._generate_mapping_id(topic, protocol.id),
            topic=topic,
            domain=self._infer_domain(topic),
            target_format=target_format,
            target_tone=target_tone,
            protocol_id=protocol.id,
            core_tension=self._derive_core_tension(topic, protocol),
            target_emotion=self._infer_emotion(target_tone),
            mappings=self._build_mapping_elements(topic, protocol, similarity),
            narrative_pattern=self._infer_narrative_pattern(protocol),
            beat_structure=self._build_beat_structure(protocol, constraints),
            generation_source="metaphor_engine_v2",
        )

        mapping.tap_weights = {
            "similarity": round(similarity, 3),
            "tone_fit": round(
                self._compatibility_score(target_tone, protocol.tone_compatibility), 3
            ),
            "format_fit": round(
                self._compatibility_score(target_format, protocol.format_compatibility),
                3,
            ),
        }
        return mapping

    def _build_mapping_elements(
        self,
        topic: str,
        protocol: Protocol,
        similarity: float,
    ) -> List[MappingElement]:
        """Translate protocol structure into mapping beats."""
        elements: List[MappingElement] = []

        for dimension in protocol.dimensions[:3]:
            explanation = (
                f"Use the {dimension.title} lens—{dimension.analysis}—to reinterpret "
                f"'{topic}' through the comic conflict."
            )
            elements.append(
                MappingElement(
                    real_world=topic,
                    comic_analog=dimension.title,
                    explanation=explanation,
                    confidence=min(0.95, 0.6 + similarity * 0.35),
                )
            )

        if not elements:
            explanation = (
                f"Borrow the protocol logic ({protocol.business_logic.strip()}) to reframe "
                f"'{topic}' as a comic confrontation."
            )
            elements.append(
                MappingElement(
                    real_world=topic,
                    comic_analog=protocol.archetype or protocol.id,
                    explanation=explanation,
                    confidence=min(0.9, 0.55 + similarity * 0.4),
                )
            )

        if protocol.application and len(elements) < 3:
            elements.append(
                MappingElement(
                    real_world="Implementation trigger",
                    comic_analog="Protocol application",
                    explanation=protocol.application,
                    confidence=0.6,
                )
            )

        return elements

    def _build_beat_structure(
        self,
        protocol: Protocol,
        constraints: Dict[str, Any],
    ) -> List[str]:
        override = constraints.get("beat_override")
        if override:
            return list(override)

        beats = [
            "Hook: Surface the user's immediate tension.",
            f"Mirror: Introduce {protocol.archetype or 'the comic archetype'} and the parallel stakes.",
            "Shift: Translate the comic resolution into a real-world strategic insight.",
            "Action: Close with concrete experiments or rituals borrowed from the protocol.",
        ]

        if protocol.themes:
            beats.insert(
                2,
                f"Theme bridge: Highlight how the theme '{protocol.themes[0]}' manifests in both worlds.",
            )
        return beats

    # ------------------------------------------------------------------ #
    # Helper methods
    # ------------------------------------------------------------------ #
    def _generate_mapping_id(self, topic: str, protocol_id: str) -> str:
        digest = hashlib.sha256(f"{topic}:{protocol_id}".encode("utf-8")).hexdigest()
        return f"mapping_{digest[:10]}"

    def _infer_domain(self, topic: str) -> str:
        topic_lower = topic.lower()
        if any(
            keyword in topic_lower
            for keyword in ("team", "culture", "manager", "leader", "org")
        ):
            return "organizational_dynamics"
        if any(
            keyword in topic_lower
            for keyword in ("health", "stress", "burnout", "wellbeing", "mental")
        ):
            return "wellness"
        if any(
            keyword in topic_lower
            for keyword in ("customer", "product", "market", "brand", "gtm")
        ):
            return "go_to_market"
        return "general_strategy"

    def _derive_core_tension(self, topic: str, protocol: Protocol) -> str:
        narrative = (protocol.narrative or protocol.business_translation or "").strip()
        summary = narrative.split(".")[0]
        return f"Holding '{topic}' in tension with the comic conflict: {summary}"

    def _infer_emotion(self, tone: ToneType) -> str:
        tone_to_emotion = {
            ToneType.HOPEFUL: "optimism",
            ToneType.GRITTY: "resilience",
            ToneType.CAUTIONARY: "vigilance",
            ToneType.PHILOSOPHICAL: "insight",
            ToneType.COMEDIC: "levity",
            ToneType.DARK: "urgency",
            ToneType.INSPIRATIONAL: "ambition",
            ToneType.ACTION: "momentum",
        }
        return tone_to_emotion.get(tone, "transformation")

    def _infer_narrative_pattern(self, protocol: Protocol) -> str:
        keywords = " ".join(protocol.themes).lower()
        if "identity" in keywords:
            return "secret_identity_reveal"
        if "control" in keywords or "power" in keywords:
            return "power_balance"
        if "redemption" in keywords:
            return "redemption_arc"
        return "hero_journey"

    def _compatibility_score(
        self,
        target_value: Any,
        compatible_values: Sequence[Any],
    ) -> float:
        if not compatible_values:
            return 0.6  # Neutral when metadata is missing.
        return 1.0 if target_value in compatible_values else 0.25

    def _theme_alignment(self, topic: str, themes: Sequence[str]) -> float:
        if not themes:
            return 0.4
        topic_tokens = set(topic.lower().split())
        overlap = sum(1 for theme in themes if theme.lower() in topic_tokens)
        return min(1.0, 0.4 + 0.2 * overlap)

    def _risk_alignment(
        self,
        protocol_risks: Sequence[RiskCategory],
        preferred_risks: Optional[Sequence[str]],
    ) -> float:
        if not preferred_risks:
            return 0.5
        preferred = {risk.lower() for risk in preferred_risks if isinstance(risk, str)}
        matches = sum(
            1
            for risk in protocol_risks
            if (risk.value if hasattr(risk, "value") else str(risk)).lower()
            in preferred
        )
        return min(1.0, 0.3 + 0.35 * matches)


if __name__ == "__main__":
    from index import MetaphorIndex  # Local import to avoid circular dependency.

    engine = MetaphorEngine(MetaphorIndex())
    demo_mapping = engine.generate_mapping(
        topic="Scaling a burnt-out product team without losing culture",
        target_format=FormatType.PODCAST_MONOLOGUE,
        target_tone=ToneType.HOPEFUL,
    )
    print(
        f"[MetaphorEngine] Generated mapping {demo_mapping.id} using protocol {demo_mapping.protocol_id} "
        f"(Trueness={demo_mapping.trueness_score:.3f})"
    )

    def generate(self, topic: str, top_k: int = 3):
        """Generate metaphor mapping for topic

        Args:
            topic: Topic to find metaphor for
            top_k: Number of candidate protocols to consider

        Returns:
            Best metaphor mapping
        """
        # Use existing logic or create new mapping
        from engine.schema import MetaphorMapping
        import hashlib

        # Generate mapping ID
        mapping_id = "mapping_" + hashlib.md5(topic.encode()).hexdigest()[:10]

        # Find best protocol (simplified - use first one for now)
        protocol_id = list(self.knowledge_base.protocols.keys())[0]
        protocol = self.knowledge_base.protocols[protocol_id]

        mapping = MetaphorMapping(
            mapping_id=mapping_id,
            topic=topic,
            protocol_id=protocol_id,
            protocol_name=protocol.name,
            relevance_score=0.8
        )

        return mapping

