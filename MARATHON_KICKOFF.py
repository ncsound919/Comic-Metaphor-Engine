"""
CHEETAH V3 PRO - MARATHON KICK-OFF ORCHESTRATOR
================================================

Comic Book Metaphor Engine - Full System Build & Benchmark

This script orchestrates the complete marathon build:
1. Data ingestion from existing files
2. Index building for semantic search
3. Metaphor engine implementation
4. Narrative generation
5. Cheetah v3 tool integration
6. Comprehensive benchmarking
7. AI Performance Advisor analysis

Usage:
    python MARATHON_KICKOFF.py --full
    python MARATHON_KICKOFF.py --phase 1
    python MARATHON_KICKOFF.py --benchmark-only
"""

import argparse

# Fix Windows console encoding for emoji/Unicode
import io
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class MarathonOrchestrator:
    """Orchestrates the complete Cheetah v3 marathon build."""

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = Path(__file__).parent
        else:
            self.project_root = Path(project_root)

        self.cheetah_root = (
            self.project_root.parent.parent.parent.parent / "Overlay Cheetah v3 Pro"
        )
        self.processed_dir = self.project_root / "processed"
        self.output_dir = self.project_root / "output"
        self.benchmark_dir = self.project_root / "benchmarks"
        self.tests_dir = self.project_root / "tests"

        # Create directories
        self.processed_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        # Marathon state
        self.start_time = None
        self.phase_times = {}
        self.phase_results = {}
        self.errors = []

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "PHASE": "🔧",
            "BENCHMARK": "📊",
        }.get(level, "•")
        print(f"[{timestamp}] {prefix} {message}")

    def run_command(
        self, cmd: List[str], phase_name: str, capture_output: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Run a shell command and track timing."""
        self.log(f"Running: {' '.join(cmd)}")
        start = time.time()

        try:
            if capture_output:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=str(self.project_root),
                )
                output = result.stdout
            else:
                subprocess.run(cmd, check=True, cwd=str(self.project_root))
                output = None

            elapsed = time.time() - start
            self.phase_times[phase_name] = elapsed
            self.log(f"Completed in {elapsed:.2f}s", "SUCCESS")
            return True, output

        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start
            error_msg = f"Failed after {elapsed:.2f}s: {str(e)}"
            self.errors.append(
                {"phase": phase_name, "error": error_msg, "command": " ".join(cmd)}
            )
            self.log(error_msg, "ERROR")
            return False, None

    def check_dependencies(self) -> bool:
        """Check that all dependencies are installed."""
        self.log("Checking dependencies...", "PHASE")

        # Map package names to their actual import names
        package_imports = {
            "pandas": "pandas",
            "numpy": "numpy",
            "faiss-cpu": "faiss",
            "sentence-transformers": "sentence_transformers",
            "scikit-learn": "sklearn",
            "pytest": "pytest",
        }

        missing = []
        for package, import_name in package_imports.items():
            try:
                __import__(import_name)
            except ImportError:
                missing.append(package)

        if missing:
            self.log(f"Missing packages: {', '.join(missing)}", "ERROR")
            self.log("Run: pip install -r requirements.txt", "INFO")
            return False

        self.log("All dependencies satisfied", "SUCCESS")
        return True

    def phase_0_setup(self) -> bool:
        """Phase 0: Pre-flight checks and setup."""
        self.log("=" * 70, "PHASE")
        self.log("PHASE 0: Setup & Pre-flight Checks", "PHASE")
        self.log("=" * 70, "PHASE")

        # Check dependencies
        if not self.check_dependencies():
            return False

        # Verify source files exist
        required_files = [
            "Storylines for metaphor engine",
            "IHS_System_Foundations.json",
            "IHS_Execution_Tools.json",
            "codex_engine.py",
        ]

        for filename in required_files:
            filepath = self.project_root / filename
            if not filepath.exists():
                self.log(f"Missing required file: {filename}", "ERROR")
                return False

        self.log("All source files present", "SUCCESS")

        # Check Cheetah v3 availability
        if not self.cheetah_root.exists():
            self.log(f"Cheetah v3 not found at {self.cheetah_root}", "ERROR")
            return False

        self.log(f"Cheetah v3 found at {self.cheetah_root}", "SUCCESS")

        return True

    def phase_1_ingestion(self) -> bool:
        """Phase 1: Data ingestion and knowledge base construction."""
        self.log("=" * 70, "PHASE")
        self.log("PHASE 1: Data Ingestion & Knowledge Base", "PHASE")
        self.log("=" * 70, "PHASE")

        # Run ingestion script
        success, output = self.run_command(
            [sys.executable, "engine/ingest.py"], "phase_1_ingestion"
        )

        if not success:
            return False

        # Verify outputs
        expected_outputs = [
            self.processed_dir / "knowledge_base.json",
            self.processed_dir / "protocols.jsonl",
            self.processed_dir / "embeddings.npy",
        ]

        for output_file in expected_outputs:
            if not output_file.exists():
                self.log(f"Missing expected output: {output_file}", "ERROR")
                return False

        self.log("Knowledge base constructed successfully", "SUCCESS")

        # Load and display stats
        try:
            with open(self.processed_dir / "knowledge_base.json", "r") as f:
                kb_data = json.load(f)
                protocol_count = len(kb_data.get("protocols", {}))
                universe_count = len(kb_data.get("universes", {}))
                self.log(f"  → {protocol_count} protocols loaded", "INFO")
                self.log(f"  → {universe_count} universes loaded", "INFO")
                self.phase_results["phase_1"] = {
                    "protocols": protocol_count,
                    "universes": universe_count,
                }
        except Exception as e:
            self.log(f"Could not read KB stats: {e}", "WARNING")

        return True

    def phase_2_indexing(self) -> bool:
        """Phase 2: Build search index."""
        self.log("=" * 70, "PHASE")
        self.log("PHASE 2: Search Index Construction", "PHASE")
        self.log("=" * 70, "PHASE")

        success, _ = self.run_command(
            [sys.executable, "engine/index.py"], "phase_2_indexing"
        )

        return success

    def phase_3_engine(self) -> bool:
        """Phase 3: Metaphor engine implementation."""
        self.log("=" * 70, "PHASE")
        self.log("PHASE 3: Metaphor Engine", "PHASE")
        self.log("=" * 70, "PHASE")

        success, _ = self.run_command(
            [sys.executable, "engine/metaphor_engine.py"], "phase_3_engine"
        )

        return success

    def phase_4_generation(self) -> bool:
        """Phase 4: Narrative generation and explanation."""
        self.log("=" * 70, "PHASE")
        self.log("PHASE 4: Narrative Generation & Explanation", "PHASE")
        self.log("=" * 70, "PHASE")

        # Narrative generator
        success, _ = self.run_command(
            [sys.executable, "engine/narrative_generator.py"], "phase_4a_narrative"
        )
        if not success:
            return False

        # Explainer
        success, _ = self.run_command(
            [sys.executable, "engine/explainers.py"], "phase_4b_explainer"
        )

        return success

    def phase_5_integration(self) -> bool:
        """Phase 5: Cheetah v3 integration."""
        self.log("=" * 70, "PHASE")
        self.log("PHASE 5: Cheetah v3 Integration", "PHASE")
        self.log("=" * 70, "PHASE")

        # Tools interface
        success, _ = self.run_command(
            [sys.executable, "engine/tools_interface.py"], "phase_5_tools_interface"
        )

        return success

    def run_tests(self, test_pattern: Optional[str] = None) -> bool:
        """Run test suite."""
        self.log("=" * 70, "PHASE")
        self.log("Running Tests", "PHASE")
        self.log("=" * 70, "PHASE")

        if test_pattern:
            cmd = [sys.executable, "-m", "pytest", test_pattern, "-v"]
        else:
            cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]

        success, output = self.run_command(cmd, "tests", capture_output=True)

        if output:
            # Extract test results
            lines = output.split("\n")
            for line in lines:
                if "passed" in line or "failed" in line:
                    self.log(line, "INFO")

        return success

    def run_benchmark(self) -> bool:
        """Run full benchmark suite."""
        self.log("=" * 70, "BENCHMARK")
        self.log("BENCHMARK SUITE: Running All Scenarios", "BENCHMARK")
        self.log("=" * 70, "BENCHMARK")

        # Run benchmark script
        success, _ = self.run_command(
            [sys.executable, "benchmarks/run_benchmark.py", "--all", "--save-results"],
            "benchmark_full",
        )

        if not success:
            return False

        # Find latest benchmark results
        benchmark_results_dir = self.cheetah_root / "benchmark_results"
        if benchmark_results_dir.exists():
            result_files = list(benchmark_results_dir.glob("comic_metaphor_*.json"))
            if result_files:
                latest_result = max(result_files, key=lambda p: p.stat().st_mtime)
                self.log(f"Benchmark results saved to: {latest_result}", "SUCCESS")
                self.phase_results["benchmark_file"] = str(latest_result)

        return True

    def adapt_benchmark_for_advisor(self, benchmark_file: str) -> Optional[str]:
        adapter_script = self.project_root / "benchmarks" / "adapter.py"
        output_dir = self.cheetah_root / "benchmark_results"
        success, output = self.run_command(
            [
                sys.executable,
                str(adapter_script),
                "--input",
                benchmark_file,
                "--output-dir",
                str(output_dir),
            ],
            "benchmark_adapter",
            capture_output=True,
        )
        if not success:
            self.log("Benchmark adapter failed to execute", "ERROR")
            return None

        adapted_path = None
        if output:
            for line in output.splitlines():
                marker = "Adapted benchmark file:"
                if marker in line:
                    adapted_path = line.split(marker, 1)[1].strip()
                    break

        if not adapted_path:
            self.log("Benchmark adapter did not report an output path", "ERROR")
            return None

        self.log(f"Adapted benchmark JSON for advisor: {adapted_path}", "INFO")
        self.phase_results["adapted_benchmark_file"] = adapted_path
        return adapted_path

    def run_advisor(self) -> bool:
        """Run AI Performance Advisor on benchmark results."""
        self.log("=" * 70, "BENCHMARK")
        self.log("AI PERFORMANCE ADVISOR: Analyzing Results", "BENCHMARK")
        self.log("=" * 70, "BENCHMARK")

        benchmark_file = self.phase_results.get("benchmark_file")
        if not benchmark_file:
            self.log("No benchmark file found to analyze", "ERROR")
            return False

        adapted_file = self.adapt_benchmark_for_advisor(benchmark_file)
        if not adapted_file:
            return False

        # Run advisor
        advisor_cmd = [
            sys.executable,
            str(self.cheetah_root / "run_advisor.py"),
            "--dir",
            str(self.cheetah_root / "benchmark_results"),
        ]

        success, output = self.run_command(
            advisor_cmd, "advisor_analysis", capture_output=True
        )

        if output:
            self.log("Advisor Output:", "INFO")
            print(output)

        return success

    def generate_report(self) -> str:
        """Generate marathon completion report."""
        report = []
        report.append("\n" + "=" * 70)
        report.append("CHEETAH V3 MARATHON - COMPLETION REPORT")
        report.append("=" * 70)
        report.append(f"\nProject: Comic Book Metaphor Engine")
        report.append(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        total_time = sum(self.phase_times.values())
        report.append(
            f"\nTotal Duration: {total_time:.2f}s ({total_time / 60:.1f} minutes)"
        )

        report.append("\n" + "-" * 70)
        report.append("PHASE BREAKDOWN:")
        report.append("-" * 70)
        for phase, duration in self.phase_times.items():
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            report.append(f"  {phase:<30} {duration:>8.2f}s ({percentage:>5.1f}%)")

        if self.phase_results:
            report.append("\n" + "-" * 70)
            report.append("RESULTS:")
            report.append("-" * 70)
            for key, value in self.phase_results.items():
                report.append(f"  {key}: {value}")

        if self.errors:
            report.append("\n" + "-" * 70)
            report.append(f"ERRORS ({len(self.errors)}):")
            report.append("-" * 70)
            for error in self.errors:
                report.append(f"  Phase: {error['phase']}")
                report.append(f"  Error: {error['error']}")
                report.append(f"  Command: {error['command']}")
                report.append("")

        report.append("\n" + "=" * 70)
        report.append("END REPORT")
        report.append("=" * 70 + "\n")

        return "\n".join(report)

    def save_report(self, report: str):
        """Save report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"marathon_report_{timestamp}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        self.log(f"Report saved to: {report_file}", "SUCCESS")

    def run_full_marathon(self) -> bool:
        """Execute complete marathon build."""
        self.start_time = datetime.now()
        self.log("🚀 CHEETAH V3 MARATHON BUILD INITIATED", "PHASE")
        self.log(f"Target: Comic Book Metaphor Engine", "INFO")
        self.log(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")

        phases = [
            ("Phase 0: Setup", self.phase_0_setup),
            ("Phase 1: Ingestion", self.phase_1_ingestion),
            ("Phase 2: Indexing", self.phase_2_indexing),
            ("Phase 3: Engine", self.phase_3_engine),
            ("Phase 4: Generation", self.phase_4_generation),
            ("Phase 5: Integration", self.phase_5_integration),
            ("Tests", lambda: self.run_tests()),
            ("Benchmark", self.run_benchmark),
            ("Advisor", self.run_advisor),
        ]

        for phase_name, phase_func in phases:
            self.log(f"\n{'=' * 70}")
            self.log(f"Starting: {phase_name}")
            self.log(f"{'=' * 70}")

            success = phase_func()

            if not success:
                self.log(f"❌ {phase_name} FAILED", "ERROR")
                self.log("Marathon aborted", "ERROR")
                break
        else:
            # All phases completed
            self.log("\n🎉 MARATHON COMPLETED SUCCESSFULLY!", "SUCCESS")

        # Generate and save report
        report = self.generate_report()
        print(report)
        self.save_report(report)

        return len(self.errors) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cheetah v3 Marathon Build - Comic Book Metaphor Engine"
    )
    parser.add_argument(
        "--full", action="store_true", help="Run complete marathon build (all phases)"
    )
    parser.add_argument(
        "--phase", type=int, choices=[0, 1, 2, 3, 4, 5], help="Run specific phase only"
    )
    parser.add_argument(
        "--benchmark-only",
        action="store_true",
        help="Run benchmark suite only (assumes system built)",
    )
    parser.add_argument("--test-only", action="store_true", help="Run tests only")

    args = parser.parse_args()

    orchestrator = MarathonOrchestrator()

    if args.full:
        success = orchestrator.run_full_marathon()
        sys.exit(0 if success else 1)

    elif args.phase is not None:
        orchestrator.start_time = datetime.now()
        phase_map = {
            0: orchestrator.phase_0_setup,
            1: orchestrator.phase_1_ingestion,
            2: orchestrator.phase_2_indexing,
            3: orchestrator.phase_3_engine,
            4: orchestrator.phase_4_generation,
            5: orchestrator.phase_5_integration,
        }
        success = phase_map[args.phase]()
        sys.exit(0 if success else 1)

    elif args.benchmark_only:
        orchestrator.start_time = datetime.now()
        success = orchestrator.run_benchmark() and orchestrator.run_advisor()
        report = orchestrator.generate_report()
        print(report)
        sys.exit(0 if success else 1)

    elif args.test_only:
        orchestrator.start_time = datetime.now()
        success = orchestrator.run_tests()
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
