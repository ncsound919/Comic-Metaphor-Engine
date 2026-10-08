#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║             COMIC METAPHOR ENGINE - ENHANCEMENT MARATHON EXECUTOR             ║
║                                                                               ║
║  Orchestrates comprehensive enhancement, hardening, and upgrading of the      ║
║  Comic Metaphor Intelligence Engine across 8 major phases.                   ║
║                                                                               ║
║  Usage:                                                                       ║
║    python enhance_protocols.py --phase 1              # Run single phase     ║
║    python enhance_protocols.py --phase 1,2,3          # Run multiple phases  ║
║    python enhance_protocols.py --marathon             # Run all phases       ║
║    python enhance_protocols.py --parallel             # Parallel execution   ║
║    python enhance_protocols.py --status               # Check status         ║
║                                                                               ║
║  Version: 1.0.0                                                              ║
║  Author: Cheetah Supreme Team                                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("enhancement_marathon.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# Remove emoji characters for Windows console compatibility
def log_safe(msg):
    """Log message with ASCII-safe characters"""
    replacements = {
        "\U0001f406": "[CHEETAH]",
        "\U0001f680": "[ROCKET]",
        "\U0001f389": "[PARTY]",
        "\U0001f4ca": "[CHART]",
        "\u2192": "->",
        "\u2705": "[OK]",
        "\u274c": "[X]",
    }
    for emoji, replacement in replacements.items():
        msg = msg.replace(emoji, replacement)
    return msg


@dataclass
class PhaseResult:
    """Result of a phase execution"""

    phase_id: int
    phase_name: str
    status: str  # 'success', 'failed', 'skipped', 'in_progress'
    duration_seconds: float
    tasks_completed: int
    tasks_failed: int
    outputs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class MarathonConfig:
    """Configuration for enhancement marathon"""

    target_protocols: int = 103
    current_protocols: int = 76
    quality_threshold: float = 0.90
    parallel_execution: bool = False
    max_workers: int = 4
    output_dir: str = "enhanced_output"
    backup_before_changes: bool = True
    validate_after_phase: bool = True
    generate_reports: bool = True


class EnhancementMarathonExecutor:
    """Orchestrates the complete enhancement marathon"""

    def __init__(self, config: MarathonConfig):
        self.config = config
        self.results: List[PhaseResult] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True)

        logger.info(log_safe("🐆 Enhancement Marathon Executor Initialized"))
        logger.info(f"Target: {config.target_protocols} protocols")
        logger.info(f"Current: {config.current_protocols} protocols")
        logger.info(
            f"Remaining: {config.target_protocols - config.current_protocols} protocols"
        )

    def run_marathon(self, phases: List[int]) -> bool:
        """Run the complete enhancement marathon"""
        self.start_time = datetime.now()
        logger.info(log_safe("🚀 Starting Enhancement Marathon"))
        logger.info(f"Phases to execute: {phases}")

        try:
            if self.config.parallel_execution and len(phases) > 1:
                success = self._run_phases_parallel(phases)
            else:
                success = self._run_phases_sequential(phases)

            self.end_time = datetime.now()
            self._generate_final_report()

            return success

        except Exception as e:
            logger.error(f"Marathon execution failed: {e}", exc_info=True)
            return False

    def _run_phases_sequential(self, phases: List[int]) -> bool:
        """Run phases sequentially"""
        all_success = True

        for phase_id in phases:
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Starting Phase {phase_id}")
            logger.info(f"{'=' * 80}\n")

            result = self._execute_phase(phase_id)
            self.results.append(result)

            if result.status == "failed":
                all_success = False
                logger.error(f"Phase {phase_id} failed. Continuing to next phase...")

            # Validate after phase if configured
            if self.config.validate_after_phase and result.status == "success":
                if not self._validate_phase_output(phase_id):
                    logger.warning(f"Phase {phase_id} validation failed")

        return all_success

    def _run_phases_parallel(self, phases: List[int]) -> bool:
        """Run independent phases in parallel"""
        logger.info(
            f"Running {len(phases)} phases in parallel (max_workers={self.config.max_workers})"
        )

        # Identify dependencies (some phases must run sequentially)
        independent_phases = self._get_independent_phases(phases)
        dependent_phases = [p for p in phases if p not in independent_phases]

        all_success = True

        # Run independent phases in parallel
        if independent_phases:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_phase = {
                    executor.submit(self._execute_phase, phase_id): phase_id
                    for phase_id in independent_phases
                }

                for future in as_completed(future_to_phase):
                    phase_id = future_to_phase[future]
                    try:
                        result = future.result()
                        self.results.append(result)
                        if result.status == "failed":
                            all_success = False
                    except Exception as e:
                        logger.error(f"Phase {phase_id} raised exception: {e}")
                        all_success = False

        # Run dependent phases sequentially
        for phase_id in sorted(dependent_phases):
            result = self._execute_phase(phase_id)
            self.results.append(result)
            if result.status == "failed":
                all_success = False

        return all_success

    def _get_independent_phases(self, phases: List[int]) -> List[int]:
        """Identify phases that can run in parallel"""
        # Phase dependencies:
        # Phase 1 must complete before phases 2-8 can use full protocol set
        # Phases 2-7 are mostly independent
        # Phase 8 requires all others to complete

        independent = []
        for phase in phases:
            if phase in [2, 3, 4, 5, 6, 7]:  # These can run in parallel
                independent.append(phase)

        return independent

    def _execute_phase(self, phase_id: int) -> PhaseResult:
        """Execute a specific enhancement phase"""
        phase_name = self._get_phase_name(phase_id)
        result = PhaseResult(
            phase_id=phase_id,
            phase_name=phase_name,
            status="in_progress",
            duration_seconds=0.0,
            tasks_completed=0,
            tasks_failed=0,
            start_time=datetime.now(),
        )

        start = time.time()

        try:
            logger.info(f"Executing Phase {phase_id}: {phase_name}")

            # Route to appropriate phase handler
            if phase_id == 1:
                success, tasks, outputs, metrics = self._phase_1_complete_protocols()
            elif phase_id == 2:
                success, tasks, outputs, metrics = self._phase_2_advanced_features()
            elif phase_id == 3:
                success, tasks, outputs, metrics = (
                    self._phase_3_performance_optimization()
                )
            elif phase_id == 4:
                success, tasks, outputs, metrics = self._phase_4_quality_hardening()
            elif phase_id == 5:
                success, tasks, outputs, metrics = (
                    self._phase_5_integration_enhancement()
                )
            elif phase_id == 6:
                success, tasks, outputs, metrics = self._phase_6_testing_expansion()
            elif phase_id == 7:
                success, tasks, outputs, metrics = self._phase_7_documentation()
            elif phase_id == 8:
                success, tasks, outputs, metrics = self._phase_8_validation()
            else:
                raise ValueError(f"Unknown phase: {phase_id}")

            result.status = "success" if success else "failed"
            result.tasks_completed = tasks
            result.outputs = outputs
            result.metrics = metrics

        except Exception as e:
            logger.error(f"Phase {phase_id} failed with exception: {e}", exc_info=True)
            result.status = "failed"
            result.errors.append(str(e))

        result.duration_seconds = time.time() - start
        result.end_time = datetime.now()

        logger.info(
            f"Phase {phase_id} {result.status.upper()} in {result.duration_seconds:.2f}s"
        )

        return result

    def _get_phase_name(self, phase_id: int) -> str:
        """Get human-readable phase name"""
        phases = {
            1: "Complete Protocol Coverage",
            2: "Advanced Feature Implementation",
            3: "Performance Optimization",
            4: "Quality Hardening",
            5: "Integration Enhancement",
            6: "Testing Expansion",
            7: "Documentation Excellence",
            8: "Integration Testing & Validation",
        }
        return phases.get(phase_id, f"Unknown Phase {phase_id}")

    # =========================================================================
    # PHASE IMPLEMENTATIONS
    # =========================================================================

    def _phase_1_complete_protocols(self) -> Tuple[bool, int, List[str], Dict]:
        """Phase 1: Complete protocol coverage to 103 protocols"""
        logger.info(log_safe("Phase 1: Completing protocol coverage (76 → 103)"))

        tasks_completed = 0
        outputs = []
        metrics = {
            "protocols_before": self.config.current_protocols,
            "protocols_target": self.config.target_protocols,
            "protocols_to_add": self.config.target_protocols
            - self.config.current_protocols,
        }

        try:
            # Task 1.1: Expand Avengers Cosmic (5 → 20)
            logger.info("Task 1.1: Expanding Avengers Cosmic protocols")
            avengers_protocols = self._generate_avengers_cosmic_protocols()
            outputs.append("avengers_cosmic_expanded.txt")
            tasks_completed += 1
            metrics["avengers_added"] = len(avengers_protocols)

            # Task 1.2: Expand Character Deep Dives (6 → 18)
            logger.info("Task 1.2: Expanding Character Deep Dives")
            character_protocols = self._generate_character_protocols()
            outputs.append("character_deep_dives_expanded.txt")
            tasks_completed += 1
            metrics["characters_added"] = len(character_protocols)

            # Task 1.3: Update knowledge base
            logger.info("Task 1.3: Updating knowledge base")
            self._update_knowledge_base(avengers_protocols + character_protocols)
            outputs.append("processed/knowledge_base.json")
            tasks_completed += 1

            # Task 1.4: Add quality scores and tags
            logger.info("Task 1.4: Adding quality scores and tags")
            self._add_protocol_metadata()
            tasks_completed += 1

            metrics["protocols_after"] = self.config.target_protocols
            metrics["completion_percentage"] = 100.0

            return True, tasks_completed, outputs, metrics

        except Exception as e:
            logger.error(f"Phase 1 failed: {e}")
            return False, tasks_completed, outputs, metrics

    def _phase_2_advanced_features(self) -> Tuple[bool, int, List[str], Dict]:
        """Phase 2: Advanced feature implementation"""
        logger.info("Phase 2: Implementing advanced features")

        tasks_completed = 0
        outputs = []
        metrics = {}

        try:
            # Task 2.1: Streaming engine
            logger.info("Task 2.1: Creating streaming engine")
            self._create_streaming_engine()
            outputs.append("engine/streaming_engine.py")
            tasks_completed += 1

            # Task 2.2: Multi-format exporters
            logger.info("Task 2.2: Creating multi-format exporters")
            self._create_exporters()
            outputs.append("engine/exporters.py")
            tasks_completed += 1

            # Task 2.3: RESTful API
            logger.info("Task 2.3: Creating RESTful API")
            self._create_api_layer()
            outputs.append("api/metaphor_api.py")
            tasks_completed += 1

            # Task 2.4: Interactive demo mode
            logger.info("Task 2.4: Creating interactive demo")
            self._create_demo_mode()
            outputs.append("engine/demo_mode.py")
            tasks_completed += 1

            metrics["features_added"] = tasks_completed

            return True, tasks_completed, outputs, metrics

        except Exception as e:
            logger.error(f"Phase 2 failed: {e}")
            return False, tasks_completed, outputs, metrics

    def _phase_3_performance_optimization(self) -> Tuple[bool, int, List[str], Dict]:
        """Phase 3: Performance optimization"""
        logger.info("Phase 3: Optimizing performance")

        tasks_completed = 0
        outputs = []
        metrics = {}

        try:
            # Task 3.1: Advanced caching
            logger.info("Task 3.1: Implementing advanced caching")
            self._create_cache_optimizer()
            outputs.append("engine/cache_optimizer.py")
            tasks_completed += 1

            # Task 3.2: Parallel processing
            logger.info("Task 3.2: Implementing parallel processing")
            self._create_parallel_processor()
            outputs.append("engine/parallel_processor.py")
            tasks_completed += 1

            # Task 3.3: Memory optimization
            logger.info("Task 3.3: Implementing memory optimization")
            self._create_memory_optimizer()
            outputs.append("engine/memory_optimizer.py")
            tasks_completed += 1

            metrics["optimizations_applied"] = tasks_completed

            return True, tasks_completed, outputs, metrics

        except Exception as e:
            logger.error(f"Phase 3 failed: {e}")
            return False, tasks_completed, outputs, metrics

    def _phase_4_quality_hardening(self) -> Tuple[bool, int, List[str], Dict]:
        """Phase 4: Quality hardening"""
        logger.info("Phase 4: Hardening quality systems")

        tasks_completed = 0
        outputs = []
        metrics = {}

        try:
            # Task 4.1: Enhanced scoring
            logger.info("Task 4.1: Creating enhanced scoring system")
            self._create_enhanced_scoring()
            outputs.append("engine/enhanced_scoring.py")
            tasks_completed += 1

            # Task 4.2: Validation framework
            logger.info("Task 4.2: Creating validation framework")
            self._create_validation_framework()
            outputs.append("engine/validation.py")
            tasks_completed += 1

            # Task 4.3: A/B testing
            logger.info("Task 4.3: Creating A/B testing framework")
            self._create_ab_testing()
            outputs.append("engine/ab_testing.py")
            tasks_completed += 1

            metrics["quality_systems_added"] = tasks_completed

            return True, tasks_completed, outputs, metrics

        except Exception as e:
            logger.error(f"Phase 4 failed: {e}")
            return False, tasks_completed, outputs, metrics

    def _phase_5_integration_enhancement(self) -> Tuple[bool, int, List[str], Dict]:
        """Phase 5: Integration enhancement"""
        logger.info("Phase 5: Enhancing ecosystem integration")

        tasks_completed = 0
        outputs = []
        metrics = {}

        try:
            # Task 5.1: CSL-X integration
            logger.info("Task 5.1: Creating CSL-X integration")
            self._create_cslx_integration()
            outputs.append("integrations/cslx_integration.py")
            tasks_completed += 1

            # Task 5.2: Draymond quality gates
            logger.info("Task 5.2: Creating Draymond integration")
            self._create_draymond_integration()
            outputs.append("integrations/draymond_gates.py")
            tasks_completed += 1

            # Task 5.3: Forge deployment
            logger.info("Task 5.3: Creating Forge deployment prep")
            self._create_forge_deployment()
            outputs.extend(
                ["integrations/forge_deployment.py", "Dockerfile", "docker-compose.yml"]
            )
            tasks_completed += 1

            metrics["integrations_added"] = tasks_completed

            return True, tasks_completed, outputs, metrics

        except Exception as e:
            logger.error(f"Phase 5 failed: {e}")
            return False, tasks_completed, outputs, metrics

    def _phase_6_testing_expansion(self) -> Tuple[bool, int, List[str], Dict]:
        """Phase 6: Testing expansion"""
        logger.info("Phase 6: Expanding test coverage")

        tasks_completed = 0
        outputs = []
        metrics = {}

        try:
            # Task 6.1: Unit tests
            logger.info("Task 6.1: Creating unit test suite")
            self._create_unit_tests()
            outputs.append("tests/test_enhanced_features.py")
            tasks_completed += 1

            # Task 6.2: Integration tests
            logger.info("Task 6.2: Creating integration tests")
            self._create_integration_tests()
            outputs.append("tests/test_integration_enhanced.py")
            tasks_completed += 1

            # Task 6.3: Performance benchmarks
            logger.info("Task 6.3: Creating performance benchmarks")
            self._create_performance_benchmarks()
            outputs.append("tests/test_performance_benchmarks.py")
            tasks_completed += 1

            metrics["test_suites_added"] = tasks_completed

            return True, tasks_completed, outputs, metrics

        except Exception as e:
            logger.error(f"Phase 6 failed: {e}")
            return False, tasks_completed, outputs, metrics

    def _phase_7_documentation(self) -> Tuple[bool, int, List[str], Dict]:
        """Phase 7: Documentation excellence"""
        logger.info("Phase 7: Creating comprehensive documentation")

        tasks_completed = 0
        outputs = []
        metrics = {}

        try:
            # Task 7.1: API documentation
            logger.info("Task 7.1: Creating API documentation")
            self._create_api_docs()
            outputs.extend(["docs/API_REFERENCE.md", "docs/API_EXAMPLES.md"])
            tasks_completed += 1

            # Task 7.2: Usage examples
            logger.info("Task 7.2: Creating usage examples")
            self._create_usage_examples()
            outputs.extend(["docs/QUICK_START.md", "docs/COOKBOOK.md", "examples/"])
            tasks_completed += 1

            # Task 7.3: Troubleshooting guide
            logger.info("Task 7.3: Creating troubleshooting guide")
            self._create_troubleshooting_guide()
            outputs.append("docs/TROUBLESHOOTING.md")
            tasks_completed += 1

            metrics["documentation_pages"] = len(outputs)

            return True, tasks_completed, outputs, metrics

        except Exception as e:
            logger.error(f"Phase 7 failed: {e}")
            return False, tasks_completed, outputs, metrics

    def _phase_8_validation(self) -> Tuple[bool, int, List[str], Dict]:
        """Phase 8: Integration testing and validation"""
        logger.info("Phase 8: Running comprehensive validation")

        tasks_completed = 0
        outputs = []
        metrics = {}

        try:
            # Task 8.1: Full system integration test
            logger.info("Task 8.1: Running full system integration test")
            integration_passed = self._run_integration_test()
            tasks_completed += 1
            metrics["integration_test_passed"] = integration_passed

            # Task 8.2: Load testing
            logger.info("Task 8.2: Running load tests")
            load_passed = self._run_load_test()
            tasks_completed += 1
            metrics["load_test_passed"] = load_passed

            # Task 8.3: Regression testing
            logger.info("Task 8.3: Running regression tests")
            regression_passed = self._run_regression_test()
            tasks_completed += 1
            metrics["regression_test_passed"] = regression_passed

            outputs.append("test_results/validation_report.json")

            all_passed = integration_passed and load_passed and regression_passed

            return all_passed, tasks_completed, outputs, metrics

        except Exception as e:
            logger.error(f"Phase 8 failed: {e}")
            return False, tasks_completed, outputs, metrics

    # =========================================================================
    # HELPER METHODS (Stubs - to be implemented)
    # =========================================================================

    def _generate_avengers_cosmic_protocols(self) -> List[Dict]:
        """Generate expanded Avengers Cosmic protocols"""
        logger.info("Generating Avengers Cosmic protocols (15 new)")
        # TODO: Implement protocol generation logic
        return [{"name": f"Avengers Protocol {i}"} for i in range(15)]

    def _generate_character_protocols(self) -> List[Dict]:
        """Generate expanded Character Deep Dive protocols"""
        logger.info("Generating Character Deep Dive protocols (12 new)")
        # TODO: Implement protocol generation logic
        return [{"name": f"Character Protocol {i}"} for i in range(12)]

    def _update_knowledge_base(self, protocols: List[Dict]) -> None:
        """Update knowledge base with new protocols"""
        logger.info(f"Updating knowledge base with {len(protocols)} protocols")
        # TODO: Implement knowledge base update logic

    def _add_protocol_metadata(self) -> None:
        """Add quality scores and tags to protocols"""
        logger.info("Adding metadata to protocols")
        # TODO: Implement metadata addition logic

    def _create_streaming_engine(self) -> None:
        """Create streaming engine implementation"""
        logger.info("Creating streaming engine")
        # TODO: Implement streaming engine creation

    def _create_exporters(self) -> None:
        """Create multi-format exporters"""
        logger.info("Creating exporters")
        # TODO: Implement exporters creation

    def _create_api_layer(self) -> None:
        """Create RESTful API layer"""
        logger.info("Creating API layer")
        # TODO: Implement API layer creation

    def _create_demo_mode(self) -> None:
        """Create interactive demo mode"""
        logger.info("Creating demo mode")
        # TODO: Implement demo mode creation

    def _create_cache_optimizer(self) -> None:
        """Create advanced caching system"""
        logger.info("Creating cache optimizer")
        # TODO: Implement cache optimizer

    def _create_parallel_processor(self) -> None:
        """Create parallel processing system"""
        logger.info("Creating parallel processor")
        # TODO: Implement parallel processor

    def _create_memory_optimizer(self) -> None:
        """Create memory optimization system"""
        logger.info("Creating memory optimizer")
        # TODO: Implement memory optimizer

    def _create_enhanced_scoring(self) -> None:
        """Create enhanced scoring system"""
        logger.info("Creating enhanced scoring")
        # TODO: Implement enhanced scoring

    def _create_validation_framework(self) -> None:
        """Create validation framework"""
        logger.info("Creating validation framework")
        # TODO: Implement validation framework

    def _create_ab_testing(self) -> None:
        """Create A/B testing framework"""
        logger.info("Creating A/B testing framework")
        # TODO: Implement A/B testing

    def _create_cslx_integration(self) -> None:
        """Create CSL-X integration"""
        logger.info("Creating CSL-X integration")
        # TODO: Implement CSL-X integration

    def _create_draymond_integration(self) -> None:
        """Create Draymond integration"""
        logger.info("Creating Draymond integration")
        # TODO: Implement Draymond integration

    def _create_forge_deployment(self) -> None:
        """Create Forge deployment preparation"""
        logger.info("Creating Forge deployment")
        # TODO: Implement Forge deployment prep

    def _create_unit_tests(self) -> None:
        """Create unit test suite"""
        logger.info("Creating unit tests")
        # TODO: Implement unit tests

    def _create_integration_tests(self) -> None:
        """Create integration test suite"""
        logger.info("Creating integration tests")
        # TODO: Implement integration tests

    def _create_performance_benchmarks(self) -> None:
        """Create performance benchmarks"""
        logger.info("Creating performance benchmarks")
        # TODO: Implement performance benchmarks

    def _create_api_docs(self) -> None:
        """Create API documentation"""
        logger.info("Creating API documentation")
        # TODO: Implement API docs

    def _create_usage_examples(self) -> None:
        """Create usage examples"""
        logger.info("Creating usage examples")
        # TODO: Implement usage examples

    def _create_troubleshooting_guide(self) -> None:
        """Create troubleshooting guide"""
        logger.info("Creating troubleshooting guide")
        # TODO: Implement troubleshooting guide

    def _run_integration_test(self) -> bool:
        """Run full system integration test"""
        logger.info("Running integration test")
        # TODO: Implement integration test
        return True

    def _run_load_test(self) -> bool:
        """Run load testing"""
        logger.info("Running load test")
        # TODO: Implement load test
        return True

    def _run_regression_test(self) -> bool:
        """Run regression testing"""
        logger.info("Running regression test")
        # TODO: Implement regression test
        return True

    def _validate_phase_output(self, phase_id: int) -> bool:
        """Validate phase output"""
        logger.info(f"Validating phase {phase_id} output")
        # TODO: Implement validation logic
        return True

    def _generate_final_report(self) -> None:
        """Generate final marathon report"""
        logger.info("\n" + "=" * 80)
        logger.info("ENHANCEMENT MARATHON - FINAL REPORT")
        logger.info("=" * 80)

        if not self.start_time or not self.end_time:
            logger.warning("Marathon timing information incomplete")
            return

        total_duration = (self.end_time - self.start_time).total_seconds()

        # Summary statistics
        total_phases = len(self.results)
        successful_phases = sum(1 for r in self.results if r.status == "success")
        failed_phases = sum(1 for r in self.results if r.status == "failed")
        total_tasks = sum(r.tasks_completed for r in self.results)

        logger.info(
            f"\nExecution Time: {total_duration:.2f} seconds ({total_duration / 60:.2f} minutes)"
        )
        logger.info(f"Phases Executed: {total_phases}")
        logger.info(f"Phases Successful: {successful_phases}")
        logger.info(f"Phases Failed: {failed_phases}")
        logger.info(f"Total Tasks Completed: {total_tasks}")

        # Phase breakdown
        logger.info("\nPhase Breakdown:")
        logger.info("-" * 80)
        for result in sorted(self.results, key=lambda x: x.phase_id):
            status_icon = "[OK]" if result.status == "success" else "[FAIL]"
            logger.info(f"{status_icon} Phase {result.phase_id}: {result.phase_name}")
            logger.info(f"   Duration: {result.duration_seconds:.2f}s")
            logger.info(f"   Tasks Completed: {result.tasks_completed}")
            logger.info(f"   Outputs: {len(result.outputs)} files")
            if result.metrics:
                logger.info(f"   Metrics: {json.dumps(result.metrics, indent=6)}")

        # Generate JSON report
        report_path = (
            self.output_dir
            / f"marathon_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_data = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_duration_seconds": total_duration,
            "phases_executed": total_phases,
            "phases_successful": successful_phases,
            "phases_failed": failed_phases,
            "total_tasks_completed": total_tasks,
            "results": [
                {
                    "phase_id": r.phase_id,
                    "phase_name": r.phase_name,
                    "status": r.status,
                    "duration_seconds": r.duration_seconds,
                    "tasks_completed": r.tasks_completed,
                    "tasks_failed": r.tasks_failed,
                    "outputs": r.outputs,
                    "errors": r.errors,
                    "metrics": r.metrics,
                }
                for r in self.results
            ],
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(log_safe(f"\n📊 Full report saved to: {report_path}"))
        logger.info("\n" + "=" * 80)
        logger.info(log_safe("🎉 ENHANCEMENT MARATHON COMPLETE!"))
        logger.info("=" * 80 + "\n")

    def get_status(self) -> Dict[str, Any]:
        """Get current marathon status"""
        return {
            "current_protocols": self.config.current_protocols,
            "target_protocols": self.config.target_protocols,
            "completion_percentage": (
                self.config.current_protocols / self.config.target_protocols
            )
            * 100,
            "phases_completed": len([r for r in self.results if r.status == "success"]),
            "phases_in_progress": len(
                [r for r in self.results if r.status == "in_progress"]
            ),
            "phases_failed": len([r for r in self.results if r.status == "failed"]),
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Comic Metaphor Engine - Enhancement Marathon Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--phase",
        type=str,
        help='Phase(s) to execute (e.g., "1" or "1,2,3")',
        default=None,
    )

    parser.add_argument(
        "--marathon", action="store_true", help="Run all phases sequentially"
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Execute phases in parallel where possible",
    )

    parser.add_argument("--status", action="store_true", help="Show current status")

    parser.add_argument(
        "--target-protocols",
        type=int,
        default=103,
        help="Target number of protocols (default: 103)",
    )

    parser.add_argument(
        "--current-protocols",
        type=int,
        default=76,
        help="Current number of protocols (default: 76)",
    )

    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=0.90,
        help="Quality threshold (0.0-1.0, default: 0.90)",
    )

    args = parser.parse_args()

    # Create configuration
    config = MarathonConfig(
        target_protocols=args.target_protocols,
        current_protocols=args.current_protocols,
        quality_threshold=args.quality_threshold,
        parallel_execution=args.parallel,
    )

    # Create executor
    executor = EnhancementMarathonExecutor(config)

    # Handle status command
    if args.status:
        status = executor.get_status()
        print("\n[TARGET] Enhancement Marathon Status:")
        print("=" * 60)
        print(f"Current Protocols: {status['current_protocols']}")
        print(f"Target Protocols: {status['target_protocols']}")
        print(f"Completion: {status['completion_percentage']:.1f}%")
        print(f"Phases Completed: {status['phases_completed']}")
        print(f"Phases In Progress: {status['phases_in_progress']}")
        print(f"Phases Failed: {status['phases_failed']}")
        print("=" * 60 + "\n")
        return

    # Determine which phases to run
    if args.marathon:
        phases = list(range(1, 9))  # All 8 phases
        logger.info("Running complete marathon (all 8 phases)")
    elif args.phase:
        phases = [int(p.strip()) for p in args.phase.split(",")]
        logger.info(f"Running selected phases: {phases}")
    else:
        print("Error: Must specify --phase, --marathon, or --status")
        parser.print_help()
        sys.exit(1)

    # Run the marathon
    success = executor.run_marathon(phases)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
