"""
Script to generate missing key_facts for test cases.

Extracts atomic, verifiable facts from expected responses using intelligent
sentence splitting and keyword scoring.
"""

import json
import sys
from pathlib import Path
from typing import Any


def extract_key_facts_from_response(test_id: str, expected_response: str) -> list[str]:
    """
    Extract atomic facts from expected response using intelligent sentence splitting.

    Args:
        test_id: Test case identifier
        expected_response: The expected response text

    Returns:
        List of atomic facts
    """
    return intelligent_extract_facts(expected_response)


def intelligent_extract_facts(expected_response: str) -> list[str]:
    """
    Extract facts by intelligently splitting into sentences.

    Prioritizes sentences with regulatory keywords and specific requirements.

    Args:
        expected_response: The expected response text

    Returns:
        List of sentences as atomic facts
    """
    import re

    # Split by sentence-ending punctuation (more sophisticated)
    # Handle abbreviations like "e.g.", "i.e.", "etc."
    text = expected_response.replace('e.g.', 'eg').replace('i.e.', 'ie').replace('etc.', 'etc')
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    # Restore periods in facts
    sentences = [s.replace('eg', 'e.g.').replace('ie', 'i.e.').replace('etc', 'etc.') for s in sentences]

    # Score sentences by importance (regulatory keywords)
    importance_keywords = [
        'must', 'require', 'shall', 'should', 'ciio', 'clause', 'ccop',
        'within', 'at least', 'minimum', 'framework', 'policy', 'control',
        'authentication', 'security', 'incident', 'patch', 'vulnerability',
        'log', 'monitor', 'test', 'audit', 'compliance', 'risk'
    ]

    scored_sentences = []
    for sentence in sentences:
        if len(sentence) < 30:  # Skip very short sentences
            continue

        # Calculate importance score
        sentence_lower = sentence.lower()
        score = sum(1 for keyword in importance_keywords if keyword in sentence_lower)

        # Bonus for numbers (specific requirements)
        if re.search(r'\d+', sentence):
            score += 2

        scored_sentences.append((score, sentence))

    # Sort by score (descending)
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    # Take top 4-6 facts
    facts = [s[1] + ('.' if not s[1].endswith('.') else '') for s in scored_sentences[:6]]

    # Ensure we have at least 2 facts
    if len(facts) < 2:
        # Just take all sentences > 30 chars
        facts = [s + '.' for s in sentences if len(s) >= 30][:6]

    return facts


def update_jsonl_with_key_facts(jsonl_path: Path, updates: dict[str, list[str]]) -> None:
    """
    Update JSONL file with new key_facts.

    Args:
        jsonl_path: Path to JSONL file
        updates: Dictionary mapping test_id to list of key_facts
    """
    # Read all lines
    lines = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            test_case = json.loads(line)
            test_id = test_case.get('test_id')

            # Update if in updates dict
            if test_id in updates:
                test_case['key_facts'] = updates[test_id]
                print(f"  Updated {test_id} with {len(updates[test_id])} facts")

            lines.append(json.dumps(test_case))

    # Write back
    with open(jsonl_path, 'w') as f:
        for line in lines:
            f.write(line + '\n')

    print(f"✓ Updated {jsonl_path.name}")


def main():
    """Main function to generate missing key_facts."""
    test_suite_dir = Path('/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/ground-truth/phase-2/test-suite')

    # Find all test cases missing key_facts
    missing_by_file: dict[str, list[dict[str, Any]]] = {}

    print("Scanning for missing key_facts...")
    for jsonl_file in sorted(test_suite_dir.glob('*.jsonl')):
        with open(jsonl_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    test_case = json.loads(line)
                    test_id = test_case.get('test_id', 'unknown')
                    key_facts = test_case.get('key_facts', [])

                    # Check if missing or placeholder
                    if not key_facts or (len(key_facts) == 1 and 'Unable to extract' in key_facts[0]):
                        if jsonl_file.name not in missing_by_file:
                            missing_by_file[jsonl_file.name] = []

                        missing_by_file[jsonl_file.name].append({
                            'test_id': test_id,
                            'expected_response': test_case.get('expected_response', '')
                        })
                except json.JSONDecodeError:
                    continue

    total_missing = sum(len(cases) for cases in missing_by_file.values())
    print(f"Found {total_missing} test cases missing key_facts across {len(missing_by_file)} files")
    print()

    # Process each file
    for file_name, test_cases in missing_by_file.items():
        print(f"\nProcessing {file_name} ({len(test_cases)} cases)...")

        updates = {}
        for test_case in test_cases:
            test_id = test_case['test_id']
            expected_response = test_case['expected_response']

            print(f"  Extracting facts for {test_id}...")
            key_facts = extract_key_facts_from_response(test_id, expected_response)
            updates[test_id] = key_facts

        # Update JSONL file
        jsonl_path = test_suite_dir / file_name
        update_jsonl_with_key_facts(jsonl_path, updates)

    print()
    print("=" * 60)
    print(f"✓ Successfully generated key_facts for {total_missing} test cases")
    print("=" * 60)


if __name__ == '__main__':
    main()
