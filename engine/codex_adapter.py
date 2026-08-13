"""
Codex Adapter Module
====================

Integrates the existing codex_engine for scoring metaphor mappings.
Computes Trueness, Flow, PCS, TAP, RPS, CU scores for quality assessment.
"""

import hashlib
from typing import Any, Dict, Optional

from codex_engine import compute_report
from schema import MetaphorMapping, Protocol

from .index import MetaphorIndex


def _calibrate_similarity(raw: float) -> float:
    """
    Map raw MiniLM cosine similarity into a meaningful 0-1 fit scale.

    Raw cosine values for good matches typically land in ~0.15-0.45, so a
    linear/identity mapping would understate fit. This sigmoid-like curve
    centers the useful range: 0.15 -> ~0.4, 0.3 -> ~0.7, 0.45 -> ~0.9.
    """
    if raw <= 0.05:
        return max(0.0, raw * 3.0)
    t = (raw - 0.05) / 0.45
    t = max(0.0, min(1.0, t))
    return round(0.15 + 0.85 * (t ** 0.8), 4)


class CodexAdapter:
    """Adapter for scoring metaphor mappings using the codex engine."""

    def __init__(self, index: Optional[Any] = None):
        self.default_params = {
            "scaler_version": "1.0",
            "params": {"k_trueness": 3.0, "D_max_default": 10.0},
            "thresholds": {
                "PCS": 0.62,
                "Flow": 0.55,
                "Trueness": 0.60,
                "CU": 0.50,
                "RPS": 0.50,
            },
            "scalers": {},  # Use identity scalers by default
        }
        self.index = index

    def score_mapping(
        self, mapping: MetaphorMapping, protocol: Protocol
    ) -> MetaphorMapping:
        """
        Score a metaphor mapping using the codex engine.

        Args:
            mapping: The metaphor mapping to score
            protocol: The associated protocol

        Returns:
            Updated mapping with computed scores
        """
        # Build codex input from mapping and protocol
        codex_input = self._build_codex_input(mapping, protocol)

        # Compute scores using codex engine
        try:
            report_md, audit = compute_report(codex_input)

            # Update mapping with scores
            scores = audit["scores"]
            mapping.trueness_score = scores.get("Trueness", 0.0)
            mapping.flow_score = scores.get("Flow", 0.0)
            mapping.pcs_score = scores.get("PCS", 0.0)
            mapping.tap_score = scores.get("Tap10", 0.0)

            # Overall fit as average of key scores
            key_scores = [
                mapping.trueness_score,
                mapping.flow_score,
                mapping.pcs_score,
                mapping.tap_score,
            ]
            mapping.overall_fit = (
                sum(key_scores) / len(key_scores) if key_scores else 0.0
            )

            # TAP weights (simplified - equal weights for now)
            mapping.tap_weights = {
                "trueness": 0.25,
                "flow": 0.25,
                "pcs": 0.25,
                "tap10": 0.25,
            }

            print(
                f"[OK] Scored mapping {mapping.id}: Trueness={mapping.trueness_score:.3f}, "
                f"Flow={mapping.flow_score:.3f}, PCS={mapping.pcs_score:.3f}, "
                f"TAP={mapping.tap_score:.3f}, Overall={mapping.overall_fit:.3f}"
            )

        except Exception as e:
            print(f"Warning: Failed to score mapping {mapping.id}: {e}")
            # Set default scores
            mapping.trueness_score = 0.5
            mapping.flow_score = 0.5
            mapping.pcs_score = 0.5
            mapping.tap_score = 0.5
            mapping.overall_fit = 0.5

        return mapping

    def _build_codex_input(
        self, mapping: MetaphorMapping, protocol: Protocol
    ) -> Dict[str, Any]:
        """
        Build codex input dictionary from mapping and protocol data.

        Uses heuristics to derive scores from available data.
        In production, this would use more sophisticated analysis.
        """
        # Base structure
        codex_input = self.default_params.copy()

        # Derive Trueness inputs (signal vs baggage vs noise)
        # A: alignment strength (how well topic matches protocol)
        # Use multi-factor alignment score including semantic similarity

        # Factor 1: Word overlap (basic)
        topic_words = set(mapping.topic.lower().split())
        protocol_words = set(
            (protocol.business_logic + protocol.narrative).lower().split()
        )
        overlap = len(topic_words.intersection(protocol_words))
        total_words = len(topic_words.union(protocol_words))
        word_overlap = overlap / total_words if total_words > 0 else 0.0

        # Factor 2: Theme matching (stronger signal)
        theme_matches = sum(
            1.0 for theme in protocol.themes if theme.lower() in mapping.topic.lower()
        )
        theme_score = min(1.0, theme_matches / max(len(protocol.themes), 1))

        # Factor 3: Risk category alignment (if mapping has domain hints)
        domain_keywords = {
            "ownership": ["responsibility", "control", "own", "manage"],
            "identity": ["identity", "trust", "who", "self", "authentic"],
            "control": ["control", "power", "optimize", "manage", "regulate"],
            "avoidance": ["avoid", "escape", "ignore", "defer", "external"],
        }

        risk_score = 0.0
        topic_lower = mapping.topic.lower()
        for risk_cat in protocol.risk_categories:
            category_name = (
                risk_cat.value.lower()
                if hasattr(risk_cat, "value")
                else str(risk_cat).lower()
            )
            keywords = domain_keywords.get(category_name, [])
            if any(kw in topic_lower for kw in keywords):
                risk_score = 1.0
                break

        # Factor 4: Core tension relevance
        tension_score = 0.5  # Default neutral
        if mapping.core_tension:
            tension_words = set(mapping.core_tension.lower().split())
            tension_overlap = len(tension_words.intersection(protocol_words))
            tension_score = min(1.0, tension_overlap / max(len(tension_words), 1) * 2.0)

        # Factor 5: Semantic similarity using embeddings
        query_text = f"{mapping.topic} {mapping.core_tension or ''}".strip()
        if self.index is not None:
            semantic_similarity = self.index.compute_similarity(query_text, protocol)
        else:
            semantic_similarity = word_overlap  # Fallback to lexical overlap
        # MiniLM cosine similarities cluster low (good matches ~0.15-0.45).
        # Calibrate into a meaningful fit scale before mixing into Trueness.
        semantic_fit = _calibrate_similarity(semantic_similarity)

        # Weighted composite: prioritize semantic similarity, then themes and tension
        trueness_a = (
            word_overlap * 0.1
            + theme_score * 0.2
            + risk_score * 0.1
            + tension_score * 0.1
            + semantic_fit * 0.5
        )
        trueness_a = min(1.0, trueness_a)  # Cap at 1.0

        # B: baggage (complexity/overhead)
        # A well-formed protocol is a feature, not a penalty. Four dimensions
        # add structure; only excessive mapping length adds real baggage.
        dimension_baggage = min(0.35, len(protocol.dimensions) * 0.04)
        mapping_baggage = min(0.35, len(mapping.mappings) * 0.05) if mapping.mappings else 0.1
        baggage = min(0.5, (dimension_baggage * 0.5 + mapping_baggage * 0.5))

        # N: noise (unrelated elements)
        # Tone/format mismatch is a mild discount, not a hard floor.
        tone_mismatch = (
            0.0 if mapping.target_tone in protocol.tone_compatibility else 0.12
        )
        format_mismatch = (
            0.0 if mapping.target_format in protocol.format_compatibility else 0.08
        )
        noise = min(0.3, tone_mismatch + format_mismatch)

        codex_input["inputs"] = {
            "Trueness": {"A": trueness_a, "B": baggage, "N": noise}
        }

        # TAP10: Weighted effectiveness (improved)
        # Use protocol dimensions + themes as levers
        levers = []
        lever_weights = []

        # Add dimension-based levers
        for dim in protocol.dimensions[:4]:
            levers.append(dim.title)
            # Weight by dimension analysis richness
            weight = 0.25  # Equal weight for 4 dimensions
            lever_weights.append(weight)

        # Fill remaining slots with themes
        remaining_slots = 10 - len(levers)
        themes_to_use = protocol.themes[:remaining_slots]
        for theme in themes_to_use:
            levers.append(theme)
            lever_weights.append(
                (1.0 - sum(lever_weights)) / max(len(themes_to_use), 1)
            )

        # Normalize weights
        total_weight = sum(lever_weights)
        weights = (
            [w / total_weight for w in lever_weights]
            if total_weight > 0
            else [0.1] * len(levers)
        )

        # Effectiveness based on relevance to topic and tension
        effectiveness = []
        combined_text = (mapping.topic + " " + mapping.core_tension).lower()
        for lever in levers:
            lever_lower = lever.lower()
            # Check for direct match, partial match, or related concepts
            if lever_lower in combined_text:
                effectiveness.append(0.9)
            elif any(word in combined_text for word in lever_lower.split()):
                effectiveness.append(0.7)
            else:
                effectiveness.append(
                    0.4
                )  # Baseline instead of 0.5 to be more conservative

        codex_input["inputs"]["Tap10"] = {"W": weights, "F": effectiveness}

        # Flow: Readiness × inverse drag × resources
        # I: readiness (how prepared/complete the mapping is)
        has_mappings = 1.0 if mapping.mappings else 0.0
        has_beats = 1.0 if mapping.beat_structure else 0.0
        has_narrative_pattern = 1.0 if mapping.narrative_pattern else 0.0
        readiness = 0.3 + (
            has_mappings * 0.3 + has_beats * 0.25 + has_narrative_pattern * 0.15
        )

        # D: drag (complexity/friction)
        beat_drag = len(mapping.beat_structure) if mapping.beat_structure else 3
        dimension_drag = len(protocol.dimensions) * 0.5
        drag = max(1.0, beat_drag + dimension_drag)

        # R: resources (compatibility as resource availability)
        tone_resource = (
            1.0 if mapping.target_tone in protocol.tone_compatibility else 0.3
        )
        format_resource = (
            1.0 if mapping.target_format in protocol.format_compatibility else 0.4
        )
        resources = tone_resource * 0.5 + format_resource * 0.5

        codex_input["inputs"]["Flow"] = {
            "I": readiness,
            "D": drag,
            "D_max": 10,
            "R": resources,
        }

        # PCS: Partner fit (how well format/tone fit the protocol)
        pcs_weights = {"format_fit": 0.4, "tone_fit": 0.3, "theme_fit": 0.3}
        pcs_values = {
            "format_fit": 1.0
            if mapping.target_format in protocol.format_compatibility
            else 0.5,
            "tone_fit": 1.0
            if mapping.target_tone in protocol.tone_compatibility
            else 0.5,
            "theme_fit": trueness_a,  # Reuse alignment
        }

        codex_input["inputs"]["PCS"] = {"weights": pcs_weights, "values": pcs_values}

        # RPS: Rollout priority (simplified)
        codex_input["inputs"]["RPS"] = {
            "S": 0.6,  # Strategic value
            "ROI": 0.7,  # Return on investment
            "PF": 0.8,  # Political feasibility
            "R": 0.2,  # Risk
            "alpha": 0.33,
            "beta": 0.33,
            "gamma": 0.34,
        }

        # CU: Capacity utilization
        codex_input["inputs"]["CU"] = {
            "G": 0.7,  # Goal alignment
            "R": 0.6,  # Resource availability
            "P": 0.8,  # Process capability
        }

        # One-knob sensitivity analysis
        codex_input["inputs"]["one_knob"] = {
            "drivers": ["Trueness.A", "Flow.I", "PCS.values.format_fit"],
            "delta": 0.05,
        }

        return codex_input


