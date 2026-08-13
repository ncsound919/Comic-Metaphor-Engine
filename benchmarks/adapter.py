"""
Benchmark Adapter - Cheetah Performance Advisor Ready Format
=============================================================

Converts the Comic Metaphor benchmark results (the list we save from
`run_benchmark.py`) into the `tool_runs`/`marathon` schema that the
Cheetah performance advisor expects so it can ingest and analyze our data.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class BenchmarkAdapter:
    """Helper for adapting benchmark JSON to the advisor schema."""

    def __init__(
        self,
        source_path: Path,
        output_dir: Path,
        marathon_name: str = "Comic Metaphor Engine Marathon",
        marathon_id: Optional[str] = None,
    ):
        self.source_path = source_path
        self.output_dir = output_dir
        self.marathon_name = marathon_name
        self.marathon_id = marathon_id or source_path.stem or "comic_metaphor_marathon"

    def adapt(self) -> Path:
        results = self._load_results()
        if not results:
            raise ValueError("Benchmark file does not contain any entries")

        phases: List[Dict[str, Any]] = []
        total_duration_ms = 0
        total_tokens = 0
        total_cache_hits = 0
        total_phase_entries = 0
        success_flags: List[bool] = []
        errors: List[str] = []
        started_at: Optional[datetime] = None
        ended_at: Optional[datetime] = None
        for entry in results:
            success_flags.append(entry.get("success", False))
            total_duration_ms += entry.get("total_duration_ms", 0)
            total_tokens += entry.get("total_tokens", 0)

            if error := entry.get("error_message"):
                errors.append(error)

            for phase in entry.get("phase_metrics", []):
                phase_entry = self._build_phase_entry(phase, entry)
                phases.append(phase_entry)

                total_cache_hits += float(
                    phase.get("cache_hit_rate", int(bool(phase.get("cache_hit"))))
                )

                total_phase_entries += 1

                phase_start = self._parse_iso(phase.get("start_time"))
                phase_end = self._parse_iso(phase.get("end_time"))

                started_at = self._min_datetime(started_at, phase_start)
                ended_at = self._max_datetime(ended_at, phase_end)

        adapted = {
            "format": "tool_runs",
            "marathon_id": self.marathon_id,
            "marathon_name": self.marathon_name,
            "started_at": started_at.isoformat() if started_at else None,
            "ended_at": ended_at.isoformat() if ended_at else None,
            "timestamp": datetime.utcnow().timestamp(),
            "total_duration": total_duration_ms / 1000,
            "total_tokens": total_tokens,
            "files_generated": len(results),
            "success": all(success_flags),
            "errors": sorted(set(errors)),
            "cache_hit_rate": (
                (total_cache_hits / total_phase_entries)
                if total_phase_entries > 0
                else 0.0
            ),
            "memory_peak_mb": 0.0,
            "phases": phases,
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{self.marathon_id}_tool_runs.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(adapted, f, indent=2, ensure_ascii=False)

        return output_path

    def _build_phase_entry(
        self, phase: Dict[str, Any], entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        duration_ms = phase.get("duration_ms", 0) or 0
        duration_seconds = duration_ms / 1000.0

        return {
            "phase_name": phase.get("phase_name", phase.get("name", "unknown")),
            "duration_seconds": duration_seconds,
            "duration": duration_seconds,
            "duration_ms": duration_ms,
            "start_time": phase.get("start_time"),
            "end_time": phase.get("end_time"),
            "cache_hit": phase.get("cache_hit", False),
            "tokens_used": phase.get("tokens_used", 0),
            "memory_mb": phase.get("memory_mb", 0.0),
            "benchmark_id": entry.get("scenario_id"),
            "scenario_id": entry.get("scenario_id"),
            "success": entry.get("success", False),
            "files_generated": 1,
            "iterations": 1,
            "metadata": {
                "mapping_id": entry.get("output_mapping_id"),
                "narrative_id": entry.get("output_narrative_id"),
                "topic": entry.get("input_topic"),
            },
        }

    def _load_results(self) -> List[Dict[str, Any]]:
        with open(self.source_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Expected a list of benchmark results")

        return data

    @staticmethod
    def _parse_iso(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _min_datetime(
        first: Optional[datetime], second: Optional[datetime]
    ) -> Optional[datetime]:
        if first is None:
            return second
        if second is None:
            return first
        return first if first <= second else second

    @staticmethod
    def _max_datetime(
        first: Optional[datetime], second: Optional[datetime]
    ) -> Optional[datetime]:
        if first is None:
            return second
        if second is None:
            return first
        return first if first >= second else second


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Adapt Comic Metaphor benchmark results for the Performance Advisor."
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Path to the benchmark JSON file"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        help="Directory to write the adapted file (defaults to the input directory)",
    )
    parser.add_argument(
        "--marathon-name",
        "-n",
        default="Comic Metaphor Engine Marathon",
        help="Name used in the Marathon metadata",
    )
    parser.add_argument(
        "--marathon-id",
        "-m",
        help="Marathon ID override (defaults to the input filename stem)",
    )

    args = parser.parse_args()

    source_path = Path(args.input)
    if not source_path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {source_path}")

    output_dir = Path(args.output_dir) if args.output_dir else source_path.parent

    adapter = BenchmarkAdapter(
        source_path=source_path,
        output_dir=output_dir,
        marathon_name=args.marathon_name,
        marathon_id=args.marathon_id,
    )

    adapted_path = adapter.adapt()
    print(f"Adapted benchmark file: {adapted_path}")


if __name__ == "__main__":
    main()
