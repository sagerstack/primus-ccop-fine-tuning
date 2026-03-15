"""
LLM-as-Judge evaluation service using Claude Agent SDK.

Tier 3 scoring methodology for subjective benchmarks (B12, B13, B20).
Uses Claude as an expert judge to evaluate complex compliance reasoning.
"""

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase


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

    Uses Claude Agent SDK to evaluate subjective compliance reasoning.
    Avoids model self-evaluation by using external Claude instance.
    """

    def __init__(self, model_name: str = "claude-sonnet-4") -> None:
        """
        Initialize LLM judge service.

        Args:
            model_name: Claude model to use for judging
        """
        self._model = model_name

    def evaluate_response(
        self,
        test_case: TestCase,
        response: ModelResponse,
        rubric: Dict[str, str]
    ) -> JudgeEvaluation:
        """
        Evaluate response using Claude as judge.

        Args:
            test_case: Test case being evaluated
            response: Model response to evaluate
            rubric: Evaluation rubric with criteria

        Returns:
            JudgeEvaluation with scores and justification
        """
        judge_prompt = self._build_judge_prompt(test_case, response, rubric)

        # Use Claude Agent SDK via subprocess
        try:
            judge_response = self._call_claude_agent(judge_prompt)
            evaluation = self._parse_judge_response(judge_response)
            evaluation.raw_response = judge_response
            return evaluation
        except Exception as e:
            # Fallback to conservative scoring on error
            return JudgeEvaluation(
                accuracy_score=3,
                completeness_score=3,
                alignment_score=3,
                justification=f"Judge evaluation error: {str(e)}",
                overall_score=0.6,
                confidence=0.0,
                raw_response=""
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
        # Use Claude Agent SDK to get evaluation
        # This avoids using the same model being evaluated
        result = subprocess.run(
            ["claude", "chat", "--model", self._model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude Agent SDK error: {result.stderr}")

        return result.stdout

    def _build_judge_prompt(
        self,
        test_case: TestCase,
        response: ModelResponse,
        rubric: Dict[str, str]
    ) -> str:
        """
        Build structured prompt for Claude judge.

        Args:
            test_case: Test case being evaluated
            response: Model response to evaluate
            rubric: Evaluation rubric

        Returns:
            Formatted prompt for Claude judge
        """
        return f"""You are an expert CCoP 2.0 compliance auditor evaluating a model's response.

**Test Question:**
{test_case.question}

**Model Response:**
{response.content}

**Expected Answer:**
{test_case.expected_response}

**Evaluation Rubric:**
{json.dumps(rubric, indent=2)}

**Instructions:**
Rate the response on a 1-5 scale for each criterion:
1. Accuracy: Technical correctness of compliance interpretation
2. Completeness: Coverage of all relevant control requirements
3. Alignment: Matches how a CSA auditor would evaluate this

Provide your evaluation in JSON format:
{{
  "accuracy_score": <1-5>,
  "completeness_score": <1-5>,
  "alignment_score": <1-5>,
  "justification": "<2-3 sentence explanation>",
  "confidence": <0.0-1.0>
}}

Only return the JSON, nothing else."""

    def _parse_judge_response(self, response: str) -> JudgeEvaluation:
        """
        Parse JSON response from Claude judge.

        Args:
            response: Raw response from Claude

        Returns:
            Parsed JudgeEvaluation

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

        # Normalize to 0-1 scale
        overall = (
            data["accuracy_score"] +
            data["completeness_score"] +
            data["alignment_score"]
        ) / 15.0

        return JudgeEvaluation(
            accuracy_score=data["accuracy_score"],
            completeness_score=data["completeness_score"],
            alignment_score=data["alignment_score"],
            justification=data["justification"],
            overall_score=overall,
            confidence=data.get("confidence", 0.5),
            raw_response=""
        )
