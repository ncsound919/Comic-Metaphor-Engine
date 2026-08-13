"""
Comic insight report generation for user-uploaded comics.

Pure engine module: no Supabase/Stripe imports, so it stays unit-testable
and reusable from CLI runs. Maps an uploaded comic's text to real-world
lessons through the existing MetaphorEngine + CodexAdapter pipeline.
"""

from __future__ import annotations

import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_ARCHIVE_EXTS = {".cbz", ".cbr", ".cb7"}
_TEXT_EXTS = {".txt", ".md"}
MAX_TEXT_CHARS = 60_000

THEME_LEXICONS: Dict[str, List[str]] = {
    "ownership": ["stolen", "ownership", "invention", "patent", "creat", "built", "taken from"],
    "trust": ["trust", "betrayal", "insider", "spy", "secret identity", "double agent", "impostor"],
    "power": ["power", "control", "dominance", "authority", "force", "destroy"],
    "freedom": ["freedom", "escape", "prison", "enslave", "liberat", "captive"],
    "sacrifice": ["sacrifice", "give up", "paid the price", "lost everything"],
    "redemption": ["redemption", "forgive", "second chance", "comeback", "atone"],
    "fear": ["fear", "afraid", "terror", "danger", "threat"],
    "hope": ["hope", "believe", "survive", "protect", "save"],
}

_CHARACTER_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b")
_CHARACTER_STOP = {
    "Once Upon", "Meanwhile", "The End", "A Long", "It Was", "He Had", "She Had",
    "They Were", "Chapter One", "In The", "At The", "This Is", "Next Issue",
}
_WORD_STOP = {
    "the", "and", "that", "with", "from", "they", "have", "this", "were",
    "their", "into", "about", "would", "could", "there", "what", "when",
    "then", "just", "like", "know", "them", "his", "her", "she", "him", "was",
}


def extract_text_from_file(path: Path, filename: str) -> Dict[str, Any]:
    """Return {"text", "page_count", "status"} for a supported comic file."""
    suffix = Path(filename).suffix.lower()
    if suffix in _ARCHIVE_EXTS:
        return {
            "text": "",
            "page_count": _count_archive_pages(path),
            "status": "unsupported",
        }
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".epub":
        return _extract_epub(path)
    if suffix in _TEXT_EXTS:
        return {"text": _read_text_capped(path), "page_count": 1, "status": "ready"}
    return {"text": "", "page_count": 0, "status": "unsupported"}


def _read_text_capped(path: Path, limit: int = MAX_TEXT_CHARS) -> str:
    parts: List[str] = []
    total = 0
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        while total < limit:
            chunk = fh.read(min(8192, limit - total))
            if not chunk:
                break
            parts.append(chunk)
            total += len(chunk)
    return "".join(parts)


def _extract_pdf(path: Path) -> Dict[str, Any]:
    import pdfplumber

    parts: List[str] = []
    page_count = 0
    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
            if sum(len(p) for p in parts) >= MAX_TEXT_CHARS:
                break
    return {
        "text": " ".join(parts)[:MAX_TEXT_CHARS],
        "page_count": page_count,
        "status": "ready",
    }


def _extract_epub(path: Path) -> Dict[str, Any]:
    try:
        import ebooklib
        from ebooklib import epub
    except ImportError:
        return {"text": "", "page_count": 0, "status": "unsupported"}

    parts: List[str] = []
    try:
        book = epub.read_epub(str(path))
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode("utf-8", errors="ignore")
                parts.append(re.sub(r"<[^>]+>", " ", content))
                if sum(len(p) for p in parts) >= MAX_TEXT_CHARS:
                    break
    except Exception:
        return {"text": "", "page_count": 0, "status": "failed"}
    return {
        "text": " ".join(parts)[:MAX_TEXT_CHARS],
        "page_count": len(book.spine) if parts else 0,
        "status": "ready",
    }


def _count_archive_pages(path: Path) -> int:
    suffix = path.suffix.lower()
    image_exts = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    try:
        if suffix in (".cbz", ".cb7"):
            with zipfile.ZipFile(path) as zf:
                return len([n for n in zf.namelist() if n.lower().endswith(image_exts)])
        if suffix == ".cbr":
            import rarfile

            with rarfile.RarFile(str(path)) as rf:
                return len([n for n in rf.namelist() if n.lower().endswith(image_exts)])
    except Exception:
        return 0
    return 0


