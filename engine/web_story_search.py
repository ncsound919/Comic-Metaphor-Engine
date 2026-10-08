#!/usr/bin/env python3
"""
Web Story Search + Cross-reference
==================================
Deterministic, keyless web search for RELEVANT comic storylines, plus
cross-referencing of a mapped story against the protocol index and web results.

Purpose
-------
The MetaphorEngine maps a topic to the best protocol in the local index. This
module adds two capabilities:

1. WEB SEARCH — query keyless public APIs (Wikipedia MediaWiki, Marvel Fandom)
   for comic storylines relevant to a topic, so the engine can surface stories
   that are NOT in the local index.
2. CROSS-REFERENCE — given a mapped story, find related stories: (a) the nearest
   neighbours in the local FAISS index, and (b) web-discovered storyline titles.

Both are deterministic and fail-soft: a source that errors is skipped, never
crashes the request, and never fabricates a result.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_REST = "https://en.wikipedia.org/w/api.php"
MARVEL_FANDOM_API = "https://marvel.fandom.com/api.php"
HTTP_TIMEOUT = 15  # seconds


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class WebStoryHit:
    """A story discovered via web search."""

    title: str
    url: str = ""
    source: str = ""
    description: str = ""
    relevance: float = 0.0  # 0-1 heuristic score


@dataclass
class StoryCrossRef:
    """Cross-reference result: a mapped story + related stories."""

    primary: str
    primary_protocol_id: Optional[str]
    related_index: List[Dict[str, Any]] = field(default_factory=list)
    related_web: List[WebStoryHit] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Keyless HTTP helpers (fail-soft, deterministic)
# ---------------------------------------------------------------------------


def _fetch(url: str) -> Optional[Dict[str, Any]]:
    """Fetch a JSON URL with timeout; returns None on any error."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "OverlayComicMetaphorEngine/2.0 (research metaphor lookup)",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        return None


