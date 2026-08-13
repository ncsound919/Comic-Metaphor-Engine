"""
Explainers Module
=================

Turns a metaphor mapping into a plain-language learning experience:
a short summary, a detailed explanation, key takeaways, and concrete
action items. This is the "learning mechanism" of the engine — it makes
every mapping teachable.

Public API:
    explain_mapping(mapping, protocol, audience=None, tone=None) -> Explanation
    generate_summary(mapping, protocol) -> str
    generate_lesson(mapping, protocol) -> Dict[str, Any]
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

from schema import (
    Explanation,
    FormatType,
    MetaphorMapping,
    Protocol,
    ToneType,
)

# Domain-specific action templates keyed off the mapping's inferred domain.
_DOMAIN_ACTIONS = {
    "organizational_dynamics": [
        "Run a team retro that names the 'villain' of the current quarter — one systemic issue your org keeps losing to.",
        "Map your org chart against the protocol's factions and ask who is being left to absorb the collateral.",
        "Draft a one-page 'origin story' for your team so new members understand the operating conflict.",
    ],
    "wellness": [
        "Keep a 3-day log of the situations that trigger your version of this comic conflict, then look for the pattern.",
        "Pick one coping ritual from the lesson and commit to it for two weeks.",
        "Write the 'last panel' of your current arc — what you want the resolution to look like — and read it weekly.",
    ],
    "go_to_market": [
        "Write the customer story that parallels the protocol's narrative and use it as your next pitch opening.",
        "Identify which of your positioning choices is the 'binary snap' — the one big lever you're betting the launch on.",
        "Interview three customers through the lens of the protocol and record what they say without editing it.",
    ],
    "leadership": [
        "Name the decision you are avoiding, then ask what the comic version of that leader would do differently.",
        "Delegate one decision this week using the protocol's core tension as your tie-breaker.",
        "Schedule a 30-minute 'watchtower' session to observe your team without intervening.",
    ],
    "general_strategy": [
        "Write the metaphor in one sentence and challenge your team to find where it breaks.",
        "Use the protocol's 'next issue' ending to write three possible futures for the current situation.",
        "Share the mapping with a peer who doesn't know your context and ask what they hear.",
    ],
}

_EMOTION_HOOK = {
    "optimism": "The good news is this conflict has a resolution arc.",
    "resilience": "The uncomfortable truth is that this pressure can be channeled.",
    "vigilance": "The warning here is real, but forewarned is forearmed.",
    "insight": "Look closely and this story explains more than the surface plot.",
    "levity": "Zoom out far enough and even this mess has a punchline.",
    "urgency": "Time is the scarcest resource in this story.",
    "ambition": "The stakes are higher than you think — that's the point.",
    "transformation": "Change is already underway; the question is who steers it.",
}


def _slug(text: str, limit: int = 60) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", text).strip()
    return " ".join(cleaned.split())[:limit]


def _domain_for(mapping: MetaphorMapping) -> str:
    if mapping.domain and mapping.domain != "general_strategy":
        return mapping.domain
    lowered = mapping.topic.lower()
    if any(k in lowered for k in ("team", "culture", "manager", "leader", "org", "ceo")):
        return "leadership"
    if any(k in lowered for k in ("health", "stress", "burnout", "wellbeing", "mental")):
        return "wellness"
    if any(k in lowered for k in ("customer", "product", "market", "brand", "launch")):
        return "go_to_market"
    return "general_strategy"


def _takeaways(mapping: MetaphorMapping, protocol: Protocol) -> List[str]:
    takeaways: List[str] = []
    for element in mapping.mappings:
        if element.explanation and len(takeaways) < 3:
            takeaways.append(element.explanation.rstrip(".") + ".")
    if protocol.business_logic:
        takeaways.append(f"The protocol for this is: {_slug(protocol.business_logic, 110)}.")
    return takeaways or [
        "The comic conflict mirrors a real structural tension worth naming."
    ]


def _action_items(mapping: MetaphorMapping) -> List[str]:
    return list(_DOMAIN_ACTIONS.get(_domain_for(mapping), _DOMAIN_ACTIONS["general_strategy"]))


def _detailed_explanation(mapping: MetaphorMapping, protocol: Protocol) -> str:
    parts: List[str] = []
    if protocol.narrative:
        parts.append(f"In the comics, {_slug(protocol.narrative, 260)}")
    if protocol.business_translation:
        parts.append(
            f"Translated to your world: {_slug(protocol.business_translation, 260)}"
        )
    for element in mapping.mappings[:2]:
        if element.explanation:
            parts.append(element.explanation.rstrip(".") + ".")
    return " ".join(parts)


def _life_application(mapping: MetaphorMapping, protocol: Protocol) -> str:
    domain = _domain_for(mapping)
    hook = _EMOTION_HOOK.get(mapping.target_emotion, _EMOTION_HOOK["transformation"])
    core = _slug(mapping.core_tension, 140) if mapping.core_tension else protocol.business_logic
    return f"{hook} For your situation — {core} — the practical move is to treat '{mapping.topic}' as a story you are actively writing, not a condition you are stuck in. The comic analogy gives you distance; distance gives you leverage."


def explain_mapping(
    mapping: MetaphorMapping,
    protocol: Protocol,
    audience: str = "general",
    tone: Optional[ToneType] = None,
) -> Explanation:
    """
    Produce a plain-language Explanation for a metaphor mapping.

    Args:
        mapping: The metaphor mapping to explain.
        protocol: The underlying comic protocol (for narrative context).
        audience: Who the explanation is for (e.g. "founder", "team", "student").
        tone: Override tone; defaults to the mapping's target tone.

    Returns:
        A populated Explanation with summary, takeaways, and action items.
    """
    tone = tone or mapping.target_tone
    summary = (
        f"'{mapping.topic}' plays out like {protocol.archetype or protocol.id} — "
        f"the same tension, the same stakes, and the same trap to avoid."
    )
    return Explanation(
        mapping_id=mapping.id,
        audience=audience,
        tone=tone,
        summary=summary,
        detailed_explanation=_detailed_explanation(mapping, protocol),
        key_takeaways=_takeaways(mapping, protocol),
        life_application=_life_application(mapping, protocol),
        action_items=_action_items(mapping),
    )


def generate_summary(mapping: MetaphorMapping, protocol: Protocol) -> str:
    """One-line summary of the mapping."""
    return (
        f"'{mapping.topic}' ≈ {protocol.archetype or protocol.id}: "
        f"the {mapping.target_emotion or 'core'} lesson in one panel."
    )


def generate_lesson(mapping: MetaphorMapping, protocol: Protocol) -> Dict[str, Any]:
    """
    Compact lesson bundle — ideal for the learning UI and spaced repetition.

    Returns a dict with: title, hook, story, translation, takeaways, actions,
    and a stable lesson_id for storage/review tracking.
    """
    lesson_id = "lesson_" + hashlib.sha256(
        f"{mapping.topic}:{mapping.protocol_id}".encode("utf-8")
    ).hexdigest()[:12]
    return {
        "lesson_id": lesson_id,
        "title": f"{_slug(mapping.topic, 50)} — via {protocol.archetype or protocol.id}",
        "hook": _EMOTION_HOOK.get(mapping.target_emotion, "Here's the story behind the strategy."),
        "story": _slug(protocol.narrative, 300) if protocol.narrative else "",
        "translation": _slug(protocol.business_translation, 300)
        if protocol.business_translation
        else "",
        "takeaways": _takeaways(mapping, protocol),
        "actions": _action_items(mapping),
        "tone": mapping.target_tone.value,
        "protocol_id": mapping.protocol_id,
    }


if __name__ == "__main__":
    # Quick smoke test against the current knowledge base.
    from index import MetaphorIndex

    idx = MetaphorIndex()
    engine = __import__("metaphor_engine", fromlist=["MetaphorEngine"]).MetaphorEngine(idx)
    demo = engine.generate_mapping(
        topic="Keeping a scaling team from burning out",
        target_format=FormatType.PODCAST_MONOLOGUE,
        target_tone=ToneType.HOPEFUL,
    )
    proto = idx.get_protocol_by_id(demo.protocol_id)
    explanation = explain_mapping(demo, proto)
    print(explanation.summary)
    for t in explanation.key_takeaways:
        print(f"  - {t}")
