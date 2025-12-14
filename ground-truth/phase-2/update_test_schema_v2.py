#!/usr/bin/env python3
"""
Improved test case schema updater with better key fact extraction.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

BENCHMARK_CATEGORIES = {
    "B1": "classification", "B2": "classification", "B3": "reasoning", "B4": "classification",
    "B5": "classification", "B6": "reasoning", "B7": "reasoning", "B8": "reasoning",
    "B9": "reasoning", "B10": "reasoning", "B11": "reasoning", "B12": "reasoning",
    "B13": "reasoning", "B14": "reasoning", "B15": "reasoning", "B16": "reasoning",
    "B17": "reasoning", "B18": "reasoning", "B19": "reasoning", "B20": "safety", "B21": "safety"
}

def extract_key_facts_improved(expected_response: str, test_case: Dict) -> List[str]:
    """Improved key fact extraction using multiple strategies."""
    facts = []

    # Strategy 1: Extract numbered/bullet points
    lines = expected_response.replace('**', '').split('\n')
    for line in lines:
        line = line.strip()
        # Match: (1), 1., •, -, *, etc.
        if re.match(r'^\s*[\(（]?\d+[\)）]', line) or \
           re.match(r'^\s*\d+[\.\)]\s+', line) or \
           line.startswith('- ') or line.startswith('• ') or line.startswith('* '):
            fact = re.sub(r'^\s*[\(（]?\d+[\)）]\.?\s*', '', line)
            fact = re.sub(r'^\s*\d+[\.\)]\s+', '', fact)
            fact = re.sub(r'^\s*[\-•\*]\s+', '', fact)
            fact = fact.strip()
            if 15 < len(fact) < 300 and not fact.endswith(':'):
                facts.append(fact)

    # Strategy 2: Extract from criteria sections (a), (b), etc.
    criteria_pattern = r'\([a-z]\)([^(]+?)(?=\([a-z]\)|$)'
    matches = re.findall(criteria_pattern, expected_response, re.DOTALL)
    for match in matches:
        fact = match.strip()
        fact = ' '.join(fact.split())  # Normalize whitespace
        if 20 < len(fact) < 300:
            facts.append(fact)

    # Strategy 3: Extract key sentences with regulatory keywords
    if len(facts) < 3:
        keywords = ['must', 'requires', 'should', 'mandates', 'specifies', 'Clause', 'Section']
        sentences = re.split(r'[.!](?=\s+[A-Z\(\d])', expected_response)
        for sent in sentences:
            sent = sent.strip()
            if any(kw in sent for kw in keywords) and 30 < len(sent) < 250:
                sent = sent.replace('**', '')
                facts.append(sent)

    # Remove duplicates while preserving order
    seen = set()
    unique_facts = []
    for fact in facts:
        fact_normalized = fact.lower().strip()
        if fact_normalized not in seen and len(fact_normalized) > 20:
            seen.add(fact_normalized)
            unique_facts.append(fact)

    # Limit to 8 most relevant facts
    return unique_facts[:8]


def get_expected_label_improved(test_case: Dict, benchmark_id: str) -> str:
    """Improved expected label extraction."""

    # Check existing fields first
    if "correct_classification" in test_case:
        return test_case["correct_classification"]
    if "correct_answer" in test_case:
        return test_case["correct_answer"]

    response = test_case.get("expected_response", "")

    # B2: Compliance classification
    if benchmark_id == "B2":
        if response.startswith("**Compliant**"):
            return "Compliant"
        elif response.startswith("**Non-Compliant**") or response.startswith("**Non-compliant**"):
            return "Non-Compliant"

    # B21: Hallucination - extract the "does not exist" statement
    if benchmark_id == "B21":
        # Find the key negative statement
        if "does not contain" in response or "does not specify" in response or "does not exist" in response:
            sentences = response.split('.')
            for sent in sentences[:3]:
                if "does not" in sent:
                    return sent.strip().replace('**', '')

    # B1, B4, B5: Extract concise label from response
    # Look for "Two criteria", "IT system", "OT system", etc.
    first_part = response[:200].replace('**', '')

    # For B1 - extract criteria summary
    if benchmark_id == "B1":
        if "two criteria" in first_part.lower():
            return "Two criteria: essential service delivery + Singapore location"
        return first_part.split('.')[0]

    # For B4 - IT/OT classification
    if benchmark_id == "B4":
        if response.startswith("**IT"):
            return "IT system"
        elif response.startswith("**OT"):
            return "OT system"
        elif "hybrid" in first_part.lower():
            return "Hybrid IT/OT system"

    # Default: first meaningful sentence
    return first_part.split('.')[0].strip()[:150]


def get_safety_checks(test_case: Dict, benchmark_id: str) -> List[str]:
    """Get safety checks for safety benchmarks."""

    # B21 already has hallucination_indicators
    if "hallucination_indicators" in test_case:
        return test_case["hallucination_indicators"]

    # B20: Over-specification
    if benchmark_id == "B20":
        return [
            "no_vendor_mandates",
            "no_technical_over_specification",
            "distinguish_requirement_from_guidance",
            "acknowledge_flexibility"
        ]

    return []


def get_reasoning_dimensions_improved(test_case: Dict, benchmark_id: str) -> Dict[str, str]:
    """Improved reasoning dimensions extraction."""
    criteria = test_case.get("evaluation_criteria", {})
    dimensions = {}

    # Common mapping
    mapping = {
        "accuracy": "factual_accuracy",
        "completeness": "comprehensiveness",
        "reasoning": "logical_coherence",
        "context": "regulatory_grounding",
        "clarity": "communication_clarity",
        "nuance": "contextual_nuance",
        "practicality": "practical_applicability",
        "precision": "technical_precision",
        "insight": "analytical_depth",
        "remediation": "remediation_quality",
        "examples": "illustrative_examples"
    }

    for old_key, new_key in mapping.items():
        if old_key in criteria:
            dimensions[new_key] = criteria[old_key]

    # Add benchmark-specific dimensions
    if benchmark_id in ["B9", "B10", "B11"]:  # Risk reasoning
        if "causal_reasoning" not in dimensions and "reasoning" in criteria:
            dimensions["causal_reasoning"] = criteria["reasoning"]

    if benchmark_id in ["B14", "B15"]:  # Remediation
        if "feasibility_assessment" not in dimensions:
            dimensions["feasibility_assessment"] = "Must assess implementation feasibility"

    return dimensions


def update_test_case_improved(test_case: Dict, benchmark_id: str) -> Dict:
    """Improved test case update."""

    category = BENCHMARK_CATEGORIES.get(benchmark_id, "reasoning")

    # 1. Add benchmark_category
    test_case["benchmark_category"] = category

    # 2. Add improved key_facts
    key_facts = extract_key_facts_improved(test_case.get("expected_response", ""), test_case)
    test_case["key_facts"] = key_facts if key_facts else ["Unable to extract key facts automatically"]

    # 3. Category-specific updates
    if category in ["classification", "safety"]:
        label = get_expected_label_improved(test_case, benchmark_id)
        test_case["expected_label"] = label

        # Remove old fields
        if "correct_classification" in test_case:
            del test_case["correct_classification"]
        if "correct_answer" in test_case:
            del test_case["correct_answer"]

    if category == "safety":
        safety_checks = get_safety_checks(test_case, benchmark_id)
        if safety_checks:
            test_case["safety_checks"] = safety_checks

        # Remove old field
        if "hallucination_indicators" in test_case:
            del test_case["hallucination_indicators"]

    if category == "reasoning":
        dimensions = get_reasoning_dimensions_improved(test_case, benchmark_id)
        if dimensions:
            test_case["reasoning_dimensions"] = dimensions

    return test_case


def process_file(input_path: Path, output_path: Path):
    """Process a single JSONL file."""

    filename = input_path.stem
    # Extract benchmark ID more carefully
    if filename.startswith('b0'):
        benchmark_id = 'B' + filename[2:filename.find('_')]
    else:
        benchmark_id = 'B' + filename[1:filename.find('_')]

    print(f"\n{'='*60}")
    print(f"Processing: {filename}")
    print(f"Benchmark ID: {benchmark_id}")
    print(f"Category: {BENCHMARK_CATEGORIES.get(benchmark_id, 'unknown')}")
    print(f"{'='*60}")

    updated_cases = []

    with open(input_path, 'r') as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                test_case = json.loads(line)
                test_id = test_case.get('test_id', f'case-{i}')

                updated_case = update_test_case_improved(test_case, benchmark_id)

                # Print summary
                num_facts = len(updated_case.get('key_facts', []))
                print(f"  ✓ {test_id}: {num_facts} key facts extracted")

                updated_cases.append(updated_case)

            except Exception as e:
                print(f"  ✗ ERROR on line {i}: {e}")

    # Write output
    with open(output_path, 'w') as f:
        for case in updated_cases:
            f.write(json.dumps(case, ensure_ascii=False) + '\n')

    print(f"\n  ✅ Successfully updated {len(updated_cases)} test cases")
    return len(updated_cases)


def main():
    test_suite_dir = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/ground-truth/phase-2/test-suite")
    updated_dir = test_suite_dir / "updated_v2"
    updated_dir.mkdir(exist_ok=True)

    print("\n" + "="*60)
    print("IMPROVED Test Case Schema Updater")
    print("="*60)

    total = 0
    for jsonl_file in sorted(test_suite_dir.glob("b*.jsonl")):
        output_file = updated_dir / jsonl_file.name
        count = process_file(jsonl_file, output_file)
        total += count

    print("\n" + "="*60)
    print(f"✅ ALL UPDATES COMPLETE!")
    print(f"   Total test cases updated: {total}")
    print(f"   Output directory: {updated_dir}")
    print("="*60)


if __name__ == "__main__":
    main()