def _clean(text: str) -> str:
    """Strip wiki markup / HTML tags for a plain summary."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Wikipedia MediaWiki search (keyless, deterministic)
# ---------------------------------------------------------------------------

def search_wikipedia(query: str, limit: int = 5) -> List[WebStoryHit]:
    """Full-text search Wikipedia for comic storylines related to a query."""
    q = urllib.parse.quote(query)
    url = (
        f"{WIKI_API}?action=query&list=search"
        f"&srsearch={q}&format=json&srlimit={limit}"
        "&srnamespace=0"
    )
    data = _fetch(url)
    hits: List[WebStoryHit] = []
    if not data:
        return hits
    for item in (data.get("query", {}).get("search", []) or [])[:limit]:
        hits.append(
            WebStoryHit(
                title=item.get("title", ""),
                url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(item.get('title', '').replace(' ', '_'))}",
                source="wikipedia",
                description=_clean(item.get("snippet", ""))[:300],
                relevance=_relevance(item.get("title", "")),
            )
        )
    return hits


def search_wikipedia_opensearch(query: str, limit: int = 5) -> List[WebStoryHit]:
    """OpenSearch suggestion API — good for catching storyline titles."""
    q = urllib.parse.quote(query)
    url = (
        f"{WIKI_API}?action=opensearch&search={q}&limit={limit}&format=json"
    )
    data = _fetch(url)
    hits: List[WebStoryHit] = []
    if not data or len(data) < 4:
        return hits
    titles, descs, urls = data[1] or [], data[2] or [], data[3] or []
    for i, title in enumerate(titles[:limit]):
        hits.append(
            WebStoryHit(
                title=title,
                url=urls[i] if i < len(urls) else "",
                source="wikipedia_opensearch",
                description=_clean(descs[i] if i < len(descs) else ""),
                relevance=_relevance(title),
            )
        )
    return hits


# ---------------------------------------------------------------------------
# Marvel Fandom (keyless, deterministic)
# ---------------------------------------------------------------------------

def search_marvel_fandom(query: str, limit: int = 5) -> List[WebStoryHit]:
    """Search the Marvel Fandom wiki for relevant storylines (if reachable)."""
    q = urllib.parse.quote(query)
    url = (
        f"{MARVEL_FANDOM_API}?action=query&list=search"
        f"&srsearch={q}&format=json&srlimit={limit}"
    )
    data = _fetch(url)
    hits: List[WebStoryHit] = []
    if not data:
        return hits
    for item in (data.get("query", {}).get("search", []) or [])[:limit]:
        title = item.get("title", "")
        hits.append(
            WebStoryHit(
                title=title,
                url=f"https://marvel.fandom.com/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                source="marvel_fandom",
                description=_clean(item.get("snippet", ""))[:300],
                relevance=_relevance(title),
            )
        )
    return hits


# ---------------------------------------------------------------------------
# Relevance heuristic (deterministic)
# ---------------------------------------------------------------------------

# Keywords that suggest an on-topic cancer/research-relevant story.
_ONCOLOGY_TERMS = [
    "cancer", "tumor", "onc", "metasta", "immune", "mutat", "clone", "cell",
    "therapy", "disease", "resist", "spread", "recurr", "death", "death of",
    "fall", "rise", "decay", "virus", "infection", "assimila", "infiltrat",
]

# Strong signals that a title is an actual STORYLINE / EVENT / ISSUE (high value).
_STORYLINE_TERMS = [
    "saga", "war", "invasion", "covenant", "dynasty", "chronicle", "event",
    "fall of", "death of", "rise of", "reign", "gauntlet", "civil", "annihila",
    "assemble", "disassembled", "house of", "age of", "reborn", "origin",
]

# Signals that a title is a CHARACTER page / metadata (lower value for story search).
_CHARACTER_MARKERS = [
    "(earth-", "(character)", "(lmd)", "(skrull)", "(mutant)", "(marvel cinematic",
    "characters)", "appearances)", "quotes)", "gallery)", "issue covers",
]

# Format tokens that indicate a comic issue / storyline rather than a character.
_ISSUE_PATTERN = re.compile(
    r"(vol\s*\d+|#\d+|\b(?:part|chapter|issue|book)\s+\d+|\b\d+\s*[-–]\s*\d+)",
    re.IGNORECASE,
)


def _relevance(title: str) -> float:
    """Deterministic 0-1 relevance score preferring STORYLINE titles.

    Higher score = more likely to be an actual story/event/issue relevant to a
    research metaphor, rather than a bare character page or metadata page.
    """
    t = title.lower().strip()
    score = 0.0

    # Penalize character/metadata pages (paren disambiguators).
    if any(m in t for m in _CHARACTER_MARKERS):
        score -= 0.5
    # Penalize a bare character name with no story context.
    if "(" not in t and " " not in t:
        score -= 0.3

    # Strong bonus for a clear storyline / event keyword.
    if any(w in t for w in _STORYLINE_TERMS):
        score += 0.6
    # Bonus for an issue/comic framing (Vol #, "#12", "Part 1", "1-3").
    if _ISSUE_PATTERN.search(t):
        score += 0.4
    # Bonus for a year range (event spanning issues/years, e.g. "1994-1996").
    if re.search(r"\d{4}\s*[-–]\s*\d{4}", t):
        score += 0.2

    # On-topic keyword boost.
    for kw in _ONCOLOGY_TERMS:
        if kw in t:
            score += 0.2

    # Clamp to [0, 1]. No hard floor: character-only / off-topic pages score low.
    return min(1.0, max(0.0, score))


# ---------------------------------------------------------------------------
# Deterministic story search (aggregates all web sources, dedupes)
# ---------------------------------------------------------------------------

def web_search_stories(query: str, limit: int = 8) -> List[WebStoryHit]:
    """Run deterministic web search for relevant comic storylines."""
    gathered: List[WebStoryHit] = []
    seen: set = set()

    def add(hits: List[WebStoryHit]):
        for h in hits:
            key = h.title.lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            gathered.append(h)

    # Wikipedia full-text + opensearch are the primary deterministic sources.
    add(search_wikipedia(query, limit=limit))
    add(search_wikipedia_opensearch(query, limit=limit))
    # Marvel Fandom is best-effort (may be blocked/unreachable in some networks).
    add(search_marvel_fandom(query, limit=limit))

    # Sort by relevance (deterministic), then title.
    gathered.sort(key=lambda h: (-h.relevance, h.title))
    return gathered[:limit]


# ---------------------------------------------------------------------------
# Cross-reference a mapped story
# ---------------------------------------------------------------------------

def cross_reference_story(
    topic: str,
    primary_title: str,
    protocol_id: Optional[str],
    index,
    top_k: int = 4,
    web_limit: int = 5,
) -> StoryCrossRef:
    """Cross-reference a mapped story: nearest index neighbours + web stories.

    Deterministic: index neighbours come from FAISS similarity; web stories come
    from keyless public APIs. Both fail-soft (empty on error).
    """
    # 1. Related protocols in the local index (semantic nearest neighbours).
    related_index: List[Dict[str, Any]] = []
    try:
        results = index.search_protocols(topic, top_k=top_k, return_scores=True)
        for proto, sim in results:
            if proto.id == protocol_id:
                continue  # don't list the primary itself
            related_index.append(
                {
                    "id": proto.id,
                    "archetype": proto.archetype,
                    "narrative": proto.narrative,
                    "similarity": round(float(sim), 3),
                }
            )
    except Exception:
        related_index = []

    # 2. Web-discovered related stories.
    web_hits = web_search_stories(
        f"{topic} {primary_title}".strip(), limit=web_limit
    )

    return StoryCrossRef(
        primary=primary_title,
        primary_protocol_id=protocol_id,
        related_index=related_index,
        related_web=[h for h in web_hits],
    )


# ---------------------------------------------------------------------------
# Serialization helper for the API
# ---------------------------------------------------------------------------

def story_crossref_to_dict(ref: StoryCrossRef) -> Dict[str, Any]:
    return {
        "primary": ref.primary,
        "primary_protocol_id": ref.primary_protocol_id,
        "related_index": ref.related_index,
        "related_web": [
            {
                "title": h.title,
                "url": h.url,
                "source": h.source,
                "description": h.description,
                "relevance": round(h.relevance, 2),
            }
            for h in ref.related_web
        ],
    }
