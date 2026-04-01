#!/usr/bin/env python3
"""
Update test case schema for all benchmarks to align with updated scoring methodology.

Changes:
1. Add benchmark_category (universal)
2. Add key_facts (universal)
3. Add/rename expected_label (classification + safety)
4. Add reasoning_dimensions (reasoning only)
5. Add/rename safety_checks (safety only)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

# Benchmark category mapping
BENCHMARK_CATEGORIES = {
    "B1": "classification",
    "B2": "classification",
    "B3": "reasoning",
    "B4": "classification",
    "B5": "classification",
    "B6": "reasoning",
    "B7": "reasoning",
    "B8": "reasoning",
    "B9": "reasoning",
    "B10": "reasoning",
    "B11": "reasoning",
    "B12": "reasoning",
    "B13": "reasoning",
    "B14": "reasoning",
    "B15": "reasoning",
    "B16": "reasoning",
    "B17": "reasoning",
    "B18": "reasoning",
    "B19": "reasoning",
    "B20": "safety",
    "B21": "safety",
}

def extract_key_facts(expected_response: str, benchmark_id: str) -> List[str]:
    """Extract key facts from expected response."""
    facts = []

    # Split by common delimiters
    lines = expected_response.split('\n')

    # Extract numbered points
    for line in lines:
        # Match patterns like "(1)", "1.", "•", "-", etc.
        if re.match(r'^\s*[\(（]?\d+[\)）]', line) or \
           re.match(r'^\s*\d+\.', line) or \
           re.match(r'^\s*[•\-\*]', line):
            fact = re.sub(r'^\s*[\(（]?\d+[\)）]\.?\s*', '', line)
            fact = re.sub(r'^\s*[•\-\*]\s*', '', fact)
            fact = fact.strip()
            if fact and len(fact) > 20:  # Skip very short lines
                facts.append(fact)

    # If no numbered points, extract sentences
    if len(facts) < 3:
        sentences = re.split(r'[.!?](?=\s+[A-Z])', expected_response)
        facts = []
        for sent in sentences:
            sent = sent.strip()
            if sent and len(sent) > 30 and len(sent) < 200:
                # Remove markdown formatting
                sent = re.sub(r'\*\*([^*]+)\*\*', r'\1', sent)
                facts.append(sent)

    # Limit to 8 facts max
    return facts[:8]


def get_expected_label(test_case: Dict[str, Any], benchmark_id: str) -> str:
    """Get expected label for classification/safety benchmarks."""

    # Check if already exists under different name
    if "correct_classification" in test_case:
        return test_case["correct_classification"]
    if "correct_answer" in test_case:
        return test_case["correct_answer"]

    # Extract from expected_response
    response = test_case.get("expected_response", "")

    # For B2 (compliance classification)
    if benchmark_id == "B2":
        if "**Compliant**" in response or "Compliant." in response[:100]:
            return "Compliant"
        elif "**Non-Compliant**" in response or "Non-Compliant." in response[:100]:
            return "Non-Compliant"
        elif "**Non-compliant**" in response or "Non-compliant." in response[:100]:
            return "Non-Compliant"

    # For B21 (hallucination)
    if benchmark_id == "B21":
        # Extract first sentence as label
        first_sentence = response.split('.')[0].strip()
        return first_sentence

    # For B1, B4, B5 - extract key answer
    first_sentence = response.split('.')[0].strip()
    # Remove markdown
    first_sentence = re.sub(r'\*\*([^*]+)\*\*', r'\1', first_sentence)
    return first_sentence[:100]  # Limit length


def get_reasoning_dimensions(test_case: Dict[str, Any]) -> Dict[str, str]:
    """Get reasoning dimensions from evaluation_criteria."""
    criteria = test_case.get("evaluation_criteria", {})

    dimensions = {}

    # Map existing criteria to reasoning dimensions
    if "accuracy" in criteria:
        dimensions["factual_accuracy"] = criteria["accuracy"]
    if "completeness" in criteria:
        dimensions["comprehensiveness"] = criteria["completeness"]
    if "reasoning" in criteria:
        dimensions["logical_coherence"] = criteria["reasoning"]
    if "context" in criteria:
        dimensions["regulatory_grounding"] = criteria["context"]
    if "clarity" in criteria:
        dimensions["communication_clarity"] = criteria["clarity"]
    if "nuance" in criteria:
        dimensions["contextual_nuance"] = criteria["nuance"]
    if "practicality" in criteria:
        dimensions["practical_applicability"] = criteria["practicality"]

    return dimensions


def update_test_case(test_case: Dict[str, Any], benchmark_id: str) -> Dict[str, Any]:
    """Update a single test case with new schema."""

    # Get benchmark category
    category = BENCHMARK_CATEGORIES.get(benchmark_id, "reasoning")

    # Add benchmark_category
    test_case["benchmark_category"] = category

    # Extract and add key_facts
    key_facts = extract_key_facts(test_case.get("expected_response", ""), benchmark_id)
    test_case["key_facts"] = key_facts

    # Category-specific updates
    if category == "classification":
        # Add expected_label
        label = get_expected_label(test_case, benchmark_id)
        test_case["expected_label"] = label

        # Remove old field if exists
        if "correct_classification" in test_case:
            del test_case["correct_classification"]

    elif category == "safety":
        # Add expected_label
        label = get_expected_label(test_case, benchmark_id)
        test_case["expected_label"] = label

        # Rename hallucination_indicators to safety_checks
        if "hallucination_indicators" in test_case:
            test_case["safety_checks"] = test_case["hallucination_indicators"]
            del test_case["hallucination_indicators"]

        # Remove old field if exists
        if "correct_answer" in test_case:
            del test_case["correct_answer"]

    elif category == "reasoning":
        # Add reasoning_dimensions
        dimensions = get_reasoning_dimensions(test_case)
        if dimensions:
            test_case["reasoning_dimensions"] = dimensions

    return test_case


def process_benchmark_file(input_path: Path, output_path: Path):
    """Process a single benchmark JSONL file."""

    # Extract benchmark ID from filename
    filename = input_path.stem
    benchmark_id = filename.split('_')[0].upper().replace('B0', 'B').replace('B', 'B')

    print(f"\nProcessing {filename} (Benchmark {benchmark_id})...")

    updated_cases = []

    with open(input_path, 'r') as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                test_case = json.loads(line)
                updated_case = update_test_case(test_case, benchmark_id)
                updated_cases.append(updated_case)
                print(f"  Updated {test_case.get('test_id', f'case-{i}')}")
            except Exception as e:
                print(f"  ERROR processing line {i}: {e}")

    # Write updated cases
    with open(output_path, 'w') as f:
        for case in updated_cases:
            f.write(json.dumps(case, ensure_ascii=False) + '\n')

    print(f"  ✅ Wrote {len(updated_cases)} updated test cases")
    return len(updated_cases)


def main():
    """Process all benchmark files."""

    test_suite_dir = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/ground-truth/phase-2/test-suite")
    updated_dir = test_suite_dir / "updated"
    updated_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("Test Case Schema Update Tool")
    print("=" * 60)

    total_cases = 0
    files_processed = 0

    # Process all JSONL files
    for jsonl_file in sorted(test_suite_dir.glob("b*.jsonl")):
        output_file = updated_dir / jsonl_file.name
        count = process_benchmark_file(jsonl_file, output_file)
        total_cases += count
        files_processed += 1

    print("\n" + "=" * 60)
    print(f"✅ Update Complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Total test cases updated: {total_cases}")
    print(f"   Updated files location: {updated_dir}")
    print("=" * 60)

    print("\n📋 Next steps:")
    print("1. Review updated files in test-suite/updated/")
    print("2. Validate schema with validation script")
    print("3. Replace original files with updated versions")


if __name__ == "__main__":
    main()
