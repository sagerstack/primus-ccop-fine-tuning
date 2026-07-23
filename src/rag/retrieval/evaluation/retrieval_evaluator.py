"""Runtime RetrievalEvaluator component for graphont-agentic mode.

Scores retrieved clauses on answer-support (0=IRRELEVANT, 1=RELATED, 2=ESSENTIAL)
to enable relevance-based filtering separate from textual similarity (CE scores).

Promoted from offline validation script with EXACT behavior preservation:
- Same prompt (0/1/2 rubric, "judge by MEANING not word overlap")
- Same caching (SHA256 key includes PROMPT_VERSION)
- Fail-open (returns score=None on errors, never raises)
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from infrastructure.config.settings import Settings, get_settings
from infrastructure.external.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)

# Version the prompt so cache invalidation is automatic when prompt changes
PROMPT_VERSION = "v1"

# Exact prompt from the offline validation script
PROMPT_TEMPLATE = """You are a retrieval evaluator for a Singapore Cybersecurity Code of Practice (CCoP) compliance QA system. You are given a QUESTION and ONE retrieved CLAUSE. Judge how much the clause helps ANSWER the question, using this scale:
  2 (ESSENTIAL): the clause states a rule, obligation, definition, or fact directly needed to answer the question.
  1 (RELATED): the clause is contextually relevant but does not itself provide what is needed to answer.
  0 (IRRELEVANT): the clause does not help answer the question.
Judge answer-support by MEANING, not word overlap. A terse obligation can be ESSENTIAL even if it shares few words with the question; an on-topic clause can be merely RELATED. Consider ONLY the question and this single clause.
Return ONLY a JSON object: {{"score": 0|1|2, "reason": "<one sentence>"}}

QUESTION: {question}

CLAUSE [{citation_id}]: {clause_text}"""


class RetrievalEvaluator:
    """Runtime per-clause answer-support scorer for graphont-agentic filtering.
    
    Evaluates clauses on a 0/1/2 scale (IRRELEVANT / RELATED / ESSENTIAL) via LLM.
    Caches results keyed by (model, temp, PROMPT_VERSION, question, text).
    Fail-open: returns score=None on API/parse errors (never raises).
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the evaluator.
        
        Args:
            settings: Optional Settings instance. If None, loads via get_settings().
        """
        self._settings = settings or get_settings()
        self._model = self._settings.retrieval_evaluator_model
        self._temp = self._settings.retrieval_evaluator_temperature
        
        # OpenRouter client
        self._client = OpenRouterClient(
            api_key=self._settings.openrouter_api_key,
            base_url=self._settings.openrouter_base_url,
        )
        
        # Cache setup (ON by default)
        self._cache_dir = Path(self._settings.results_dir) / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self._cache_dir / "retrieval_evaluator_cache.json"
        self._cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Dict]:
        """Load the evaluation cache from disk."""
        if self._cache_file.exists():
            try:
                return json.loads(self._cache_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load retrieval evaluator cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save the evaluation cache to disk."""
        try:
            self._cache_file.write_text(json.dumps(self._cache, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save retrieval evaluator cache: {e}")
    
    def _compute_cache_key(self, question: str, text: str) -> str:
        """Compute SHA256 cache key for a (model, temp, version, question, text) tuple."""
        key_str = f"{self._model}|{self._temp}|{PROMPT_VERSION}|{question}|{text}"
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _parse_llm_response(self, raw: str) -> Dict:
        """Parse LLM response as JSON, stripping markdown fences if present.
        
        Returns:
            dict with {score: int|None, reason: str}
        """
        text = raw.strip()
        
        # Strip markdown fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        
        try:
            parsed = json.loads(text)
            return {
                "score": parsed.get("score"),
                "reason": parsed.get("reason", ""),
            }
        except json.JSONDecodeError:
            # Truncate raw text for error message
            truncated = raw[:100] + ("..." if len(raw) > 100 else "")
            return {
                "score": None,
                "reason": f"PARSE_ERROR: {truncated}",
            }
    
    def evaluate_clause(self, question: str, citation_id: str, text: str) -> Dict:
        """Evaluate one clause's answer-support for the given question.
        
        Args:
            question: The user's question
            citation_id: Clause citation (for context in prompt)
            text: Full clause text
        
        Returns:
            dict with {score: int|None, reason: str}
            - score: 0 (IRRELEVANT) / 1 (RELATED) / 2 (ESSENTIAL) or None on error
            - reason: One-sentence explanation or error message
            
        Fail-open: Returns score=None on API/parse errors (never raises).
        """
        # Check cache
        cache_key = self._compute_cache_key(question, text)
        if cache_key in self._cache:
            return {
                "score": self._cache[cache_key].get("score"),
                "reason": self._cache[cache_key].get("reason", ""),
            }
        
        # Build prompt
        prompt = PROMPT_TEMPLATE.format(
            question=question,
            citation_id=citation_id,
            clause_text=text,
        )
        
        # Call LLM
        try:
            raw_response = self._client.call(
                prompt=prompt,
                model=self._model,
                temperature=self._temp,
                seed=0,
            )
            
            # Parse response
            result = self._parse_llm_response(raw_response)
            
            # Cache successful result
            self._cache[cache_key] = result
            self._save_cache()
            
            return result
            
        except Exception as e:
            # Fail-open: log warning and return score=None
            logger.warning(f"Retrieval evaluator error for {citation_id}: {type(e).__name__}: {e}")
            return {
                "score": None,
                "reason": f"EVAL_ERROR: {type(e).__name__}",
            }
    
    def evaluate_pool(self, question: str, candidates: List[Dict]) -> List[Dict]:
        """Evaluate a pool of candidates.
        
        Args:
            question: The user's question
            candidates: List of dicts with keys {citation_id, text, ...}
        
        Returns:
            List of dicts with {citation_id, score, reason}
        """
        results = []
        for candidate in candidates:
            citation_id = candidate.get("citation_id", "")
            text = candidate.get("text", "")
            
            eval_result = self.evaluate_clause(question, citation_id, text)
            
            results.append({
                "citation_id": citation_id,
                "score": eval_result["score"],
                "reason": eval_result["reason"],
            })
        
        return results


__all__ = ["RetrievalEvaluator", "PROMPT_VERSION"]
