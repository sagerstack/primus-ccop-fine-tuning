"""
Test Case Repository Port (Interface)

Abstract interface for test case persistence and retrieval.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.test_case import TestCase
from domain.value_objects.benchmark_type import BenchmarkType


class ITestCaseRepository(ABC):
    """
    Port (interface) for test case storage operations.

    This is an output port defining how the application accesses test cases.
    """

    @abstractmethod
    async def load_all(self) -> List[TestCase]:
        """
        Load all test cases from storage.

        Returns:
            List of all test cases

        Raises:
            RepositoryError: If loading fails
        """
        pass

    @abstractmethod
    async def load_by_benchmark(self, benchmark_type: BenchmarkType) -> List[TestCase]:
        """
        Load test cases for a specific benchmark.

        Args:
            benchmark_type: Benchmark to filter by

        Returns:
            List of test cases for the benchmark

        Raises:
            RepositoryError: If loading fails
        """
        pass

    @abstractmethod
    async def load_by_id(self, test_id: str) -> Optional[TestCase]:
        """
        Load a specific test case by ID.

        Args:
            test_id: Test case identifier

        Returns:
            Test case if found, None otherwise

        Raises:
            RepositoryError: If loading fails
        """
        pass

    @abstractmethod
    async def load_by_ids(self, test_ids: List[str]) -> List[TestCase]:
        """
        Load multiple test cases by IDs.

        Args:
            test_ids: List of test case identifiers

        Returns:
            List of found test cases

        Raises:
            RepositoryError: If loading fails
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Count total number of test cases.

        Returns:
            Total count

        Raises:
            RepositoryError: If operation fails
        """
        pass

    @abstractmethod
    async def exists(self, test_id: str) -> bool:
        """
        Check if a test case exists.

        Args:
            test_id: Test case identifier

        Returns:
            True if exists

        Raises:
            RepositoryError: If operation fails
        """
        pass
