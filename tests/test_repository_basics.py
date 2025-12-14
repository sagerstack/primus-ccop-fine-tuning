"""
Basic tests for repository implementations.

Tests implemented functionality: error handling for missing files.
"""
import pytest
from unittest.mock import Mock

from infrastructure.adapters.repositories.jsonl_test_case_repository import JSONLTestCaseRepository
from domain.value_objects.benchmark_type import BenchmarkType


class TestJSONLTestCaseRepositoryBasics:
    """Tests for basic repository functionality that is implemented."""

    @pytest.mark.asyncio
    async def test_load_nonexistent_test_case(self, tmp_path):
        """CRITICAL: Handle loading nonexistent test case gracefully."""
        test_cases_dir = tmp_path / "test-cases"
        test_cases_dir.mkdir()

        repo = JSONLTestCaseRepository(test_cases_dir=test_cases_dir, logger=Mock())

        # Try to load nonexistent test
        test_case = await repo.load_by_id("B1-999")

        assert test_case is None

    @pytest.mark.asyncio
    async def test_handle_missing_file(self, tmp_path):
        """CRITICAL: Handle missing test case file gracefully."""
        test_cases_dir = tmp_path / "test-cases"
        test_cases_dir.mkdir()

        repo = JSONLTestCaseRepository(test_cases_dir=test_cases_dir, logger=Mock())

        # Try to load from non-existent file
        test_cases = await repo.load_by_benchmark(BenchmarkType("B1"))

        # Should return empty list, not crash
        assert test_cases == []
