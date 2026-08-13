"""Tests for engine.comic_insights."""
import sys
import zipfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engine.comic_insights import analyze_text, build_insight_report, extract_text_from_file

SAMPLE = (
    "Peter Parker lost everything when his invention was stolen. "
    "He had to rebuild trust with the people he loved while a secret "
    "identity let a double agent destroy the team from the inside. "
    "His sacrifice gave him a second chance at redemption."
)


class _StubEngine:
    index = None

    def generate_mapping(self, **kwargs):
        raise ValueError("no viable protocols")


def test_analyze_text_detects_themes():
    result = analyze_text(SAMPLE)
    assert "trust" in result["themes"]
    assert "sacrifice" in result["themes"]
    assert result["word_count"] > 0


def test_analyze_text_finds_characters():
    result = analyze_text(SAMPLE)
    assert "Peter Parker" in result["characters"]


def test_extract_text_txt(tmp_path):
    p = tmp_path / "comic.txt"
    p.write_text(SAMPLE, encoding="utf-8")
    out = extract_text_from_file(p, "comic.txt")
    assert out["status"] == "ready"
    assert "Peter Parker" in out["text"]


def test_extract_text_unsupported_archive(tmp_path):
    p = tmp_path / "comic.cbz"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("page1.png", b"\x89PNG\r\n\x1a\n")
        zf.writestr("page2.png", b"\x89PNG\r\n\x1a\n")
    out = extract_text_from_file(p, "comic.cbz")
    assert out["status"] == "unsupported"
    assert out["page_count"] == 2


def test_build_report_shape(engine):
    report = build_insight_report(SAMPLE, "my_comic.txt", engine=engine)
    assert report["report_id"].startswith("insight_")
    assert report["source_file"] == "my_comic.txt"
    assert isinstance(report["themes"], list)
    assert isinstance(report["characters"], list)
    assert "codex_scores" in report
    assert "takeaways" in report
    assert "action_items" in report


def test_build_report_empty_text():
    report = build_insight_report("", "empty.txt", engine=_StubEngine())
    assert report["report_id"].startswith("insight_")
    assert report["themes"] == []
    assert report["codex_scores"] == {}


def test_build_report_no_viable_protocols():
    report = build_insight_report(SAMPLE, "x.txt", engine=_StubEngine())
    assert report["protocol_id"] is None
    assert report["codex_scores"] == {}
    assert report["takeaways"] == []


def test_extract_text_txt_caps_length(tmp_path):
    from engine.comic_insights import MAX_TEXT_CHARS

    p = tmp_path / "big.txt"
    p.write_text("word " * 20_000, encoding="utf-8")
    out = extract_text_from_file(p, "big.txt")
    assert out["status"] == "ready"
    assert len(out["text"]) <= MAX_TEXT_CHARS
