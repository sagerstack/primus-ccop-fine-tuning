"""
LLM-as-Judge evaluation service using OpenRouter.

Loads benchmark-specific rubric prompts from evaluation-rubrics.md.
Uses 0-3 anchored scale with Chain-of-Thought instruction.
Skip-and-flag error handling (no fallback scores).

Judge calls route through OpenRouter (OpenAI-compatible API) supporting:
  - Primary judge (runs on every eval): Qwen3-235B-A22B by default
  - Secondary judge (runs only on measurement snapshots): GPT-4o-mini by default

Path B 2-judge methodology — see:
  research/llm-judge-cybersec/followup-openrouter-judge/30-recommendation.md
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

import structlog

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.response_extractor import extract_final_answer

if TYPE_CHECKING:
    # Lazy-imported at runtime inside __init__ to avoid the
    # domain -> infrastructure -> application -> domain cycle through
    # infrastructure/__init__.py. See note in __init__.
    from infrastructure.external.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)
# Structured logger — events written via this go through the same JSON
# pipeline as the rest of the eval CLI, so retry warnings appear in the
# log file alongside test-case progress events.
struct_logger = structlog.get_logger(__name__)

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
    LLM-as-Judge evaluation via OpenRouter (Qwen3-235B by default).

    Loads benchmark-specific rubric prompts from evaluation-rubrics.md at
    initialization. Calls an external judge model through the OpenRouter
    chat-completions API (default: ``qwen/qwen3-235b-a22b-07-25``,
    configurable via ``CCOP_JUDGE_PRIMARY_MODEL``). Using an external,
    different-family model avoids self-evaluation bias on responses
    generated by the local Llama-Primus-Reasoning model under test.

    Two evaluation modes are supported:
      - ``evaluate_response`` — benchmark-specific rubric (5 dimensions × 0-3),
        requires labeled ground truth (expected_response, clause_reference,
        key_facts, forbidden_claims).
      - ``universal_evaluate_response`` — GT-free 2-dimension judge
        (hallucination detection + reasoning depth), needs only the question,
        response, and retrieved contexts. Suitable for ad-hoc queries.
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
        *,
        openrouter_client: "Optional[OpenRouterClient]" = None,
        secondary_model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        """
        Initialize LLM judge service.

        Loads and caches rubric templates from evaluation-rubrics.md.

        Args:
            model_name: Primary judge model ID (OpenRouter slug, e.g.,
                "qwen/qwen3-235b-a22b-07-25"). If None, reads from
                CCOP_JUDGE_PRIMARY_MODEL setting.
            rubric_path: Path to evaluation-rubrics.md. Defaults to
                docs/phase-2/evaluation-rubrics.md relative to project root.
            openrouter_client: Optional OpenRouterClient instance. If None,
                constructs one from settings. Allows DI for testing.
            secondary_model: Secondary judge model ID for dual-judge runs
                (measurement snapshots). If None, reads from
                CCOP_JUDGE_SECONDARY_MODEL setting.
            temperature: Judge sampling temperature. If None, reads from
                CCOP_JUDGE_TEMPERATURE setting (default 0.2).
        """
        # Lazy imports to avoid circular-import cycle at module load:
        # domain -> infrastructure -> application -> domain via infrastructure/__init__.py.
        from infrastructure.config.settings import get_settings
        from infrastructure.external.openrouter_client import OpenRouterClient as _OpenRouterClient
        settings = get_settings()
        self._settings = settings  # Store for judge_seed access

        self._model = model_name or settings.judge_primary_model
        self._secondary_model = secondary_model or settings.judge_secondary_model
        self._temperature = (
            temperature if temperature is not None else settings.judge_temperature
        )
        # Retries for malformed-JSON responses from the judge (separate from
        # OpenRouter's API-level retries). Used by evaluate_response and
        # universal_evaluate_raw to re-call the judge when the response can't
        # be parsed as JSON. Default 3 attempts (initial + 2 retries).
        self._json_retry_attempts = getattr(
            settings, "judge_json_retry_attempts", 3,
        )

        if openrouter_client is not None:
            self._judge_client = openrouter_client
        else:
            if not settings.openrouter_api_key:
                raise ValueError(
                    "OpenRouter API key missing. Set CCOP_OPENROUTER_API_KEY in "
                    "src/config/.env.local. Get a key at https://openrouter.ai."
                )
            self._judge_client = _OpenRouterClient(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                timeout=settings.judge_timeout,
                max_retries=settings.judge_max_retries,
            )

        self._rubric_path = Path(rubric_path) if rubric_path else (
            _PROJECT_ROOT / "docs" / "phase-2" / "evaluation-rubrics.md"
        )
        self._rubrics: Dict[str, str] = self._load_rubrics()

        # Ground-truth verification infrastructure for D3 factual_grounding.
        # Loads clause inventory (deterministic existence check) from the
        # offline ground-truth test suite.
        # Doc-keyed inventory built first — _inventory_ids derives its flat
        # union from it.
        self._inventory_by_doc: Dict[str, set[str]] = self._load_inventory_by_doc()
        self._inventory_ids: set[str] = self._load_inventory_ids()

    def _load_inventory_ids(self) -> set[str]:
        """Load the set of valid clause IDs across the full source corpus.

        Returns the *flat* union across all 7 docs — kept for backward
        compatibility with `_build_expected_citations_block` which doesn't
        need doc routing. The richer doc-keyed inventory used for citation
        verification is in `_inventory_by_doc` (loaded separately).
        """
        return set().union(*self._inventory_by_doc.values()) if hasattr(self, "_inventory_by_doc") else set()

    def _load_inventory_by_doc(self) -> Dict[str, set[str]]:
        """Load a doc-keyed inventory: canonical_doc_name → set of clause_ids.

        This is the structure the judge needs for proper hallucination
        detection: each cited (document, clause) pair is verified against
        the *specific* document's inventory, so a clause format that's
        valid for one doc but not another doesn't get spuriously credited
        or blamed.
        """
        from collections import defaultdict
        by_doc: Dict[str, set[str]] = defaultdict(set)
        inventory_path = _PROJECT_ROOT / "src" / "rag" / "ingestion" / "fixtures" / "clause_inventory.json"
        if not inventory_path.exists():
            logger.warning(
                "Clause inventory not found at %s. Citation verification disabled.",
                inventory_path,
            )
            return {}
        try:
            data = json.loads(inventory_path.read_text(encoding="utf-8"))
            for e in data.get("entries", []):
                cid = e.get("clause_id")
                src = e.get("source_doc")
                if cid and src:
                    by_doc[src].add(cid)
            total = sum(len(s) for s in by_doc.values())
            logger.info(
                "Loaded %d clause IDs across %d source docs for citation verification",
                total, len(by_doc),
            )
            return dict(by_doc)
        except Exception as e:
            logger.warning("Failed to load clause inventory: %s", e)
            return {}

    # Map model-written document names (lowercased) to canonical inventory keys.
    # The model writes natural variants ("the Act", "CCoP", "Audit Guidelines"),
    # we route to canonical names matching the inventory's source_doc field.
    _DOC_ALIASES: Dict[str, list[str]] = {
        "CCoP 2.0": [
            "ccop 2.0", "ccop2.0", "ccop", "ccop v2", "ccop second edition",
            "cybersecurity code of practice", "cybersecurity code of practice 2.0",
            "cybersecurity code of practice (second edition)",
        ],
        "CCoP Response to Feedback": [
            "ccop response to feedback", "response to feedback",
            "ccop 2.0 response to feedback", "csa response to feedback",
        ],
        "Cybersecurity Act 2018": [
            "cybersecurity act 2018", "cybersecurity act", "csa act",
            "the act", "act 2018", "singapore cybersecurity act",
        ],
        "Auditing Guidelines": [
            "auditing guidelines", "audit guidelines",
            "guidelines for auditing critical information infrastructure",
            "guidelines for auditing cii", "audit guideline",
        ],
        "Threat Modelling Guide": [
            "threat modelling guide", "threat modeling guide",
            "guide to cyber threat modelling", "guide to cyber threat modeling",
            "cyber threat modelling guide",
        ],
        "Risk Assessment Guide": [
            "risk assessment guide",
            "guide to conducting cybersecurity risk assessment for cii",
            "cybersecurity risk assessment guide",
        ],
        "Security By Design": [
            "security by design", "security by design framework",
            "sbd framework", "sbd",
        ],
    }

    def _normalize_doc_name(self, claimed: str) -> Optional[str]:
        """Map the model's claimed document name to a canonical inventory key.

        Returns None when no canonical match exists — those citations get
        EXTERNAL classification (cross-document references outside our 7-doc
        corpus, like NIST CSF / ISO 27001).
        """
        if not claimed:
            return None
        norm = claimed.strip().lower()
        # Exact match against alias table
        for canonical, aliases in self._DOC_ALIASES.items():
            if norm in aliases:
                return canonical
            if norm == canonical.lower():
                return canonical
        return None


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
        """Extract unique clause-like citations from inline prose.

        Returns clause-ID strings only (no document attribution). For the
        document-aware extraction used by the new citation verification
        path, see `_extract_attributed_citations`.
        """
        matches: set[str] = set()
        matches.update(self._CITATION_LEADIN_PATTERN.findall(text))
        matches.update(self._CITATION_BARE_PATTERN.findall(text))
        return sorted(matches)

    def _extract_attributed_citations(
        self, text: str
    ) -> list[Tuple[Optional[str], str, str]]:
        """Extract citations with document attribution from a response.

        Sources:
          1. The three structured footer blocks (Sources / Cross-references /
             Other Sources) — each entry has explicit `<doc>: <clause>`
             attribution.
          2. Inline prose mentions ("Section 5.3.1", "Clause 11(7) of the
             Act") that aren't already represented in the footer blocks.

        Returns:
            List of `(claimed_document, clause, source_location)` tuples,
            deduplicated. `claimed_document` is None for inline mentions
            without explicit attribution; downstream classification routes
            those to the default corpus document (CCoP 2.0). The model's
            block placement is informative but not authoritative — the
            verification logic routes by claimed_document, not by which
            block the model used.
        """
        # Lazy import to avoid pulling resolver into domain layer at module
        # load time.
        from rag.citations.resolver import parse_citations

        seen: set[Tuple[str, str]] = set()
        result: list[Tuple[Optional[str], str, str]] = []

        # 1. Block-attributed citations (full document name + clause)
        for c in parse_citations(text):
            doc = c["document"]
            clause = c["clause"]
            key = (doc.lower(), clause.lower())
            if key in seen:
                continue
            seen.add(key)
            result.append((doc, clause, f"block:{c['kind']}"))

        # 2. Inline citations not already accounted for
        for m in self._CITATION_LEADIN_PATTERN.finditer(text):
            clause = m.group(1)
            # If any block citation has this same clause, skip — the block
            # version is more specific (carries attribution).
            if any(c.lower() == clause.lower() for _, c in seen):
                continue
            key = ("", clause.lower())
            if key in seen:
                continue
            seen.add(key)
            result.append((None, clause, "inline"))

        for m in self._CITATION_BARE_PATTERN.finditer(text):
            clause = m.group(1)
            if any(c.lower() == clause.lower() for _, c in seen):
                continue
            key = ("", clause.lower())
            if key in seen:
                continue
            seen.add(key)
            result.append((None, clause, "inline"))

        return result

    def _extract_clause_id(self, s: str) -> Optional[str]:
        """
        Extract bare clause ID from a citation string and normalize it.
        
        Examples:
            "CCoP 2.0: 5.3.1" -> "5.3.1"
            "CCoP 2.0 5.9.2(b)" -> "5.9.2(b)"
            "Response to Feedback 11.28" -> "11.28"
            "Section 5.3.1(b)" -> "5.3.1(b)"
            "AnnexC" -> "AnnexC"
        
        Returns:
            Normalized clause ID or None if no clause token found.
        """
        if not s:
            return None
        
        # Strip document name prefix if present (handles both ":"-separated and space-separated)
        # First try colon-separated ("CCoP 2.0: 5.3.1")
        if ":" in s:
            s = s.split(":", 1)[1].strip()
        else:
            # For space-separated ("CCoP 2.0 5.9.2(b)"), remove known document prefixes
            s = re.sub(r"^(?:CCoP 2\.0|RESPONSE-TO-FEEDBACK|Response to Feedback|CCoP Response to Feedback|Cybersecurity Act 2018|Section|Clause|\u00a7|Part|Chapter)\s+", "", s, flags=re.IGNORECASE).strip()
        
        # Try to extract clause pattern: digits with optional dots and sub-letters
        # Also handle Annex patterns and table references
        patterns = [
            r"^(\d{1,2}(?:\.\d{1,2})*(?:\([a-z]\))?)",  # Standard clause at start like 5.3.1 or 5.9.2(b)
            r"(Annex[A-Z])",  # Annex patterns
        ]
        
        for pattern in patterns:
            match = re.search(pattern, s)
            if match:
                clause_token = match.group(1)
                # Normalize using ClauseHitScoringService
                try:
                    from domain.services.clause_hit_scoring_service import ClauseHitScoringService
                    return ClauseHitScoringService.normalize_clause_id(clause_token)
                except Exception:
                    # Fallback: just return the extracted token
                    return clause_token
        
        return None

    def _compute_citation_correctness(
        self,
        response_content: str,
        test_case: TestCase,
    ) -> int:
        """
        Compute D6 (citation_correctness) programmatically.
        
        Returns precision score (0-3) of model's in-corpus citations against
        ground-truth clause set.
        
        Args:
            response_content: Model's response text (contains Sources block)
            test_case: Test case with clause_reference and key_facts
        
        Returns:
            0-3 score based on precision:
                3 if precision = 1.0 (perfect)
                2 if precision >= 0.67
                1 if precision >= 0.34 or no corpus citations
                0 if precision < 0.34
        """
        # Build C (model's in-corpus citations from Sources)
        attributed = self._extract_attributed_citations(response_content)
        corpus_citations = set()
        
        for doc_name, clause_str, _ in attributed:
            clause_id = self._extract_clause_id(clause_str)
            if not clause_id:
                continue
            
            # Classify as corpus or external using inventory
            # If doc_name is provided, check that specific doc; otherwise check any-doc
            if doc_name:
                canonical = self._normalize_doc_name(doc_name)
                if canonical and canonical in self._inventory_by_doc:
                    doc_inventory = self._inventory_by_doc[canonical]
                    if clause_id in doc_inventory:
                        corpus_citations.add(clause_id)
                # Else: external doc or not in corpus -> exclude
            else:
                # No doc name -> classify by clause ID membership in any inventory
                if clause_id in self._inventory_ids:
                    corpus_citations.add(clause_id)
                # Else: not in any inventory -> external, exclude
        
        # Build G (ground-truth clause set from clause_reference + key_facts sources)
        gt_clauses = set()
        
        # From clause_reference
        clause_ref = test_case.clause_reference or ""
        if clause_ref:
            # Handle both comma-separated string and list
            if isinstance(clause_ref, str):
                clause_ids = [c.strip() for c in clause_ref.split(",") if c.strip()]
            else:
                clause_ids = clause_ref
            
            for cid in clause_ids:
                normalized = self._extract_clause_id(cid)
                if normalized:
                    gt_clauses.add(normalized)
        
        # From key_facts sources
        # Try structured key_facts first
        structured_kf = test_case.metadata.get("key_facts_structured", [])
        if structured_kf:
            for kf in structured_kf:
                if isinstance(kf, dict) and "source" in kf:
                    source = kf["source"]
                    clause_id = self._extract_clause_id(source)
                    if clause_id:
                        gt_clauses.add(clause_id)
        
        # If no corpus citations, return D6=1 (neutral)
        if not corpus_citations:
            return 1
        
        # Compute precision
        intersection = corpus_citations & gt_clauses
        precision = len(intersection) / len(corpus_citations)
        
        # Map precision to 0-3 scale
        if precision == 1.0:
            return 3
        elif precision >= 0.67:
            return 2
        elif precision >= 0.34:
            return 1
        else:
            return 0

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

            # Retry loop on JSON parse failures: the OpenRouter client retries
            # on API-level errors (timeouts, rate limits) but cannot detect a
            # successful API response that returned malformed JSON. That happens
            # occasionally on Qwen models when the CoT block consumes too many
            # tokens and truncates mid-JSON, or when the model emits trailing
            # text outside the JSON object. We re-call the judge up to N times
            # to get a fresh response.
            last_err: Optional[Exception] = None
            for attempt in range(1, self._json_retry_attempts + 1):
                struct_logger.info(
                    "judge_call_started",
                    benchmark_id=benchmark_id,
                    attempt=attempt,
                    max_attempts=self._json_retry_attempts,
                    judge_mode="rubric",
                )
                judge_response = self._call_judge(judge_prompt, seed=self._settings.judge_seed)
                try:
                    # Parse D1-D5 from LLM
                    dimensions, justification, confidence, raw_response = self._parse_judge_response(judge_response)
                    
                    # Compute D6 programmatically
                    d6_score = self._compute_citation_correctness(response.content, test_case)
                    dimensions.append(DimensionScore(
                        name="citation_correctness",
                        score=d6_score,
                        weight=0.5,
                    ))
                    
                    # Build final JudgeEvaluation with all 6 dimensions
                    return JudgeEvaluation.from_dimensions(
                        dimensions=dimensions,
                        justification=justification,
                        confidence=confidence,
                        raw_response=raw_response,
                    )
                except (json.JSONDecodeError, KeyError, ValueError) as parse_err:
                    last_err = parse_err
                    struct_logger.warning(
                        "judge_response_parse_failed",
                        benchmark_id=benchmark_id,
                        attempt=attempt,
                        max_attempts=self._json_retry_attempts,
                        error_type=type(parse_err).__name__,
                        error_message=str(parse_err)[:200],
                        will_retry=attempt < self._json_retry_attempts,
                    )
                    if attempt < self._json_retry_attempts:
                        continue
                    raise
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
        return self.universal_evaluate_raw(
            question=test_case.question,
            response_content=response.content,
            retrieved_contexts=retrieved_contexts,
            label=benchmark_id,
        )

    def universal_evaluate_raw(
        self,
        *,
        question: str,
        response_content: str,
        retrieved_contexts: Optional[List[str]] = None,
        label: str = "ad-hoc",
    ) -> JudgeEvaluation:
        """
        Universal judge for inputs that aren't wrapped in TestCase/ModelResponse entities.

        Same prompt + parser as ``universal_evaluate_response``; suitable for
        ad-hoc queries (``query ask``) where there's no labeled test case to
        construct. Use ``label`` for log lines (e.g., the run_id) — it has no
        effect on scoring.

        Args:
            question: User question.
            response_content: Raw model output (chain-of-thought OK; the
                final-answer extractor strips it).
            retrieved_contexts: List of retrieved context strings from RAG.
                None or empty list signals "no contexts" to the judge.
            label: Identifier used in log lines on failure.

        Returns:
            JudgeEvaluation with hallucination fields and reasoning_depth dimension.
            On failure, returns JudgeEvaluation with judge_error=True.
        """
        try:
            final_answer = extract_final_answer(response_content)
            contexts_text = (
                "\n\n".join(retrieved_contexts)
                if retrieved_contexts
                else "No retrieved contexts available"
            )
            judge_prompt = self.UNIVERSAL_JUDGE_PROMPT.format(
                question=question,
                response=final_answer,
                contexts=contexts_text,
            )

            # Retry on JSON parse failures (see evaluate_response for rationale).
            for attempt in range(1, self._json_retry_attempts + 1):
                struct_logger.info(
                    "judge_call_started",
                    label=label,
                    attempt=attempt,
                    max_attempts=self._json_retry_attempts,
                    judge_mode="universal",
                )
                judge_response = self._call_judge(judge_prompt, seed=self._settings.judge_seed)
                try:
                    return self._parse_universal_judge_response(judge_response)
                except (json.JSONDecodeError, KeyError, ValueError) as parse_err:
                    struct_logger.warning(
                        "universal_judge_response_parse_failed",
                        label=label,
                        attempt=attempt,
                        max_attempts=self._json_retry_attempts,
                        error_type=type(parse_err).__name__,
                        error_message=str(parse_err)[:200],
                        will_retry=attempt < self._json_retry_attempts,
                    )
                    if attempt < self._json_retry_attempts:
                        continue
                    raise

        except Exception as e:
            logger.error("Universal judge evaluation failed for %s: %s", label, e)
            return JudgeEvaluation.error(
                error_message=f"Universal judge evaluation failed for {label}: {str(e)}",
                raw_response="",
            )

    def _call_judge(
        self,
        prompt: str,
        *,
        role: str = "primary",
        seed: Optional[int] = None,
    ) -> str:
        """
        Call a judge model via OpenRouter.

        Args:
            prompt: Evaluation prompt (full rubric + ground-truth injection).
            role: "primary" (default) or "secondary" — selects which model ID.
            seed: Optional seed for byte-level reproducibility on supporting models.

        Returns:
            Judge's text response.

        Raises:
            JudgeAPIError: If the call fails after all retries.
            ValueError: If role is not "primary" or "secondary".
        """
        if role == "primary":
            model_id = self._model
        elif role == "secondary":
            model_id = self._secondary_model
        else:
            raise ValueError(f"Unknown judge role: {role!r}. Use 'primary' or 'secondary'.")

        return self._judge_client.call(
            prompt,
            model=model_id,
            temperature=self._temperature,
            seed=seed,
        )

    def _call_both_judges(
        self,
        prompt: str,
        *,
        seed: Optional[int] = None,
    ) -> Tuple[str, str]:
        """
        Call both primary and secondary judges with the same prompt.

        Used for measurement snapshots where inter-judge agreement is computed.
        Not called from normal evaluation paths — those call only the primary.

        Args:
            prompt: Evaluation prompt.
            seed: Optional seed forwarded to both models.

        Returns:
            Tuple (primary_response, secondary_response).

        Raises:
            JudgeAPIError: If either call fails after retries.
        """
        primary = self._call_judge(prompt, role="primary", seed=seed)
        secondary = self._call_judge(prompt, role="secondary", seed=seed)
        return primary, secondary

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
        prompt = prompt.replace("{forbidden_claims}", forbidden)
        prompt = prompt.replace("{hallucination_patterns}", hallucination_patterns_str)

        # B19 has an optional {related_scenarios} placeholder
        related_scenarios = test_case.metadata.get("related_scenarios", "N/A")
        if isinstance(related_scenarios, list):
            related_scenarios = "\n".join(related_scenarios)
        prompt = prompt.replace("{related_scenarios}", related_scenarios)

        return prompt

    def _parse_judge_response(self, response: str) -> Tuple[List[DimensionScore], str, float, str]:
        """
        Parse JSON response from LLM judge into components.

        Expects the standardized format (D1-D5 only, D6 computed separately):
        {
            "dimensions": [{"dimension": "...", "score": 0-3, "weight": 0.5}],
            "justification": "...",
            "confidence": 0.0-1.0
        }

        Args:
            response: Raw response from LLM judge

        Returns:
            Tuple of (dimensions D1-D5, justification, confidence, raw_response)

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

        return (
            dimensions,
            data["justification"],
            float(data.get("confidence", 0.5)),
            response,
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