def analyze_text(text: str) -> Dict[str, Any]:
    """Extract title, themes, characters, and keywords from comic text."""
    lower = text.lower()
    themes = [
        name for name, kws in THEME_LEXICONS.items() if any(kw in lower for kw in kws)
    ]
    characters = _extract_characters(text)
    keywords = _top_keywords(text)
    return {
        "title": _derive_title(text),
        "themes": themes,
        "characters": characters,
        "keywords": keywords,
        "word_count": len(text.split()),
    }


def _extract_characters(text: str, limit: int = 8) -> List[str]:
    counts: Dict[str, int] = {}
    for match in _CHARACTER_PATTERN.finditer(text):
        name = match.group(0)
        if name in _CHARACTER_STOP:
            continue
        counts[name] = counts.get(name, 0) + 1
    ranked = sorted(counts, key=counts.get, reverse=True)
    return ranked[:limit]


def _top_keywords(text: str, limit: int = 12) -> List[str]:
    counts: Dict[str, int] = {}
    for word in re.findall(r"[a-zA-Z]{5,}", text.lower()):
        if word not in _WORD_STOP:
            counts[word] = counts.get(word, 0) + 1
    return sorted(counts, key=counts.get, reverse=True)[:limit]


def _derive_title(text: str) -> str:
    for line in text.splitlines()[:20]:
        line = line.strip()
        if 3 <= len(line) <= 80 and _CHARACTER_PATTERN.match(line):
            return line
    for line in text.splitlines()[:20]:
        line = line.strip()
        if 3 <= len(line) <= 80:
            return line
    return ""


def build_insight_report(
    text: str, filename: str, engine: Optional[Any] = None
) -> Dict[str, Any]:
    """Build the full insight report dict for an uploaded comic."""
    analysis = analyze_text(text)
    report: Dict[str, Any] = {
        "report_id": "insight_" + uuid.uuid4().hex[:12],
        "source_file": filename,
        "title": analysis["title"] or filename,
        "characters": analysis["characters"],
        "themes": analysis["themes"],
        "keywords": analysis["keywords"],
        "word_count": analysis["word_count"],
        "protocol_id": None,
        "codex_scores": {},
        "mappings": [],
        "lessons": {},
        "takeaways": [],
        "action_items": [],
        "summary": "",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if engine is None:
        engine = _lazy_engine()

    topic = " ".join(analysis["themes"]) if analysis["themes"] else analysis["title"]
    topic = (topic or filename).strip()
    if not topic:
        return report

    try:
        mapping = engine.generate_mapping(
            topic=topic,
            target_format=FormatType.BLOG_POST,
            target_tone=ToneType.HOPEFUL,
            top_k=3,
        )
    except ValueError:
        return report

    report["protocol_id"] = mapping.protocol_id
    report["codex_scores"] = {
        "trueness": round(mapping.trueness_score, 4),
        "flow": round(mapping.flow_score, 4),
        "pcs": round(mapping.pcs_score, 4),
        "overall_fit": round(mapping.overall_fit, 4),
        "tap": round(mapping.tap_score, 4),
    }
    report["mappings"] = mapping.to_dict().get("mappings", [])

    try:
        protocol = engine.index.get_protocol_by_id(mapping.protocol_id)
        explanation = explain_mapping(mapping, protocol, audience="writer")
        report["lessons"] = generate_lesson(mapping, protocol)
        report["takeaways"] = explanation.key_takeaways
        report["action_items"] = explanation.action_items
        report["summary"] = explanation.summary
    except Exception:
        pass

    return report


_ENGINE_SINGLETON = None


def _lazy_engine():
    global _ENGINE_SINGLETON
    if _ENGINE_SINGLETON is None:
        from engine.codex_adapter import CodexAdapter
        from engine.index import MetaphorIndex
        from engine.metaphor_engine import MetaphorEngine

        _ROOT = Path(__file__).resolve().parent.parent
        index = MetaphorIndex(processed_dir=str(_ROOT / "processed"), lazy=True)
        _ENGINE_SINGLETON = MetaphorEngine(index, CodexAdapter(index))
    return _ENGINE_SINGLETON


# Imports kept at the bottom so the module still loads if the engine's
# schema/explainers have import-order quirks.
from engine.explainers import explain_mapping, generate_lesson  # noqa: E402
from engine.schema import FormatType, ToneType  # noqa: E402
