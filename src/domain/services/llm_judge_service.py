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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.response_extractor import extract_final_answer

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

    # Universal judge fields (hallucination detection + reasoning depth)
    hallucination_detected: bool = False                          # Binary gate for hallucination
    unsupported_count: int = 0                                    # Count of UNSUPPORTED claims
    contradicted_count: int = 0                                   # Count of CONTRADICTED claims
    claims: List[Dict[str, str]] = field(default_factory=list)   # List of claim verification results
    reasoning_criteria_met: Dict[str, Optional[bool]] = field(default_factory=dict)  # Reasoning criteria evaluation

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
    def from_universal_judge(
        reasoning_criteria_met: Dict[str, Optional[bool]],
        hallucination_detected: bool,
        claims: List[Dict[str, str]],
        unsupported_count: int,
        contradicted_count: int,
        justification: str,
        confidence: float,
        raw_response: str,
    ) -> "JudgeEvaluation":
        """
        Create JudgeEvaluation from universal judge evaluation.

        Computes overall_score as:
        - If hallucination_detected: overall_score = 0.0
        - Else: overall_score = reasoning_depth_score / 3.0
        - Where reasoning_depth_score is sum of True values in reasoning_criteria_met
          (excluding None/N/A entries)

        Args:
            reasoning_criteria_met: Dict of criteria names to True/False/None
            hallucination_detected: Binary hallucination gate
            claims: List of claim verification results
            unsupported_count: Count of UNSUPPORTED claims
            contradicted_count: Count of CONTRADICTED claims
            justification: CoT explanation
            confidence: Judge self-assessed confidence (0-1)
            raw_response: Full judge response

        Returns:
            JudgeEvaluation with computed overall_score
        """
        # Calculate reasoning depth score (count of True values, excluding None)
        reasoning_depth_score = sum(
            1 for value in reasoning_criteria_met.values()
            if value is True
        )

        # Apply hallucination gate
        if hallucination_detected:
            overall_score = 0.0
        else:
            overall_score = reasoning_depth_score / 3.0

        # Create single dimension for reasoning depth
        dimensions = [
            DimensionScore(
                name="reasoning_depth",
                score=reasoning_depth_score,
                weight=1.0,
            )
        ]

        return JudgeEvaluation(
            dimensions=dimensions,
            justification=justification,
            overall_score=overall_score,
            confidence=confidence,
            raw_response=raw_response,
            judge_error=False,
            error_message="",
            hallucination_detected=hallucination_detected,
            unsupported_count=unsupported_count,
            contradicted_count=contradicted_count,
            claims=claims,
            reasoning_criteria_met=reasoning_criteria_met,
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

    UNIVERSAL_JUDGE_PROMPT = """You are evaluating a CCoP 2.0 compliance response on two dimensions: hallucination detection and reasoning depth.

**QUESTION:**
{question}

**RESPONSE (extracted final answer):**
{response}

**RETRIEVED CONTEXTS (from CCoP 2.0 documents):**
{contexts}

---

## EVALUATION INSTRUCTIONS

### PART 1: HALLUCINATION CHECK

1. Extract all atomic factual claims from the RESPONSE
2. For each claim, verify against RETRIEVED CONTEXTS:
   - SUPPORTED: Claim is directly supported by contexts or is a valid inference from them
   - UNSUPPORTED: Claim makes assertions not found in contexts
   - CONTRADICTED: Claim directly contradicts information in contexts

**IMPORTANT:** A claim citing a different clause than expected is SUPPORTED if that clause is factually correct per the contexts. Valid inference from provided contexts is NOT hallucination.

3. Verdict: hallucination_detected = true if ANY claim is UNSUPPORTED or CONTRADICTED

### PART 2: REASONING DEPTH (question-adaptive)

Evaluate which of these 3 criteria are **applicable** to this question type, then score each applicable criterion:

1. **clause_citations**: Does response reference specific CCoP 2.0 clause numbers?
   - Applicable for: Most questions (factual, advisory, classification)
   - Not applicable if: Question doesn't require regulatory citation
   - Met: true/false

2. **conditional_analysis**: Does response analyze if-then scenarios or conditional compliance?
   - Applicable for: Reasoning questions, scenario-based questions
   - Not applicable if: Pure factual lookup or simple classification
   - Met: true/false / null (if N/A)

3. **actionable_steps**: Does response provide concrete CIIO implementation steps?
   - Applicable for: Advisory questions, implementation guidance
   - Not applicable if: Pure classification, factual lookup, or theoretical analysis
   - Met: true/false / null (if N/A)

**Scoring:** For each applicable criterion, evaluate true (met) or false (not met). Use null for criteria that are not applicable to this question type.

reasoning_depth_score = count of criteria marked true (0-3)

---

## OUTPUT FORMAT

Return ONLY valid JSON (no markdown):

{{
  "claims": [
    {{
      "text": "Extracted claim text",
      "status": "SUPPORTED|UNSUPPORTED|CONTRADICTED",
      "evidence": "Quote from contexts or 'No evidence found'"
    }}
  ],
  "hallucination_detected": true/false,
  "unsupported_count": <count of UNSUPPORTED claims>,
  "contradicted_count": <count of CONTRADICTED claims>,
  "reasoning_depth_score": 0-3,
  "reasoning_criteria_met": {{
    "clause_citations": true/false/null,
    "conditional_analysis": true/false/null,
    "actionable_steps": true/false/null
  }},
  "justification": "Brief explanation of hallucination verdict and reasoning depth assessment",
  "confidence": 0.0-1.0
}}
"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        rubric_path: Optional[str] = None,
    ) -> None:
        """
        Initialize LLM judge service.

        Loads and caches rubric templates from evaluation-rubrics.md.

        Args:
            model_name: Claude model to use for judging. If None, reads from
                CCOP_LLM_JUDGE_MODEL setting (defaults to "sonnet").
            rubric_path: Path to evaluation-rubrics.md. Defaults to
                docs/phase-2/evaluation-rubrics.md relative to project root.
        """
        if model_name is None:
            from infrastructure.config.settings import get_settings
            settings = get_settings()
            model_name = settings.llm_judge_model
            self._timeout = settings.claude_cli_timeout
        else:
            self._timeout = 120
        self._model = model_name
        self._rubric_path = Path(rubric_path) if rubric_path else (
            _PROJECT_ROOT / "docs" / "phase-2" / "evaluation-rubrics.md"
        )
        self._rubrics: Dict[str, str] = self._load_rubrics()

        # Ground-truth verification infrastructure for D3 factual_grounding.
        # Loads clause inventory (deterministic existence check) and caches
        # actual clause text from Qdrant (for misattribution detection).
        self._inventory_ids: set[str] = self._load_inventory_ids()
        self._clause_text_cache: Dict[str, str] = self._load_clause_text_cache()

    def _load_inventory_ids(self) -> set[str]:
        """Load the set of valid CCoP 2.0 clause IDs from the inventory fixture."""
        inventory_path = _PROJECT_ROOT / "src" / "rag" / "ingestion" / "fixtures" / "clause_inventory.json"
        if not inventory_path.exists():
            logger.warning(
                "Clause inventory not found at %s. Citation verification disabled.",
                inventory_path,
            )
            return set()
        try:
            data = json.loads(inventory_path.read_text(encoding="utf-8"))
            ids = {
                e["clause_id"] for e in data.get("entries", [])
                if e.get("source_doc") == "CCoP 2.0" and "clause_id" in e
            }
            logger.info("Loaded %d CCoP 2.0 clause IDs for citation verification", len(ids))
            return ids
        except Exception as e:
            logger.warning("Failed to load clause inventory: %s", e)
            return set()

    def _load_clause_text_cache(self) -> Dict[str, str]:
        """
        Pre-load all CCoP 2.0 clause texts from Qdrant for misattribution detection.
        Non-fatal: if Qdrant is unreachable, judge falls back to inventory-only
        (existence check still works; misattribution detection is limited).
        """
        cache: Dict[str, str] = {}
        try:
            from infrastructure.config.settings import get_settings
            from qdrant_client import QdrantClient
        except ImportError:
            logger.warning("qdrant_client not installed. Clause text verification disabled.")
            return cache

        try:
            settings = get_settings()
            client = QdrantClient(url=settings.qdrant_url)
            next_offset = None
            while True:
                batch, next_offset = client.scroll(
                    collection_name=settings.qdrant_collection_name,
                    limit=500,
                    offset=next_offset,
                    with_payload=["text", "citation_id", "clause", "document_source"],
                )
                if not batch:
                    break
                for hit in batch:
                    payload = hit.payload or {}
                    if payload.get("document_source") != "CCoP 2.0":
                        continue
                    # Prefer the `clause` field (bare clause id like "5.3.1");
                    # fall back to stripping the "CCoP 2.0::" prefix from
                    # citation_id. Skip table/preamble sub-chunks whose
                    # citation_id contains extra "::" segments beyond the prefix.
                    clause_id = payload.get("clause") or ""
                    if not clause_id:
                        cid = payload.get("citation_id") or ""
                        if "::" in cid:
                            parts = cid.split("::")
                            # Only accept "DOC::CLAUSE" — skip "DOC::CLAUSE::table::N" etc.
                            if len(parts) == 2:
                                clause_id = parts[1]
                    if not clause_id:
                        continue
                    text = (payload.get("text") or "").strip()
                    if not text:
                        continue
                    # Keep the primary (longest) chunk if multiple exist
                    if clause_id not in cache or len(text) > len(cache[clause_id]):
                        cache[clause_id] = text[:500]
                if next_offset is None:
                    break
            logger.info(
                "Cached %d CCoP 2.0 clause texts from Qdrant for misattribution detection",
                len(cache),
            )
        except Exception as e:
            logger.warning(
                "Could not build clause text cache from Qdrant: %s. "
                "Misattribution detection will use existence check only.",
                e,
            )
        return cache

    # Two patterns combined to avoid false positives on version numbers
    # ("CCoP 2.0"):
    # 1. Citations with a lead-in word (clause/section/§) — 1-3 part numbers
    # 2. Bare 3-part citations (e.g., "5.3.1", "5.3.1(c)") — the 3-part form
    #    is unambiguous enough to not require a lead-in.
    # The negative lookbehind on the bare pattern prevents matching inside
    # version strings or larger numbers.
    _CITATION_LEADIN_PATTERN = re.compile(
        r"(?:clause|section|§)\s+(\d{1,2}(?:\.\d{1,2}){0,2}(?:\([a-z]\))?)",
        re.IGNORECASE,
    )
    _CITATION_BARE_PATTERN = re.compile(
        r"(?<![\d.\w])(\d{1,2}\.\d{1,2}\.\d{1,2}(?:\([a-z]\))?)(?![\d.])",
    )

    def _extract_citations(self, text: str) -> list[str]:
        """Extract unique clause-like citations from response text.

        Matches:
          - Lead-in citations: "Clause 5.2.1", "Section 3.4", "§5.3.1(c)"
          - Bare 3-part citations: "5.3.1", "5.3.1(c)"
        Does not match:
          - Bare 2-part numbers like "2.0" (version strings)
          - Numbers embedded inside larger identifiers
        """
        matches: set[str] = set()
        matches.update(self._CITATION_LEADIN_PATTERN.findall(text))
        matches.update(self._CITATION_BARE_PATTERN.findall(text))
        return sorted(matches)

    def _resolve_clause_text(self, clause_id: str) -> tuple[str, str]:
        """
        Return (text, lookup_source) for a clause ID. Falls back to the parent
        clause if a sub-letter citation (e.g., 5.3.1(c)) isn't chunked
        separately in Qdrant — the parent clause chunk contains all sub-letters.

        Returns:
            (text, source) where source is "exact", "parent", or "missing".
        """
        text = self._clause_text_cache.get(clause_id, "")
        if text:
            return text, "exact"
        # Sub-letter fallback: 5.3.1(c) -> 5.3.1
        parent_match = re.match(r"^(\d{1,2}(?:\.\d{1,2}){1,2})\([a-z]\)$", clause_id)
        if parent_match:
            parent_id = parent_match.group(1)
            parent_text = self._clause_text_cache.get(parent_id, "")
            if parent_text:
                return parent_text, "parent"
        return "", "missing"

    def _build_citation_verification_block(self, response_text: str) -> str:
        """
        Extract citations from the response, verify each against the clause
        inventory, and format as a pre-verified ground-truth block for the judge.
        """
        cited = self._extract_citations(response_text)
        if not cited:
            return "  (no clause citations detected in response)"

        lines = []
        for cid in cited:
            if cid in self._inventory_ids:
                text, source = self._resolve_clause_text(cid)
                if source == "exact":
                    snippet = text.replace("\n", " ").strip()[:280]
                    lines.append(f'  - "{cid}": EXISTS in CCoP 2.0. Actual clause text: "{snippet}..."')
                elif source == "parent":
                    snippet = text.replace("\n", " ").strip()[:280]
                    lines.append(f'  - "{cid}": EXISTS in CCoP 2.0. Parent clause text (sub-letter not chunked separately): "{snippet}..."')
                else:
                    lines.append(f'  - "{cid}": EXISTS in CCoP 2.0 (clause text not cached — limited verification)')
            else:
                lines.append(f'  - "{cid}": FABRICATED — not found in CCoP 2.0 clause inventory')
        return "\n".join(lines)

    def _build_expected_citations_block(self, clause_reference: str) -> str:
        """
        For each clause in the test case's clause_reference list, fetch its
        actual text from the Qdrant cache and format as a ground-truth block.
        Gives the judge access to what the expected answer's cited clauses
        actually say, not just their IDs.
        """
        if not clause_reference:
            return "  (no expected citations specified in ground truth)"

        expected_ids = [cid.strip() for cid in clause_reference.split(",") if cid.strip()]
        if not expected_ids:
            return "  (no expected citations specified in ground truth)"

        lines = []
        for cid in expected_ids:
            text, source = self._resolve_clause_text(cid)
            if source == "exact":
                snippet = text.replace("\n", " ").strip()[:280]
                lines.append(f'  - "{cid}": "{snippet}..."')
            elif source == "parent":
                snippet = text.replace("\n", " ").strip()[:280]
                lines.append(f'  - "{cid}": (parent clause text, sub-letter not chunked separately) "{snippet}..."')
            elif cid in self._inventory_ids:
                lines.append(f'  - "{cid}": (exists in CCoP 2.0 inventory, text not cached)')
            else:
                lines.append(f'  - "{cid}": (not found in CCoP 2.0 corpus — possible ground-truth issue)')
        return "\n".join(lines)

    def _build_key_facts_block(self, test_case: TestCase) -> str:
        """
        Format key_facts as a tier-grouped block preserving the structured
        tier (critical/important) and source info from ground truth.
        Falls back to a flat list if structured key_facts aren't available.
        """
        structured = test_case.metadata.get("key_facts_structured", [])

        if not structured:
            if test_case.key_facts:
                return "\n".join(f"  - {f}" for f in test_case.key_facts)
            return "  (none specified)"

        critical = [f for f in structured if isinstance(f, dict) and f.get("tier") == "critical"]
        important = [f for f in structured if isinstance(f, dict) and f.get("tier") != "critical"]

        lines = []
        if critical:
            lines.append("  CRITICAL (must be present in response):")
            for f in critical:
                src = f.get("source", "?")
                lines.append(f'    - {f.get("fact", "")}  [source: {src}]')
        if important:
            lines.append("  IMPORTANT (should be present):")
            for f in important:
                src = f.get("source", "?")
                lines.append(f'    - {f.get("fact", "")}  [source: {src}]')

        return "\n".join(lines) if lines else "  (none specified)"

    def _load_rubrics(self) -> Dict[str, str]:
        """
        Load the benchmark-agnostic universal rubric from evaluation-rubrics.md.

        Parses the markdown file for the single `## UNIVERSAL RUBRIC` section
        and maps every known benchmark ID to that same rubric. Benchmark-specific
        signal comes from each test case's ground truth (key_facts,
        clause_reference, expected_response), not from the rubric itself.

        Returns:
            Dictionary mapping benchmark short names (B1..B24) to the universal
            rubric prompt template. Empty dict if file not found or universal
            section missing.
        """
        if not self._rubric_path.exists():
            logger.warning(
                "Rubric file not found at %s. All evaluations will return errors.",
                self._rubric_path,
            )
            return {}

        content = self._rubric_path.read_text(encoding="utf-8")

        universal_match = re.search(
            r"^## UNIVERSAL RUBRIC\b.*?(?=^## |\Z)",
            content,
            flags=re.MULTILINE | re.DOTALL,
        )
        if not universal_match:
            logger.warning(
                "No '## UNIVERSAL RUBRIC' section found in %s", self._rubric_path
            )
            return {}

        universal_section = universal_match.group(0)

        template_split = universal_section.split("### Judge Prompt Template")
        if len(template_split) < 2:
            logger.warning(
                "No '### Judge Prompt Template' heading in UNIVERSAL RUBRIC"
            )
            return {}

        code_blocks = re.findall(
            r"```\n(.*?)```", template_split[1], re.DOTALL
        )
        if not code_blocks:
            logger.warning(
                "No code block found in UNIVERSAL RUBRIC judge prompt template"
            )
            return {}

        universal_rubric = code_blocks[0].strip()

        known_benchmarks = [f"B{i}" for i in range(1, 25)]
        rubrics = {bid: universal_rubric for bid in known_benchmarks}

        logger.info(
            "Loaded universal rubric; applied to %d benchmark IDs",
            len(rubrics),
        )
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

    def universal_evaluate_response(
        self,
        test_case: TestCase,
        response: ModelResponse,
        benchmark_id: str,
        retrieved_contexts: Optional[List[str]] = None,
    ) -> JudgeEvaluation:
        """
        Evaluate response using universal two-dimension judge (hallucination + reasoning depth).

        Uses combined prompt to evaluate:
        1. Hallucination detection (binary gate with claim-level verification)
        2. Reasoning depth (question-adaptive criteria: citations, conditional analysis, actionable steps)

        Args:
            test_case: Test case being evaluated
            response: Model response to evaluate
            benchmark_id: Benchmark short name (for logging)
            retrieved_contexts: List of retrieved context strings from RAG

        Returns:
            JudgeEvaluation with hallucination fields and reasoning_depth dimension.
            On failure, returns JudgeEvaluation with judge_error=True (skip-and-flag).
        """
        try:
            # Extract final answer from chain-of-thought output
            final_answer = extract_final_answer(response.content)

            # Prepare contexts text
            contexts_text = (
                "\n\n".join(retrieved_contexts)
                if retrieved_contexts
                else "No retrieved contexts available"
            )

            # Build universal judge prompt
            judge_prompt = self.UNIVERSAL_JUDGE_PROMPT.format(
                question=test_case.question,
                response=final_answer,
                contexts=contexts_text,
            )

            # Call Claude judge
            judge_response = self._call_claude_agent(judge_prompt)

            # Parse universal judge response
            evaluation = self._parse_universal_judge_response(judge_response)
            return evaluation

        except Exception as e:
            logger.error("Universal judge evaluation failed for %s: %s", benchmark_id, e)
            return JudgeEvaluation.error(
                error_message=f"Universal judge evaluation failed for {benchmark_id}: {str(e)}",
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
            timeout=self._timeout,
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

        # Tiered key_facts preserving structured tier (critical/important)
        # and source metadata from ground truth.
        key_facts_block = self._build_key_facts_block(test_case)

        # Pre-verify citations in the response against the CCoP 2.0 clause
        # inventory and fetch actual clause text from Qdrant. Injected into
        # the prompt so the judge scores D3 from verified ground truth rather
        # than its own parametric knowledge.
        citation_verifications = self._build_citation_verification_block(response.content)

        # Expected citations from ground truth clause_reference, with actual
        # clause text so the judge can compare response claims against what
        # the expected-to-cite clauses actually say.
        expected_citations_block = self._build_expected_citations_block(
            test_case.clause_reference or ""
        )

        forbidden = (
            "\n".join(f"  - {c}" for c in test_case.forbidden_claims)
            if test_case.forbidden_claims
            else "  (none specified)"
        )
        hallucination_patterns_list = test_case.metadata.get("hallucination_patterns", [])
        hallucination_patterns_str = (
            "\n".join(f"  - {p}" for p in hallucination_patterns_list)
            if hallucination_patterns_list
            else "  (none specified)"
        )

        prompt = template.replace("{question}", test_case.question)
        prompt = prompt.replace("{response}", response.content)
        prompt = prompt.replace("{expected_response}", test_case.expected_response)
        prompt = prompt.replace("{key_facts}", key_facts_block)
        prompt = prompt.replace("{clause_reference}", test_case.clause_reference)
        prompt = prompt.replace("{expected_citations_text}", expected_citations_block)
        prompt = prompt.replace("{citation_verifications}", citation_verifications)
        prompt = prompt.replace("{forbidden_claims}", forbidden)
        prompt = prompt.replace("{hallucination_patterns}", hallucination_patterns_str)

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

    def _parse_universal_judge_response(self, response: str) -> JudgeEvaluation:
        """
        Parse JSON response from universal judge into JudgeEvaluation.

        Expects format:
        {
            "claims": [{"text": "...", "status": "...", "evidence": "..."}],
            "hallucination_detected": true/false,
            "unsupported_count": N,
            "contradicted_count": M,
            "reasoning_depth_score": 0-3,
            "reasoning_criteria_met": {
                "clause_citations": true/false/null,
                "conditional_analysis": true/false/null,
                "actionable_steps": true/false/null
            },
            "justification": "...",
            "confidence": 0.0-1.0
        }

        Args:
            response: Raw response from Claude

        Returns:
            Parsed JudgeEvaluation with hallucination and reasoning depth fields

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If required fields are missing
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            # Extract fields
            claims = data.get("claims", [])
            hallucination_detected = bool(data.get("hallucination_detected", False))
            unsupported_count = int(data.get("unsupported_count", 0))
            contradicted_count = int(data.get("contradicted_count", 0))
            reasoning_criteria_met = data.get("reasoning_criteria_met", {})
            justification = data.get("justification", "")
            confidence = float(data.get("confidence", 0.5))

            return JudgeEvaluation.from_universal_judge(
                reasoning_criteria_met=reasoning_criteria_met,
                hallucination_detected=hallucination_detected,
                claims=claims,
                unsupported_count=unsupported_count,
                contradicted_count=contradicted_count,
                justification=justification,
                confidence=confidence,
                raw_response=response,
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Failed to parse universal judge response: %s", e)
            return JudgeEvaluation.error(
                error_message=f"Failed to parse universal judge response: {str(e)}",
                raw_response=response,
            )
