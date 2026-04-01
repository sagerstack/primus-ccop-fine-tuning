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
                        benchmark_type = data.get("benchmark_type") or data.get("benchmark_id")
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
        """Parse JSON data to TestCase entity. Handles both v1 flat and v2 nested formats."""
        if data.get("version") == "2.0":
            return self._parse_v2_test_case(data)
        return self._parse_v1_test_case(data)

    def _parse_v1_test_case(self, data: dict) -> TestCase:
        """Parse v1 flat format (backward compatibility)."""
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
            # Phase 2 fields (optional, backward compatible)
            key_facts=data.get("key_facts", []),
            expected_label=data.get("expected_label"),
            forbidden_claims=data.get("forbidden_claims", []),
        )

    def _parse_v2_test_case(self, data: dict) -> TestCase:
        """Parse v2 nested format."""
        inp = data.get("input", {})
        gt = data.get("ground_truth", {})
        fc = data.get("fail_conditions", {})
        meta = data.get("metadata", {})

        # Extract key_facts as list[str] for scorer backward compatibility
        raw_key_facts = gt.get("key_facts", [])
        key_facts_strings = [kf["fact"] for kf in raw_key_facts if isinstance(kf, dict)]

        # Merge v2-specific fields into metadata for downstream access
        enriched_metadata = {
            **meta,
            "scenario_sector": inp.get("scenario_sector"),
            "scenario_role": inp.get("scenario_role"),
            "test_category": meta.get("test_category"),
            "reasoning_chain": gt.get("reasoning_chain", []),
            "acceptable_variations": gt.get("acceptable_variations", []),
            "key_facts_structured": raw_key_facts,
            "hallucination_patterns": fc.get("hallucination_patterns", []),
        }

        # Build clause_reference as string (v1 format expects string, not list)
        clause_refs = meta.get("clause_reference", [])
        clause_ref_str = ", ".join(clause_refs) if isinstance(clause_refs, list) else clause_refs

        return TestCase(
            test_id=data["test_id"],
            benchmark_type=BenchmarkType.from_string(data["benchmark_id"]),
            section=CCoPSection.from_string(meta.get("section", "N/A")),
            clause_reference=clause_ref_str,
            difficulty=DifficultyLevel.from_string(meta.get("difficulty", "Medium")),
            question=inp["question"],
            expected_response=gt["expected_response"],
            evaluation_criteria={},  # v2 uses universal judge — no per-test criteria
            metadata=enriched_metadata,
            key_facts=key_facts_strings,
            expected_label=gt.get("expected_label"),
            forbidden_claims=fc.get("forbidden_claims", []),
        )
