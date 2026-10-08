#!/usr/bin/env python3
"""
Compile Business Books → Metaphor Engine Protocols
====================================================

Scans the Overlay365 book library (E:\\Books and E:\\books 2) for business-relevant
titles, extracts their structure (TOC + opening pages), classifies each into a
business domain, and emits protocols in the Comic Metaphor Engine's native
format (Source Material / Narrative / Business Translation / D1–D4 / Strategy /
Vector Entry). Output goes to business_books/books_<domain>.txt which the engine's
DataIngestionPipeline parses on the next rebuild.

Design:
- TITLE-BASED CLASSIFICATION: business domain is inferred from the title via a
  keyword rule table (deterministic, auditable).
- STRATEGY LAYER: each domain maps to a default BusinessStrategy (strategy type,
  moat, value-chain stage, business-model lever, target segment, risk, principle).
- REUSE: uses the same PDF/EPUB extraction approach as engine/ingest.py so the
  compiled output parses cleanly with the existing parser.

Usage:
    python scripts/compile_business_books.py --scan
    python scripts/compile_business_books.py --compile   # curate + emit protocols
    python scripts/compile_business_books.py --all       # every readable book
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from ebooklib import epub as _epub_lib

    EBOOKLIB_AVAILABLE = True
except Exception:
    EBOOKLIB_AVAILABLE = False

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent.parent  # engine root
BUSINESS_DIR = HERE / "business_books"
DEFAULT_LIBRARIES = [
    Path(r"E:\Books"),
    Path(r"E:\books 2\Books"),
]
MAX_OPENING_CHARS = 4500  # keep per-book narrative compact
MAX_TOC_LINES = 60
PER_BOOK_TIMEOUT_SEC = 30  # a single slow PDF must not stall the whole domain

# ----------------------------------------------------------------------------
# Business domains & strategy defaults
# ----------------------------------------------------------------------------
# domain -> (StrategyType, MoatType, ValueChainStage, BusinessModelLever,
#            target_segment, strategic_risk, key_principle, tags)
DOMAIN_STRATEGY: Dict[str, Tuple[str, str, str, str, str, str, str, List[str]]] = {
    "strategy": (
        "differentiation", "brand", "marketing_sales", "retention",
        "CEOs, founders, strategists", "Imitation erodes differentiation without a defensible moat",
        "Competitive position is a choice, not an accident — pick where to win.", ["strategy", "positioning", "competitive", "moat", "planning"],
    ),
    "marketing": (
        "differentiation", "brand", "marketing_sales", "acquisition",
        "marketers, growth teams, brand managers", "Tactics without a durable brand erode margins",
        "Permission beats interruption; attention is earned, never bought.", ["marketing", "brand", "growth", "demand", "positioning"],
    ),
    "sales": (
        "distribution_play", "distribution", "marketing_sales", "volume",
        "sales teams, founders, B2B reps", "Pipeline collapse when relationship leverage is not systematized",
        "Win the channel and you win the market — distribution compounds.", ["sales", "pipeline", "conversion", "revenue", "distribution"],
    ),
    "leadership": (
        "transformational", "talent", "operations", "retention",
        "executives, managers, team leads", "Culture decay compounds faster than product decay",
        "Leadership is the allocation of attention — spend it like capital.", ["leadership", "culture", "management", "team", "execution"],
    ),
    "finance": (
        "focus", "switching_costs", "operations", "margin",
        "investors, traders, finance teams", "Volatility is a tax on the unprepared",
        "Risk management is the strategy; returns are the byproduct.", ["finance", "investing", "trading", "risk", "capital"],
    ),
    "economics": (
        "cost_leadership", "scale_economies", "operations", "margin",
        "economists, policy analysts, strategists", "Incentives misread produce policy failure",
        "Follow the incentive — it predicts behavior better than stated intent.", ["economics", "incentives", "markets", "macro", "policy"],
    ),
    "operations": (
        "vertical_integration", "scale_economies", "operations", "margin",
        "COOs, ops leaders, supply chain", "Bottlenecks migrate; the system is only as fast as its slowest link",
        "Flow beats peak efficiency — smooth the constraint, not the average.", ["operations", "supply chain", "logistics", "process", "efficiency"],
    ),
    "entrepreneurship": (
        "blue_ocean", "none_na", "platform_infrastructure", "compounding",
        "founders, solo operators, startups", "Founder-market fit is fragile without repeatable demand",
        "Find the uncontested space; create value where no one is looking.", ["startup", "founder", "business model", "ventures", "opportunity"],
    ),
    "biotech": (
        "proprietary_tech", "proprietary_tech", "r_and_d", "margin",
        "biotech founders, R&D leaders, clinicians", "Regulatory and trial risk dominate technical success",
        "Translate biology into capital by de-risking the pipeline stage by stage.", ["biotech", "healthcare", "therapeutics", "diagnostics", "bioinformatics"],
    ),
    "coding": (
        "platform", "proprietary_tech", "platform_infrastructure", "compounding",
        "engineers, technical founders, AI builders", "Tooling velocity compounds or decays the whole fleet",
        "Software leverage is exponential — build once, run everywhere.", ["coding", "software", "ai", "engineering", "tools"],
    ),
    "psychology": (
        "network_effect", "data_moat", "operations", "retention",
        "operators, negotiators, product leaders", "Human bias is a tax every decision pays",
        "Design for the human; the system runs on psychology.", ["psychology", "behavior", "bias", "influence", "decision"],
    ),
    "general": (
        "differentiation", "none_na", "operations", "margin",
        "general business readers", "Unfocused strategies underperform every focused one",
        "Clarity of purpose beats volume of activity.", ["business", "general", "management", "productivity"],
    ),
}

# Title keyword → domain classifier (longest-prefix wins, first match).
TITLE_RULES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"strateg|competitive|blue ocean|positioning|moat|5 forces|porter", re.I), "strategy"),
    (re.compile(r"market|brand|advertis|content market|seo|social media market|growth market|permission", re.I), "marketing"),
    (re.compile(r"sales|pipeline|negotiat|clos(e|ing).*sale|referral", re.I), "sales"),
    (re.compile(r"leader|manage|executive|ceo|team|coach|culture|power$|influence", re.I), "leadership"),
    (re.compile(r"invest|trade|stock|option|finance|wealth|money|bank|account|capital|crypto|forex|dividend|portfolio", re.I), "finance"),
    (re.compile(r"econom|macro|micro|market struct|incentive|tax", re.I), "economics"),
    (re.compile(r"logistic|supply chain|operation|inventor|warehouse|manufactur|lean|six sigma|process", re.I), "operations"),
    (re.compile(r"startup|entrepren|small business|founder|business plan|passive income|side hustle|dropship|amazon fba", re.I), "entrepreneurship"),
    (re.compile(r"bioinform|biotech|healthcare|therapeut|genom|drug|clinical|molecular|pharma|medicine|biology", re.I), "biotech"),
    (re.compile(r"coding|programm|software|python|ai (assist|agent|code)|langchain|develop(er|ment)|deploy|github|postgres|kubernetes|distributed", re.I), "coding"),
    (re.compile(r"psycholog|behavior|manipulat|persuasion|nlp|mind|influence people|habits|emotional", re.I), "psychology"),
]

# Explicit overrides for known titles (deterministic curation).
TITLE_OVERRIDES: Dict[str, str] = {
    "the psychology of money": "finance",
    "the 48 laws of power": "leadership",
    "atomic habits": "psychology",
    "the diary of a ceo": "entrepreneurship",
    "unshakeable": "finance",
    "options trading for dummies": "finance",
    "global business today": "strategy",
    "managerial accounting for dummies": "finance",
    "business analytics for managers": "operations",
    "logistics and supply chain management": "operations",
    "global supply chain": "operations",
    "strategic logistics management": "operations",
    "the 1-page marketing plan": "marketing",
    "22 immutable laws of branding": "marketing",
    "22 immutable laws of marketing": "marketing",
    "how to win friends and influence people": "leadership",
    "permission marketing": "marketing",
    "handbook on the economics of renewable energy": "economics",
    "principles of economics": "economics",
    "the economics book": "economics",
    "economics of inequality": "economics",
    "poor economics": "economics",
    "making sense of chaos": "economics",
    "modern principles of economics": "economics",
    "understandable economics": "economics",
    "calculus with applications to economics": "economics",
    "illustrated handbook of trade and global market": "finance",
    "how to start your own business": "entrepreneurship",
    "the small business start-up kit": "entrepreneurship",
    "chatgpt millionaire handbook": "entrepreneurship",
    "passive income ideas": "entrepreneurship",
    "critical business skills for success": "strategy",
    "harvard business review": "strategy",
    "100 best business books of all time": "strategy",
    "50 business classics": "strategy",
    "sports betting for winners": "finance",
    "affiliate marketing and amazon fba": "marketing",
    "youtube marketing for dummies": "marketing",
    "killer chatgpt prompts": "entrepreneurship",
    "knowledge is profit": "strategy",
    "business intelligence and data analysis": "operations",
    "data analysis for business decisions": "operations",
    "modern business data analyst": "operations",
    "business intelligence, analytics, data science": "operations",
    "python for business analytics": "operations",
    "excel skills for business": "operations",
    "data tables and pivot tables": "operations",
    "generative ai for trading and asset management": "finance",
    "the art of ai product development": "entrepreneurship",
    "behavioral economics": "economics",
    "man's search for meaning": "psychology",
    "dark psychology": "psychology",
    "how to become a communication genius": "leadership",
    "the algo rhythm": "finance",
    "options trading crash course": "finance",
    "options trading made simple": "finance",
    "options as a strategic investment": "finance",
    "mastering stocks": "finance",
    "penny stocks made simple": "finance",
    "day trade for a living": "finance",
    "algorithmic trading system toolbox": "finance",
    "cryptocurrency trading with python": "finance",
    "practical blockchain and cryptocurrency": "finance",
    "fintech 5.0": "finance",
    "a beginner's guide to bitcoin": "finance",
    "commodity branding": "marketing",
    "music law": "entrepreneurship",
    "the economics of renewable energy": "economics",
    "logistics and supply chain toolkit": "operations",
    "watts pocket handbook": "finance",
    "resume and cover letter": "leadership",
    "job search mastery": "leadership",
    "communication genius": "leadership",
    "how to day trade for a living": "finance",
    "sap s-4hana supply chain": "operations",
    "essentials of logistics and management": "operations",
    "management accounting for dummies": "finance",
    "the ultimate algorithmic trading system": "finance",
    "opzioni trading for dummies": "finance",
}

# Titles that should NEVER be compiled (tools, mods, non-books, software).
SKIP_PATTERNS: List[re.Pattern] = [
    re.compile(r"mod apk|crackshash|\.exe|v[0-9]+\.\d+\.\d+\.\d+.*(mod|apk)", re.I),
    re.compile(r"premium (mod|apk)", re.I),
    re.compile(r"portable", re.I),
    re.compile(r"fitness, home workout", re.I),
    re.compile(r"spotify|musify|voxengo|nordvpn|instaprime", re.I),
    re.compile(r"photography books collection", re.I),
    re.compile(r"sex & sexuality", re.I),
    re.compile(r"recipe|coastal|cookbook", re.I),
    re.compile(r"farmer's weekly|golf digest|wall street journal", re.I),
    re.compile(r"windows 10|digital activation|ebooks manager|e-books", re.I),
]

# False-positive guards: titles matching these are NOT business books even if a
# strategy/marketing keyword appears (e.g. "Strabismus Surgery Strategies",
# "English Grammar Communication Strategies", "Full Stack JavaScript Strategies").
NON_BUSINESS_PATTERNS: List[re.Pattern] = [
    re.compile(r"surgery|strabismus|ophthal|optical|ortho|surgical", re.I),
    re.compile(r"english grammar|grammar|language learning|intermediate level|vocabulary", re.I),
    re.compile(r"full stack|javascript strategies|react|typescript|frontend|backend", re.I),
    re.compile(r"physics|chemistry|astronomy|mathematics|calculus|quantum|thermodynam", re.I),
    re.compile(r"photography|astrophys|marine biology|astronomy", re.I),
    re.compile(r"aerospace|aviation|spacecraft|satellite", re.I),
    re.compile(r"dental|radiology|imaging\.specific|medical diagnosis|nursing", re.I),
    re.compile(r"guitar|music theory|beat making|fl studio|songwriting", re.I),
    re.compile(r"cookbook|recipes|culinary|chef", re.I),
    re.compile(r"workout|fitness|exercise|yoga|nutrition|diet", re.I),
    re.compile(r"parenting|pregnancy|teen|child.*develop", re.I),
    re.compile(r"christian|bible|prayer|spiritual|buddhist", re.I),
]


# ----------------------------------------------------------------------------
# Book discovery
# ----------------------------------------------------------------------------
def iter_book_files(library_dirs: List[Path]) -> List[Path]:
    files: List[Path] = []
    seen: set = set()
    for lib in library_dirs:
        if not lib.exists():
            continue
        for f in lib.rglob("*"):
            if f.is_file() and f.suffix.lower() in (".pdf", ".epub"):
                key = f.stem.lower()
                if key in seen:
                    continue
                seen.add(key)
                files.append(f)
    return files


def clean_title(fname: str) -> str:
    """Derive a readable title from a filename (strip year/author cruft)."""
    stem = Path(fname).stem
    stem = re.sub(r"\.(pdf|epub|txt)$", "", stem, flags=re.I)
    stem = re.sub(r"\b(19|20)\d{2}\b", "", stem)  # years
    stem = re.sub(r"\s{2,}", " ", stem)
    return stem.strip(" -_")


def classify(title: str, fname: str) -> str:
    key = title.lower().strip()
    for override, domain in TITLE_OVERRIDES.items():
        if override in key:
            return domain
    for pattern, domain in TITLE_RULES:
        if pattern.search(key):
            return domain
    return "general"


def should_skip(title: str, fname: str) -> bool:
    for pat in SKIP_PATTERNS:
        if pat.search(fname) or pat.search(title):
            return True
    for pat in NON_BUSINESS_PATTERNS:
        if pat.search(title):
            return True
    return False


# ----------------------------------------------------------------------------
# Text extraction (PDF / EPUB)
# ----------------------------------------------------------------------------
def extract_pdf_text(path: Path) -> Tuple[str, int]:
    """Return (opening text, page_count) from a PDF (fast: first few pages)."""
    if pdfplumber is None:
        return "", 0
    parts: List[str] = []
    count = 0
    try:
        with pdfplumber.open(path) as pdf:
            total = len(pdf.pages)
            pages_to_read = min(total, 3)  # TOC + opening is enough for a protocol
            for i in range(pages_to_read):
                text = pdf.pages[i].extract_text() or ""
                if text.strip():
                    parts.append(text.strip()[:1800])  # cap per-page size
                    count += 1
                if sum(len(p) for p in parts) > MAX_OPENING_CHARS:
                    break
        return "\n\n".join(parts), count
    except Exception as e:
        return f"[extract error: {e}]", 0


def extract_epub_text(path: Path) -> Tuple[str, int]:
    """Return (opening text, chapter_count) from an EPUB (fast)."""
    parts: List[str] = []
    count = 0
    try:
        if EBOOKLIB_AVAILABLE:
            book = _epub_lib.read_epub(str(path))
            for item in book.get_items():
                if item.get_type() == 9:  # DOCUMENT
                    try:
                        html = item.get_content().decode("utf-8", errors="ignore")
                        text = re.sub(r"<[^>]+>", " ", html)
                        text = re.sub(r"\s{2,}", " ", text).strip()[:1800]
                        if text:
                            parts.append(text)
                            count += 1
                        if sum(len(p) for p in parts) > MAX_OPENING_CHARS:
                            break
                    except Exception:
                        continue
        else:
            with zipfile.ZipFile(path, "r") as zf:
                for name in zf.namelist():
                    if name.lower().endswith((".xhtml", ".html", ".htm")):
                        try:
                            html = zf.read(name).decode("utf-8", errors="ignore")
                            text = re.sub(r"<[^>]+>", " ", html)
                            text = re.sub(r"\s{2,}", " ", text).strip()[:1800]
                            if text:
                                parts.append(text)
                                count += 1
                        except Exception:
                            continue
        return "\n\n".join(parts), count
    except Exception as e:
        return f"[extract error: {e}]", 0


def extract_book_text(path: Path) -> Tuple[str, int]:
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    return extract_epub_text(path)


# --- Hard per-book timeout + disk cache --------------------------------------
# Some textbooks (Harrison's, huge PDFs) take minutes in pdfplumber. Each book
# is extracted in a child python process capped at PER_BOOK_TIMEOUT_SEC and the
# result is cached in .book_cache.json keyed by (path, mtime, size) so re-runs
# and interrupted builds are cheap and resumable.
_CACHE_PATH = HERE / "business_books" / ".book_cache.json"


def _load_cache() -> Dict[str, Dict[str, Any]]:
    try:
        return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: Dict[str, Dict[str, Any]]) -> None:
    try:
        _CACHE_PATH.parent.mkdir(exist_ok=True)
        _CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def extract_book_text_guarded(path: Path) -> Tuple[str, int]:
    """Extract with a hard subprocess timeout + disk cache (resumable)."""
    try:
        stat = path.stat()
        key = f"{path}|{stat.st_mtime_ns}|{stat.st_size}"
    except Exception:
        key = str(path)
    cache = _load_cache()
    if key in cache:
        return cache[key].get("text", ""), cache[key].get("count", 0)

    try:
        res = subprocess.run(
            [sys.executable, str(HERE / "scripts" / "compile_business_books.py"),
             "--extract-one", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=PER_BOOK_TIMEOUT_SEC,
            cwd=str(HERE),
        )
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout.strip().splitlines()[-1])
            cache[key] = {"text": data.get("text", ""), "count": data.get("count", 0)}
            _save_cache(cache)
            return data.get("text", ""), data.get("count", 0)
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass

    cache[key] = {"text": f"[timeout or extract failure: {path.name}]", "count": 0}
    _save_cache(cache)
    return cache[key]["text"], 0


# ----------------------------------------------------------------------------
# Protocol emission
# ----------------------------------------------------------------------------
def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return s[:90]


def strategy_block(domain: str, title: str) -> Dict[str, Any]:
    s = DOMAIN_STRATEGY.get(domain, DOMAIN_STRATEGY["general"])
    (stype, moat, vc, lever, seg, risk, principle, tags) = s
    return {
        "strategy_type": stype,
        "moat": moat,
        "value_chain_stage": vc,
        "business_model_lever": lever,
        "target_segment": seg,
        "strategic_risk": risk,
        "key_principle": principle,
        "strategy_tags": tags,
        "confidence": 0.7,
    }


def emit_protocol(index: int, title: str, fname: str, domain: str,
                  narrative: str, src_type: str) -> str:
    strat = strategy_block(domain, title)
    pid = f"protocol_{slugify(title)}"
    archetype = f"{title} Pattern"
    dims = {
        "Bio/Internal": ("The book's treatment of the internal capability, learning and team psychology required to execute.",
                         "Outcome metric tracking internal capability across the {domain} practice"),
        "Tech/External": ("The book's treatment of external technology, tools and system architecture.",
                          "Outcome metric tracking technology adoption across the {domain} practice"),
        "Eco/Resources": ("The book's treatment of resources, economics, allocation and market forces.",
                          "Outcome metric tracking resource allocation across the {domain} practice"),
        "Cosmic/Limit": ("The book's treatment of structural limits, uncertainty and long-horizon dynamics.",
                         "Outcome metric tracking long-horizon risk across the {domain} practice"),
    }
    narrative_short = narrative[:MAX_OPENING_CHARS] if narrative else f"Source: {fname}"

    lines = [
        f"{index}. The \"{title}\" Protocol",
        "",
        f"Source Material: {title}",
        "",
        "The Narrative:",
        "Source text (TOC + opening pages):",
        narrative_short,
        "",
        f"The Business Translation:",
        f"{domain.capitalize()} domain protocol compiled from the Overlay365 book library. {strat['key_principle']}",
        "",
    ]
    for dim_num, (dim_label, (logic, metric)) in enumerate(dims.items(), start=1):
        lines += [
            f"* D{dim_num} ({dim_label}):",
            f"  * Logic: {logic.replace('{domain}', domain)}",
            f"  * Metric: {metric.replace('{domain}', domain)}",
            "",
        ]
    lines += [
        f"* Strategy:",
        f"  * Strategy Type: {strat['strategy_type']}",
        f"  * Moat: {strat['moat']}",
        f"  * Value Chain Stage: {strat['value_chain_stage']}",
        f"  * Business Model Lever: {strat['business_model_lever']}",
        f"  * Target Segment: {strat['target_segment']}",
        f"  * Strategic Risk: {strat['strategic_risk']}",
        f"  * Key Principle: {strat['key_principle']}",
        f"  * Strategy Tags: {', '.join(strat['strategy_tags'])}",
        "",
        "Vector Entry (JSON):",
        "{",
        f"  \"id\": \"{pid}\",",
        f"  \"archetype\": \"{archetype}\",",
        f"  \"domain\": \"{domain}\",",
        f"  \"source\": \"{fname}\",",
        f"  \"business_logic\": \"{strat['key_principle']}\",",
        f"  \"application\": \"Business Book: {title}\",",
        f"  \"strategy\": {json.dumps(strat)},",
        "  \"key_characters\": [],",
        "  \"related_protocols\": []",
        "}",
        "",
    ]
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Compile
# ----------------------------------------------------------------------------
def compile_books(library_dirs: List[Path], all_books: bool = False,
                  domains_filter: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    files = iter_book_files(library_dirs)
    by_domain: Dict[str, List[Dict[str, Any]]] = {}
    skipped = 0
    for f in files:
        title = clean_title(f.name)
        if should_skip(title, f.name):
            skipped += 1
            continue
        domain = classify(title, f.name)
        if domains_filter and domain not in domains_filter:
            continue
        by_domain.setdefault(domain, []).append({"path": f, "title": title, "domain": domain})
    print(f"Scanned {len(files)} files → {skipped} skipped, "
          f"{sum(len(v) for v in by_domain.values())} candidates by domain:")
    for dom, items in sorted(by_domain.items()):
        print(f"  {dom}: {len(items)}")
    return by_domain


def emit_files(by_domain: Dict[str, List[Dict[str, Any]]]) -> None:
    BUSINESS_DIR.mkdir(exist_ok=True)
    for domain, items in sorted(by_domain.items()):
        out_path = BUSINESS_DIR / f"books_{domain}.txt"
        blocks: List[str] = [f"Expansion Pack: {domain} books compiled from the Overlay365 book library."]
        idx = 0
        for item in items:
            narrative, _ = extract_book_text_guarded(item["path"])
            idx += 1
            blocks.append(emit_protocol(
                idx, item["title"], item["path"].name, item["domain"], narrative, item["path"].suffix.lstrip(".")
            ))
            print(f"  [{domain}] {idx}. {item['title']}", flush=True)
        out_path.write_text("\n".join(blocks), encoding="utf-8")
        print(f"✓ Wrote {idx} {domain} protocols → {out_path.name}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Compile business books into metaphor engine protocols.")
    parser.add_argument("--scan", action="store_true", help="Scan libraries and report classification (no write).")
    parser.add_argument("--compile", action="store_true", help="Emit protocol files for the curated business subset.")
    parser.add_argument("--all", action="store_true", help="Compile every readable book (no curation).")
    parser.add_argument("--domains", type=str, default=None,
                        help="Comma-separated domain filter, e.g. strategy,finance,marketing")
    parser.add_argument("--lib", type=str, default=None, help="Additional library path (pass ;-separated)")
    parser.add_argument("--extract-one", type=str, default=None,
                        help="(internal) Print JSON of extracted text for one file, used by the guarded extractor.")
    args = parser.parse_args()

    if args.extract_one:
        p = Path(args.extract_one)
        text, count = extract_book_text(p)
        print(json.dumps({"text": text, "count": count}, ensure_ascii=False))
        return

    libs = list(DEFAULT_LIBRARIES)
    if args.lib:
        libs += [Path(p.strip()) for p in args.lib.split(";") if p.strip()]

    domains_filter = [d.strip() for d in args.domains.split(",")] if args.domains else None

    if args.scan:
        compile_books(libs, all_books=args.all, domains_filter=domains_filter)
        return

    if args.compile or args.all:
        by_domain = compile_books(libs, all_books=args.all, domains_filter=domains_filter)
        emit_files(by_domain)
        print("\nDone. Run the ingestion pipeline next to merge these into the KB.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
