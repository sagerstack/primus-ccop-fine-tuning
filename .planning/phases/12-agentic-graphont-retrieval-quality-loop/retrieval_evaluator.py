#!/usr/bin/env python3
"""Retrieval Evaluator (Phase 12, Step 2 of relevance-filter work)

Per-clause answer-support scoring (0/1/2 scale) via LLM to identify which
clauses actually help answer the question, separate from textual similarity.

Scores:
  2 (ESSENTIAL): clause states a rule/obligation/definition directly needed
  1 (RELATED): contextually relevant but doesn't provide what's needed
  0 (IRRELEVANT): doesn't help answer the question

Output: 12-retrieval-evaluator-scores.json (per-clause eval_score + eval_reason)
Cache: retrieval_evaluator_cache.json (keyed by hash of model+temp+question+text)
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path (same as capture_per_clause.py)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.config.settings import get_settings
from infrastructure.external.openrouter_client import OpenRouterClient

# Paths
OUTPUT_DIR = Path(__file__).parent
PER_CLAUSE_DATA = OUTPUT_DIR / "12-per-clause-ce-data.json"
CACHE_FILE = OUTPUT_DIR / "retrieval_evaluator_cache.json"
OUTPUT_FILE = OUTPUT_DIR / "12-retrieval-evaluator-scores.json"

# Prompt template
PROMPT_TEMPLATE = """You are a retrieval evaluator for a Singapore Cybersecurity Code of Practice (CCoP) compliance QA system. You are given a QUESTION and ONE retrieved CLAUSE. Judge how much the clause helps ANSWER the question, using this scale:
  2 (ESSENTIAL): the clause states a rule, obligation, definition, or fact directly needed to answer the question.
  1 (RELATED): the clause is contextually relevant but does not itself provide what is needed to answer.
  0 (IRRELEVANT): the clause does not help answer the question.
Judge answer-support by MEANING, not word overlap. A terse obligation can be ESSENTIAL even if it shares few words with the question; an on-topic clause can be merely RELATED. Consider ONLY the question and this single clause.
Return ONLY a JSON object: {{"score": 0|1|2, "reason": "<one sentence>"}}

QUESTION: {question}

CLAUSE [{citation_id}]: {clause_text}"""


def load_cache() -> Dict[str, Dict]:
    """Load the evaluation cache (keyed by hash)."""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except:
            return {}
    return {}


def save_cache(cache: Dict[str, Dict]):
    """Save the evaluation cache."""
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def compute_cache_key(model: str, temperature: float, question: str, clause_text: str) -> str:
    """Compute SHA256 cache key for a (model, temp, question, clause_text) tuple."""
    key_str = f"{model}|{temperature}|{question}|{clause_text}"
    return hashlib.sha256(key_str.encode()).hexdigest()


def parse_llm_response(raw: str) -> Dict:
    """Parse LLM response as JSON, stripping markdown fences if present."""
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
    except json.JSONDecodeError as e:
        # Truncate raw text for error message
        truncated = raw[:200] + ("..." if len(raw) > 200 else "")
        return {
            "score": None,
            "reason": f"PARSE_ERROR: {truncated}",
        }


def evaluate_clause(
    client: OpenRouterClient,
    model: str,
    temperature: float,
    question: str,
    citation_id: str,
    clause_text: str,
    cache: Dict[str, Dict],
) -> Dict:
    """Evaluate one clause. Returns {score, reason}. Uses cache if available."""
    
    # Check cache
    cache_key = compute_cache_key(model, temperature, question, clause_text)
    if cache_key in cache:
        return cache[cache_key]
    
    # Build prompt
    prompt = PROMPT_TEMPLATE.format(
        question=question,
        citation_id=citation_id,
        clause_text=clause_text,
    )
    
    # Call LLM
    try:
        raw_response = client.call(
            prompt=prompt,
            model=model,
            temperature=temperature,
            seed=0,
        )
        
        # Parse response
        result = parse_llm_response(raw_response)
        result["raw"] = raw_response
        
        # Cache result
        cache[cache_key] = result
        save_cache(cache)
        
        return result
        
    except Exception as e:
        error_result = {
            "score": None,
            "reason": f"API_ERROR: {type(e).__name__}: {str(e)}",
            "raw": None,
        }
        return error_result


def main():
    """Main evaluator script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-ids", type=str, help="Comma-separated test IDs (default: all)")
    args = parser.parse_args()
    
    # Load settings
    settings = get_settings()
    model = settings.retrieval_evaluator_model
    temperature = settings.retrieval_evaluator_temperature
    
    print(f"Retrieval Evaluator")
    print(f"  Model: {model}")
    print(f"  Temperature: {temperature}")
    print()
    
    # Initialize OpenRouter client
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    
    # Load per-clause data
    per_clause_data = json.loads(PER_CLAUSE_DATA.read_text())
    
    # Filter by test IDs if specified
    if args.test_ids:
        test_ids = set(tid.strip() for tid in args.test_ids.split(","))
        per_clause_data = [c for c in per_clause_data if c["test_id"] in test_ids]
    
    print(f"Processing {len(per_clause_data)} cases...")
    print()
    
    # Load cache
    cache = load_cache()
    print(f"Cache loaded: {len(cache)} entries")
    print()
    
    # Load existing output if resuming
    results = []
    if OUTPUT_FILE.exists():
        try:
            results = json.loads(OUTPUT_FILE.read_text())
            completed_ids = {r["test_id"] for r in results}
            per_clause_data = [c for c in per_clause_data if c["test_id"] not in completed_ids]
            print(f"Resuming: {len(completed_ids)} already completed, {len(per_clause_data)} remaining")
            print()
        except:
            results = []
    
    # Process each case
    for i, case_data in enumerate(per_clause_data, 1):
        test_id = case_data["test_id"]
        question = case_data["question"]
        gold_set = case_data["gold_set"]
        
        print(f"[{i}/{len(per_clause_data)}] {test_id}:")
        
        evaluated_clauses = []
        for j, clause in enumerate(case_data["clauses"], 1):
            citation_id = clause["citation_id"]
            clause_text = clause["text"]
            
            print(f"  [{j}/8] {citation_id}...", end=" ", flush=True)
            
            eval_result = evaluate_clause(
                client, model, temperature, question, citation_id, clause_text, cache
            )
            
            evaluated_clauses.append({
                "citation_id": citation_id,
                "ce_score": clause["ce_score"],
                "is_gold": clause["is_gold"],
                "eval_score": eval_result["score"],
                "eval_reason": eval_result["reason"],
            })
            
            score_str = str(eval_result["score"]) if eval_result["score"] is not None else "ERR"
            gold_marker = "★" if clause["is_gold"] else " "
            print(f"{gold_marker} score={score_str}")
        
        # Save case result
        case_result = {
            "test_id": test_id,
            "question": question,
            "gold_set": gold_set,
            "clauses": evaluated_clauses,
        }
        results.append(case_result)
        
        # Write incrementally
        OUTPUT_FILE.write_text(json.dumps(results, indent=2))
        
        print()
    
    print(f"Complete! Wrote {len(results)} cases to {OUTPUT_FILE}")
    print(f"Cache: {len(cache)} entries")


if __name__ == "__main__":
    main()
