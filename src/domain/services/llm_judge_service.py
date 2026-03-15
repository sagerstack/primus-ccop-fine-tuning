"""
LLM-as-Judge evaluation service using Claude Agent SDK.

Loads benchmark-specific rubric prompts from evaluation-rubrics.md.
Uses 0-3 anchored scale with Chain-of-Thought instruction.
Skip-and-flag error handling (no fallback scores).
"""

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass
class DimensionScore:
    """Single dimension score from LLM judge."""

    name: str           # e.g., "gap_prioritization"
    score: int          # 0-3 anchored scale
    weight: float       # From criteria-establishment.md


@dataclass
class JudgeEvaluation:
    """LLM judge evaluation result with dynamic dimensions."""

    dimensions: List[DimensionScore]  # Benchmark-specific dimension scores
    justification: str                # CoT explanation with evidence
    overall_score: float              # 0-1 normalized (weighted avg of dimensions)
    confidence: float                 # 0-1 judge self-assessed confidence
    raw_response: str                 # Full judge response for debugging
    judge_error: bool = False         # True if evaluation failed (skip-and-flag)
    error_message: str = ""           # Error details when judge_error=True

    @staticmethod
    def from_dimensions(
        dimensions: List[DimensionScore],
        justification: str,
        confidence: float,
        raw_response: str
    ) -> "JudgeEvaluation":
        """
        Create JudgeEvaluation from dimension scores.

        Calculates overall_score as weighted average normalized to 0-1:
        sum(d.score * d.weight for d in dimensions) / (3.0 * sum(d.weight for d in dimensions))

        Args:
            dimensions: List of dimension scores (0-3 scale)
            justification: CoT explanation
            confidence: Judge self-assessed confidence (0-1)
            raw_response: Full judge response

        Returns:
            JudgeEvaluation with calculated overall_score
        """
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0:
            overall = 0.0
        else:
            weighted_sum = sum(d.score * d.weight for d in dimensions)
            overall = weighted_sum / (3.0 * total_weight)

        return JudgeEvaluation(
            dimensions=dimensions,
            justification=justification,
            overall_score=overall,
            confidence=confidence,
            raw_response=raw_response,
            judge_error=False,
            error_message=""
        )

    @staticmethod
    def error(error_message: str, raw_response: str = "") -> "JudgeEvaluation":
        """
        Create skip-and-flag JudgeEvaluation for evaluation failures.

        Args:
            error_message: Error details
            raw_response: Raw response if available

        Returns:
            JudgeEvaluation with judge_error=True and zero scores
        """
        return JudgeEvaluation(
            dimensions=[],
            justification="",
            overall_score=0.0,
            confidence=0.0,
            raw_response=raw_response,
            judge_error=True,
            error_message=error_message
        )


