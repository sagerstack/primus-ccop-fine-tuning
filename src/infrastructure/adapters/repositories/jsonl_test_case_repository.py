"""
JSONL Test Case Repository

Loads test cases from JSONL files with auto-discovery.
Discovers all b*.jsonl files and builds mapping dynamically.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from application.ports.output.i_logger import ILogger
from application.ports.output.i_test_case_repository import ITestCaseRepository
from domain.entities.test_case import TestCase
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


class JSONLTestCaseRepository(ITestCaseRepository):
    """Repository for loading test cases from JSONL files with auto-discovery."""

    def __init__(self, test_cases_dir: Path, logger: ILogger) -> None:
        self._test_cases_dir = Path(test_cases_dir)
        self._logger = logger
        self._cache: Optional[List[TestCase]] = None
        self._benchmark_files: Optional[Dict[str, Path]] = None
        self._discover_benchmark_files()

    def _discover_benchmark_files(self) -> None:
        """
        Auto-discover benchmark files by scanning test_cases_dir for b*.jsonl files.
        Reads first line of each file to determine benchmark_type.
        """
        self._benchmark_files = {}

        if not self._test_cases_dir.exists():
            self._logger.warning(f"Test cases directory not found: {self._test_cases_dir}")
            return

        # Find all b*.jsonl files
        jsonl_files = sorted(self._test_cases_dir.glob("b*.jsonl"))

        for filepath in jsonl_files:
            try:
                # Read first line to extract benchmark_type
                with open(filepath, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if first_line:
                        data = json.loads(first_line)
                        benchmark_type = data.get("benchmark_type")
                        if benchmark_type:
                            # Store mapping: benchmark_type -> filepath
                            self._benchmark_files[benchmark_type] = filepath
                            self._logger.info(
                                f"Discovered benchmark file: {filepath.name} -> {benchmark_type}"
                            )
            except Exception as e:
                self._logger.warning(
                    f"Could not parse benchmark type from {filepath.name}: {e}"
                )

        self._logger.info(
            f"Discovered {len(self._benchmark_files)} benchmark files"
        )

    async def load_all(self) -> List[TestCase]:
        """Load all test cases."""
        if self._cache is not None:
            return self._cache

        all_cases = []
        # Load from all discovered files
        for benchmark_type_str in self._benchmark_files.keys():
            benchmark_type = BenchmarkType.from_string(benchmark_type_str)
            cases = await self.load_by_benchmark(benchmark_type)
            all_cases.extend(cases)

        self._cache = all_cases
        return all_cases

    async def load_by_benchmark(self, benchmark_type: BenchmarkType) -> List[TestCase]:
        """Load test cases for a specific benchmark."""
        # Find filepath for this benchmark type
        filepath = None
        for bt_str, fp in self._benchmark_files.items():
            if benchmark_type == bt_str or benchmark_type.short_name == BenchmarkType.from_string(bt_str).short_name:
                filepath = fp
                break

        if not filepath:
            self._logger.warning(f"No file found for benchmark: {benchmark_type}")
            return []

        if not filepath.exists():
            self._logger.warning(f"Test case file not found: {filepath}")
            return []

        test_cases = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                    data = json.loads(line)
                    test_case = self._parse_test_case(data)
                    test_cases.append(test_case)
                except Exception as e:
                    self._logger.error(
                        f"Error parsing test case at line {line_num}: {e}",
                        file=str(filepath)
                    )

        return test_cases

    async def load_by_id(self, test_id: str) -> Optional[TestCase]:
        """Load test case by ID."""
        all_cases = await self.load_all()
        for case in all_cases:
            if case.test_id == test_id:
                return case
        return None

    async def load_by_ids(self, test_ids: List[str]) -> List[TestCase]:
        """Load multiple test cases by IDs."""
        all_cases = await self.load_all()
        test_id_set = set(test_ids)
        return [case for case in all_cases if case.test_id in test_id_set]

    async def count(self) -> int:
        """Count total test cases."""
        all_cases = await self.load_all()
        return len(all_cases)

    async def exists(self, test_id: str) -> bool:
        """Check if test case exists."""
        case = await self.load_by_id(test_id)
        return case is not None

    def _parse_test_case(self, data: dict) -> TestCase:
        """Parse JSON data to TestCase entity."""
        return TestCase(
            test_id=data["test_id"],
            benchmark_type=BenchmarkType.from_string(data["benchmark_type"]),
            section=CCoPSection.from_string(data["section"]),
            clause_reference=data["clause_reference"],
            difficulty=DifficultyLevel.from_string(data["difficulty"]),
            question=data["question"],
            expected_response=data["expected_response"],
            evaluation_criteria=data.get("evaluation_criteria", {}),
            metadata=data.get("metadata", {}),
        )
