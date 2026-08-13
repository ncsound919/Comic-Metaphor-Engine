"""
Full Benchmark Runner
=====================

Executes end-to-end metaphor engine benchmarks across multiple scenarios.
Captures detailed metrics and saves results in Cheetah v3 format.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from engine.codex_adapter import score_metaphor_mapping
from engine.index import build_index
from engine.narrative_generator import generate_narrative
from engine.schema import (
    BenchmarkResult,
    FormatType,
    GenerationContext,
    KnowledgeBase,
    MetaphorMapping,
    PhaseMetrics,
    Protocol,
    ToneType,
)


class BenchmarkRunner:
    """Runner for executing metaphor engine benchmarks."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.processed_dir = self.project_root / "processed"
        self.scenarios_dir = self.project_root / "benchmarks" / "scenarios"
        self.results_dir = (
            self.project_root / "output" / "benchmarks"
        )  # Local output directory

        # Ensure results directory exists
        self.results_dir.mkdir(exist_ok=True)

        # Load knowledge base and build index
        self.kb = KnowledgeBase.load(str(self.processed_dir / "knowledge_base.json"))
        self.index = build_index(self.kb, str(self.processed_dir))

    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmark scenarios."""
        print("Starting Comic Metaphor Engine Benchmarks")
        print("=" * 50)

        # Load all scenarios
        scenarios = self._load_scenarios()
        print(f"Loaded {len(scenarios)} scenarios")

        results = []
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id", "unknown")
            if "input" not in scenario:
                print(
                    f"WARNING: Skipping scenario {scenario_id}: missing 'input' definition, "
                    "no benchmark executed"
                )
                continue

            try:
                result = self._run_scenario(scenario)
                results.append(result)
                print(f"[PASS] Completed scenario {scenario_id}")
            except Exception as e:
                print(f"[FAIL] Failed scenario {scenario_id}: {e}")
                # Create failed result
                result = BenchmarkResult(
                    id=f"benchmark_{scenario_id}",
                    scenario_id=scenario_id,
                    timestamp=datetime.utcnow(),
                    input_topic=scenario["input"]["topic"],
                    input_format=FormatType(scenario["input"]["format"]),
                    input_tone=ToneType(scenario["input"]["tone"]),
                    success=False,
                    error_message=str(e),
                )
                results.append(result)

        print(f"\nBenchmark run complete: {len(results)} results")
        return results

    def _load_scenarios(self) -> List[Dict[str, Any]]:
        """Load all scenario files."""
        scenarios = []
        for scenario_file in self.scenarios_dir.glob("*.json"):
            with open(scenario_file, "r", encoding="utf-8") as f:
                file_scenarios = json.load(f)
                scenarios.extend(file_scenarios)
        return scenarios

    def _run_scenario(self, scenario: Dict[str, Any]) -> BenchmarkResult:
        """Run a single benchmark scenario."""
        scenario_id = scenario["scenario_id"]
        input_data = scenario["input"]

        print(f"\n=> Running scenario: {scenario_id} - {scenario['name']}")

        # Initialize result
        result = BenchmarkResult(
            id=f"benchmark_{scenario_id}",
            scenario_id=scenario_id,
            timestamp=datetime.utcnow(),
            input_topic=input_data["topic"],
            input_format=FormatType(input_data["format"]),
            input_tone=ToneType(input_data["tone"]),
        )

        phase_metrics = []

        # Phase 1: Protocol Search
        start_time = time.time()
        try:
            protocols = self.index.search_protocols(input_data["topic"], top_k=3)
            duration = int((time.time() - start_time) * 1000)

            phase_metrics.append(
                PhaseMetrics(
                    phase_name="protocol_search",
                    start_time=datetime.fromtimestamp(start_time),
                    end_time=datetime.fromtimestamp(time.time()),
                    duration_ms=duration,
                    cache_hit_rate=self.index.get_cache_stats()["cache_hit_rate"],
                    tokens_used=0,  # Would track if using LLM
                    memory_mb=0.0,  # Would track actual memory
                )
            )

            if not protocols:
                raise ValueError("No protocols found for topic")

            # Use first protocol for mapping
            selected_protocol = protocols[0]
            result.output_mapping_id = f"mapping_{scenario_id}"

        except Exception as e:
            result.success = False
            result.error_message = f"Protocol search failed: {e}"
            return result

        # Phase 2: Mapping Creation
        start_time = time.time()
        try:
            mapping = MetaphorMapping(
                id=result.output_mapping_id,
                topic=input_data["topic"],
                domain=self._infer_domain(input_data["topic"]),
                target_format=result.input_format,
                target_tone=result.input_tone,
                protocol_id=selected_protocol.id,
                core_tension=self._generate_core_tension(
                    input_data["topic"], selected_protocol
                ),
                target_emotion=self._infer_emotion(result.input_tone),
                generation_source="benchmark_runner",
            )

            duration = int((time.time() - start_time) * 1000)
            phase_metrics.append(
                PhaseMetrics(
                    phase_name="mapping_creation",
                    start_time=datetime.fromtimestamp(start_time),
                    end_time=datetime.fromtimestamp(time.time()),
                    duration_ms=duration,
                )
            )

        except Exception as e:
            result.success = False
            result.error_message = f"Mapping creation failed: {e}"
            return result

        # Phase 3: Codex Scoring
        start_time = time.time()
        try:
            mapping = score_metaphor_mapping(
                mapping, selected_protocol, index=self.index
            )
            duration = int((time.time() - start_time) * 1000)

            phase_metrics.append(
                PhaseMetrics(
                    phase_name="codex_scoring",
                    start_time=datetime.fromtimestamp(start_time),
                    end_time=datetime.fromtimestamp(time.time()),
                    duration_ms=duration,
                )
            )

            # Update result with scores
            result.codex_scores = {
                "trueness": mapping.trueness_score,
                "flow": mapping.flow_score,
                "pcs": mapping.pcs_score,
                "tap": mapping.tap_score,
            }
            result.tap_score = mapping.tap_score

        except Exception as e:
            result.success = False
            result.error_message = f"Codex scoring failed: {e}"
            return result

        # Phase 4: Narrative Generation
        start_time = time.time()
        try:
            context = GenerationContext(
                mapping=mapping,
                protocol=selected_protocol,
                word_count_target=input_data.get("target_word_count", 1000),
                avoid_topics=input_data.get("constraints", {}).get("avoid_topics", []),
                required_elements=input_data.get("constraints", {}).get(
                    "required_elements", []
                ),
            )

            narrative = generate_narrative(context)
            duration = int((time.time() - start_time) * 1000)

            phase_metrics.append(
                PhaseMetrics(
                    phase_name="narrative_generation",
                    start_time=datetime.fromtimestamp(start_time),
                    end_time=datetime.fromtimestamp(time.time()),
                    duration_ms=duration,
                )
            )

            result.output_narrative_id = narrative.id

        except Exception as e:
            result.success = False
            result.error_message = f"Narrative generation failed: {e}"
            return result

        # Calculate aggregate metrics
        result.phase_metrics = phase_metrics
        result.total_duration_ms = sum(p.duration_ms for p in phase_metrics)
        result.total_tokens = sum(p.tokens_used for p in phase_metrics)
        result.cache_hit_rate = (
            sum(p.cache_hit_rate for p in phase_metrics) / len(phase_metrics)
            if phase_metrics
            else 0.0
        )
        result.success = True

        return result

    def _infer_domain(self, topic: str) -> str:
        """Infer domain from topic (simplified)."""
        topic_lower = topic.lower()
        if "startup" in topic_lower or "business" in topic_lower:
            return "business"
        elif "health" in topic_lower or "mental" in topic_lower:
            return "health"
        else:
            return "general"

    def _generate_core_tension(self, topic: str, protocol: Protocol) -> str:
        """Generate core tension from topic and protocol."""
        return f"Tension between {topic} and {protocol.business_logic[:50]}..."

    def _infer_emotion(self, tone: ToneType) -> str:
        """Infer target emotion from tone."""
        mapping = {
            ToneType.HOPEFUL: "inspiration",
            ToneType.GRITTY: "resilience",
            ToneType.CAUTIONARY: "caution",
            ToneType.PHILOSOPHICAL: "understanding",
        }
        return mapping.get(tone, "transformation")

    def save_results(
        self, results: List[BenchmarkResult], filename: Optional[str] = None
    ) -> str:
        """Save benchmark results in Cheetah format."""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"comic_metaphor_{timestamp}.json"

        filepath = self.results_dir / filename

        # Convert to Cheetah format (list of results)
        cheetah_results = [result.to_dict() for result in results]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(cheetah_results, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(results)} benchmark results to {filepath}")
        return str(filepath)


def main():
    """Main benchmark execution."""
    runner = BenchmarkRunner()

    # Run all benchmarks
    results = runner.run_all_benchmarks()

    # Save results
    saved_path = runner.save_results(results)

    # Print summary
    successful = sum(1 for r in results if r.success)
    total_duration = sum(r.total_duration_ms for r in results if r.success)

    print("\n=== Benchmark Summary ===")
    print(f"  Total scenarios: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")
    print(f"  Average duration: {total_duration // max(successful, 1)}ms per scenario")
    print(f"  Results saved to: {saved_path}")

    return results


if __name__ == "__main__":
    results = main()