class LLMJudgeService:
    """
    LLM-as-Judge evaluation using Claude.

    Loads benchmark-specific rubric prompts from evaluation-rubrics.md at
    initialization. Uses Claude Agent SDK to evaluate compliance reasoning.
    Avoids model self-evaluation by using external Claude instance.
    """

    def __init__(
        self,
        model_name: str = "claude-sonnet-4",
        rubric_path: Optional[str] = None,
    ) -> None:
        """
        Initialize LLM judge service.

        Loads and caches rubric templates from evaluation-rubrics.md.

        Args:
            model_name: Claude model to use for judging
            rubric_path: Path to evaluation-rubrics.md. Defaults to
                docs/phase-2/evaluation-rubrics.md relative to project root.
        """
        self._model = model_name
        self._rubric_path = Path(rubric_path) if rubric_path else (
            _PROJECT_ROOT / "docs" / "phase-2" / "evaluation-rubrics.md"
        )
        self._rubrics: Dict[str, str] = self._load_rubrics()

    def _load_rubrics(self) -> Dict[str, str]:
        """
        Load and parse rubric templates from evaluation-rubrics.md.

        Parses the markdown file into a dictionary mapping benchmark ID
        (e.g., "B8") to complete judge prompt template string.

        Returns:
            Dictionary mapping benchmark short name to rubric prompt template.
            Empty dict if file not found.
        """
        if not self._rubric_path.exists():
            logger.warning(
                "Rubric file not found at %s. All evaluations will return errors.",
                self._rubric_path,
            )
            return {}

        content = self._rubric_path.read_text(encoding="utf-8")
        rubrics: Dict[str, str] = {}

        # Split on benchmark headers: ## B3: ..., ## B7: ..., etc.
        # Each section contains a ```...``` code block with the prompt template
        sections = re.split(r"(?=^## B\d+:)", content, flags=re.MULTILINE)

        for section in sections:
            header_match = re.match(r"^## (B\d+):", section)
            if not header_match:
                continue

            benchmark_id = header_match.group(1)

            # Extract the Judge Prompt Template code block
            # Look for the ### Judge Prompt Template heading, then the ``` block
            template_section = section.split("### Judge Prompt Template")
            if len(template_section) < 2:
                logger.warning(
                    "No Judge Prompt Template found for %s", benchmark_id
                )
                continue

            # Extract content between first ``` pair after the heading
            code_blocks = re.findall(
                r"```\n(.*?)```", template_section[1], re.DOTALL
            )
            if not code_blocks:
                logger.warning(
                    "No code block found in Judge Prompt Template for %s",
                    benchmark_id,
                )
                continue

            rubrics[benchmark_id] = code_blocks[0].strip()

        logger.info("Loaded %d rubric templates: %s", len(rubrics), sorted(rubrics.keys()))
        return rubrics

    def evaluate_response(
        self,
        test_case: TestCase,
        response: ModelResponse,
        benchmark_id: str,
    ) -> JudgeEvaluation:
        """
        Evaluate response using Claude as judge with benchmark-specific rubric.

        Args:
            test_case: Test case being evaluated
            response: Model response to evaluate
            benchmark_id: Benchmark short name (e.g., "B8")

        Returns:
            JudgeEvaluation with dimension scores and justification.
            On failure, returns JudgeEvaluation with judge_error=True (skip-and-flag).
        """
        try:
            judge_prompt = self._build_judge_prompt(test_case, response, benchmark_id)
            if isinstance(judge_prompt, JudgeEvaluation):
                return judge_prompt  # Error from missing rubric
            judge_response = self._call_claude_agent(judge_prompt)
            evaluation = self._parse_judge_response(judge_response)
            return evaluation
        except Exception as e:
            logger.error("Judge evaluation failed for %s: %s", benchmark_id, e)
            return JudgeEvaluation.error(
                error_message=f"Judge evaluation failed for {benchmark_id}: {str(e)}",
                raw_response="",
            )

    def _call_claude_agent(self, prompt: str) -> str:
        """
        Call Claude Agent SDK via subprocess.

        Args:
            prompt: Evaluation prompt

        Returns:
            Claude's response

        Raises:
            subprocess.CalledProcessError: If Claude call fails
            subprocess.TimeoutExpired: If call times out
        """
        result = subprocess.run(
            ["claude", "chat", "--model", self._model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude Agent SDK error: {result.stderr}")

        return result.stdout

    def _build_judge_prompt(
        self,
        test_case: TestCase,
        response: ModelResponse,
        benchmark_id: str,
    ) -> Union[str, JudgeEvaluation]:
        """
        Build benchmark-specific judge prompt from rubric template.

        Looks up the rubric template for benchmark_id and substitutes
        test case placeholders.

        Args:
            test_case: Test case being evaluated
            response: Model response to evaluate
            benchmark_id: Benchmark short name (e.g., "B8")

        Returns:
            Formatted prompt string, or JudgeEvaluation.error() if rubric not found.
        """
        if benchmark_id not in self._rubrics:
            logger.error("No rubric found for benchmark %s", benchmark_id)
            return JudgeEvaluation.error(
                error_message=f"No rubric found for benchmark {benchmark_id}"
            )

        template = self._rubrics[benchmark_id]

        key_facts_str = ", ".join(test_case.key_facts) if test_case.key_facts else "N/A"

        prompt = template.replace("{question}", test_case.question)
        prompt = prompt.replace("{response}", response.content)
        prompt = prompt.replace("{expected_response}", test_case.expected_response)
        prompt = prompt.replace("{key_facts}", key_facts_str)
        prompt = prompt.replace("{clause_reference}", test_case.clause_reference)

        # B19 has an optional {related_scenarios} placeholder
        related_scenarios = test_case.metadata.get("related_scenarios", "N/A")
        if isinstance(related_scenarios, list):
            related_scenarios = "\n".join(related_scenarios)
        prompt = prompt.replace("{related_scenarios}", related_scenarios)

        return prompt

    def _parse_judge_response(self, response: str) -> JudgeEvaluation:
        """
        Parse JSON response from Claude judge into JudgeEvaluation.

        Expects the standardized format:
        {
            "dimensions": [{"dimension": "...", "score": 0-3, "weight": 1.0}],
            "justification": "...",
            "confidence": 0.0-1.0
        }

        Args:
            response: Raw response from Claude

        Returns:
            Parsed JudgeEvaluation with dynamic DimensionScore list

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If required fields are missing
        """
        # Extract JSON from response (handle markdown code blocks)
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)

        dimensions: List[DimensionScore] = []
        for d in data["dimensions"]:
            score = int(d["score"])
            if score < 0 or score > 3:
                logger.warning(
                    "Score %d out of 0-3 range for dimension '%s', clamping",
                    score,
                    d["dimension"],
                )
                score = max(0, min(3, score))

            dimensions.append(
                DimensionScore(
                    name=d["dimension"],
                    score=score,
                    weight=float(d["weight"]),
                )
            )

        return JudgeEvaluation.from_dimensions(
            dimensions=dimensions,
            justification=data["justification"],
            confidence=float(data.get("confidence", 0.5)),
            raw_response=response,
        )
