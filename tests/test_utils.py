"""
Test Utilities for Comic Metaphor Engine

Common utilities for all test types:
- Test data generation
- Mock objects
- Assertion helpers
- Performance measurement
"""

import json
import time
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, MagicMock, patch

class TestDataGenerator:
    """Generate test data for various scenarios"""

    @staticmethod
    def generate_protocol(id_suffix: str = "test") -> Dict[str, Any]:
        """Generate a test protocol"""
        return {
            "id": f"protocol_{id_suffix}",
            "title": f"Test Protocol {id_suffix}",
            "description": f"This is a test protocol for {id_suffix}",
            "dimensions": {
                "D1": f"Test dimension 1 for {id_suffix}",
                "D2": f"Test dimension 2 for {id_suffix}",
                "D3": f"Test dimension 3 for {id_suffix}",
                "D4": f"Test dimension 4 for {id_suffix}"
            },
            "metadata": {
                "category": "test",
                "complexity": "medium",
                "risk_level": "low"
            }
        }

    @staticmethod
    def generate_content(format_type: str = "markdown") -> Dict[str, Any]:
        """Generate test content"""
        return {
            "title": "Test Content",
            "body": "# Test Content\n\nThis is test content for validation.",
            "format": format_type,
            "metadata": {
                "generated_at": "2024-01-01T00:00:00Z",
                "source": "test_generator",
                "quality_score": 0.8
            }
        }

class PerformanceTimer:
    """Measure performance of operations"""

    def __init__(self):
        self.measurements = {}

    def measure(self, operation_name: str):
        """Context manager for timing operations"""
        class TimerContext:
            def __init__(self, timer, name):
                self.timer = timer
                self.name = name
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.time() - self.start_time
                self.timer.measurements[self.name] = elapsed

        return TimerContext(self, operation_name)

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.measurements:
            return {}

        values = list(self.measurements.values())
        return {
            "total_operations": len(values),
            "total_time": sum(values),
            "average_time": sum(values) / len(values),
            "min_time": min(values),
            "max_time": max(values)
        }

class AssertionHelpers:
    """Custom assertion helpers for complex validations"""

    @staticmethod
    def assert_protocol_valid(protocol: Dict[str, Any]):
        """Assert that a protocol is valid"""
        assert "id" in protocol, "Protocol missing id"
        assert "title" in protocol, "Protocol missing title"
        assert "description" in protocol, "Protocol missing description"
        assert "dimensions" in protocol, "Protocol missing dimensions"

        dimensions = protocol["dimensions"]
        required_dims = ["D1", "D2", "D3", "D4"]
        for dim in required_dims:
            assert dim in dimensions, f"Protocol missing dimension {dim}"
            assert isinstance(dimensions[dim], str), f"Dimension {dim} must be string"
            assert len(dimensions[dim]) >= 10, f"Dimension {dim} too short"

    @staticmethod
    def assert_content_valid(content: Dict[str, Any], min_length: int = 100):
        """Assert that content is valid"""
        assert "title" in content, "Content missing title"
        assert "body" in content, "Content missing body"
        assert "format" in content, "Content missing format"

        assert len(content["title"]) >= 5, "Title too short"
        assert len(content["body"]) >= min_length, f"Body too short (min {min_length})"
        assert content["format"] in ["markdown", "json", "html"], "Invalid format"

# Global test utilities
test_data_generator = TestDataGenerator()
performance_timer = PerformanceTimer()
assertion_helpers = AssertionHelpers()