def score_metaphor_mapping(
    mapping: MetaphorMapping, protocol: Protocol, index: Optional[MetaphorIndex] = None
) -> MetaphorMapping:
    """
    Convenience function to score a single mapping.

    Args:
        mapping: The mapping to score
        protocol: Associated protocol
        index: Optional index to use for similarity computation

    Returns:
        Scored mapping
    """
    adapter = CodexAdapter(index=index)
    return adapter.score_mapping(mapping, protocol)


if __name__ == "__main__":
    # Test the adapter
    from schema import FormatType, MetaphorMapping, Protocol, ProtocolType, ToneType

    # Create test protocol
    protocol = Protocol(
        id="test_protocol",
        protocol_type=ProtocolType.ARMOR_WARS,
        archetype="Test Archetype",
        business_logic="Test business logic about armor and responsibility",
        application="Strategic analysis",
        narrative="Test narrative",
        business_translation="Translation",
        dimensions=[],
        vector_entry={},
        risk_categories=[],
        themes=["responsibility", "control", "power"],
        tone_compatibility=[ToneType.GRITTY],
        format_compatibility=[FormatType.PODCAST_MONOLOGUE],
    )

    # Create test mapping
    mapping = MetaphorMapping(
        id="test_mapping",
        topic="startup burnout",
        domain="business",
        target_format=FormatType.PODCAST_MONOLOGUE,
        target_tone=ToneType.GRITTY,
        protocol_id="test_protocol",
        core_tension="Burnout vs responsibility",
        target_emotion="empowerment",
    )

    # Score it
    scored = score_metaphor_mapping(mapping, protocol)
    print(f"Scored mapping: overall_fit={scored.overall_fit:.3f}")
