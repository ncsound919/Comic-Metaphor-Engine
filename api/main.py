"""
Comic Metaphor Engine - REST API
================================

FastAPI service exposing the metaphor engine as a modern web API.

Endpoints:
    GET  /health                 Liveness + readiness probe
    GET  /api/protocols          List all protocols (with filters)
    GET  /api/protocols/{id}     Single protocol detail
    POST /api/search             Semantic protocol search
    POST /api/map                Generate a metaphor mapping
    POST /api/explain            Plain-language explanation of a mapping
    POST /api/lesson             Compact learning lesson for a topic
    POST /api/narrative          Full generated narrative (podcast/marketing/etc.)

Run:
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api.runtime import get_adapter, get_engine, get_index  # noqa: E402
from engine.schema import (  # noqa: E402
    FormatType,
    GenerationContext,
    ToneType,
)

app = FastAPI(
    title="Comic Metaphor Engine API",
    description="Map real-world problems to comic book storylines, scored and explained.",
    version="2.0.0",
)

# Allow the React UI (ui-v2) on any origin during development and on Vercel.
_APP_URL = os.getenv("APP_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        _APP_URL,
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request / Response models
# =============================================================================


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Free-text search query")
    top_k: int = Field(5, ge=1, le=25)
    filters: Optional[Dict[str, Any]] = None


class MapRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    format: str = "podcast_monologue"
    tone: str = "hopeful"
    top_k: int = Field(5, ge=1, le=25)
    constraints: Optional[Dict[str, Any]] = None


class ExplainRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    format: str = "podcast_monologue"
    tone: str = "hopeful"
    audience: str = "general"
    top_k: int = Field(5, ge=1, le=25)


class NarrativeRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    format: str = "podcast_monologue"
    tone: str = "hopeful"
    word_count_target: int = Field(600, ge=100, le=5000)
    top_k: int = Field(5, ge=1, le=25)


def _enum_value(enum_cls, value: str, default):
    try:
        return enum_cls(value)
    except ValueError:
        return default


# =============================================================================
# Routes
# =============================================================================


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "comic-metaphor-engine",
        "version": app.version,
        "protocols_loaded": len(get_index().protocol_list),
        "timestamp": time.time(),
    }


@app.get("/api/protocols")
def list_protocols(
    protocol_type: Optional[str] = None,
    archetype: Optional[str] = None,
    limit: int = 100,
):
    index = get_index()
    results: List[Dict[str, Any]] = []
    for p in index.protocol_list:
        if protocol_type and p.protocol_type.value != protocol_type:
            continue
        if archetype and archetype.lower() not in p.archetype.lower():
            continue
        results.append(
            {
                "id": p.id,
                "protocol_type": p.protocol_type.value,
                "archetype": p.archetype,
                "business_logic": p.business_logic,
                "themes": p.themes,
                "risk_categories": [r.value for r in p.risk_categories],
                "tone_compatibility": [t.value for t in p.tone_compatibility],
            }
        )
        if len(results) >= limit:
            break
    return {"count": len(results), "protocols": results}


@app.get("/api/protocols/{protocol_id}")
def get_protocol(protocol_id: str):
    index = get_index()
    protocol = index.get_protocol_by_id(protocol_id)
    if protocol is None:
        raise HTTPException(status_code=404, detail=f"Protocol not found: {protocol_id}")
    return protocol.to_dict()


@app.post("/api/search")
def search(req: SearchRequest):
    index = get_index()
    t0 = time.time()
    results = index.search_protocols(
        req.query, filters=req.filters, top_k=req.top_k, return_scores=True
    )
    payload = [
        {
            "protocol_id": p.id,
            "similarity": round(score, 4),
            "archetype": p.archetype,
            "business_logic": p.business_logic,
            "themes": p.themes,
            "protocol_type": p.protocol_type.value,
        }
        for p, score in results
    ]
    return {
        "query": req.query,
        "latency_ms": round((time.time() - t0) * 1000, 1),
        "results": payload,
    }


@app.post("/api/map")
def generate_mapping(req: MapRequest):
    engine = get_engine()
    fmt = _enum_value(FormatType, req.format, FormatType.PODCAST_MONOLOGUE)
    tone = _enum_value(ToneType, req.tone, ToneType.HOPEFUL)
    try:
        mapping = engine.generate_mapping(
            topic=req.topic,
            target_format=fmt,
            target_tone=tone,
            constraints=req.constraints,
            top_k=req.top_k,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return mapping.to_dict()


@app.post("/api/explain")
def explain(req: ExplainRequest):
    from engine.explainers import explain_mapping

    engine = get_engine()
    index = get_index()
    fmt = _enum_value(FormatType, req.format, FormatType.PODCAST_MONOLOGUE)
    tone = _enum_value(ToneType, req.tone, ToneType.HOPEFUL)
    try:
        mapping = engine.generate_mapping(
            topic=req.topic, target_format=fmt, target_tone=tone, top_k=req.top_k
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    protocol = index.get_protocol_by_id(mapping.protocol_id)
    explanation = explain_mapping(mapping, protocol, audience=req.audience)
    return {
        "mapping": mapping.to_dict(),
        "explanation": explanation.to_dict(),
    }


@app.post("/api/lesson")
def lesson(req: ExplainRequest):
    from engine.explainers import generate_lesson

    engine = get_engine()
    fmt = _enum_value(FormatType, req.format, FormatType.PODCAST_MONOLOGUE)
    tone = _enum_value(ToneType, req.tone, ToneType.HOPEFUL)
    try:
        mapping = engine.generate_mapping(
            topic=req.topic, target_format=fmt, target_tone=tone, top_k=req.top_k
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    protocol = get_index().get_protocol_by_id(mapping.protocol_id)
    return {
        "mapping": mapping.to_dict(),
        "lesson": generate_lesson(mapping, protocol),
    }


@app.post("/api/narrative")
def narrative(req: NarrativeRequest):
    from engine.narrative_generator import NarrativeGenerator

    engine = get_engine()
    index = get_index()
    fmt = _enum_value(FormatType, req.format, FormatType.PODCAST_MONOLOGUE)
    tone = _enum_value(ToneType, req.tone, ToneType.HOPEFUL)
    try:
        mapping = engine.generate_mapping(
            topic=req.topic, target_format=fmt, target_tone=tone, top_k=req.top_k
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    protocol = index.get_protocol_by_id(mapping.protocol_id)
    ctx = GenerationContext(
        mapping=mapping,
        protocol=protocol,
        word_count_target=req.word_count_target,
    )
    output = NarrativeGenerator().generate(ctx)
    return {
        "mapping": mapping.to_dict(),
        "narrative": output.to_dict(),
    }


# =============================================================================
# SaaS: billing + uploads
# =============================================================================

from api.billing import router as billing_router  # noqa: E402
from api.uploads import router as uploads_router  # noqa: E402

app.include_router(uploads_router)
app.include_router(billing_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
