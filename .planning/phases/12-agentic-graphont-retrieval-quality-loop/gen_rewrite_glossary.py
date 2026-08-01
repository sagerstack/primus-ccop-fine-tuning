#!/usr/bin/env python3
"""Generate the corpus canonical-vocabulary glossary for the corrective rewrite prompt.

Reads src/rag/graph/ontology_v2/concept_aliases.json, extracts concepts with
lay-synonym surface forms (>1 surface entry), and emits a formatted glossary
block for inclusion in the CRAG corrective rewrite system prompt.
"""
import json
from pathlib import Path


def main():
    # Read concept_aliases.json from src/rag/graph/ontology_v2/
    repo_root = Path(__file__).resolve().parents[3]
    aliases_path = repo_root / "src" / "rag" / "graph" / "ontology_v2" / "concept_aliases.json"
    
    with open(aliases_path) as f:
        data = json.load(f)
    
    concepts = data["concepts"]
    
    # Filter to concepts with >1 surface form (i.e., have lay-synonyms)
    with_synonyms = {
        k: v for k, v in concepts.items()
        if len(v.get("surface", [])) > 1
    }
    
    # Sort by concept name for deterministic output
    sorted_concepts = sorted(with_synonyms.items())
    
    print(f"# Corpus Canonical Vocabulary Glossary ({len(sorted_concepts)} concepts)\n")
    print("Prefer these canonical phrases from the CCoP 2.0 corpus:\n")
    
    for concept_name, concept_data in sorted_concepts:
        surface_forms = concept_data["surface"]
        # Format: join with " / " or "; " — using semicolon for consistency with the brief
        formatted = "; ".join(surface_forms)
        # Wrap long lines at ~80 chars for readability
        if len(formatted) > 70:
            # Split at semicolons and format multi-line
            parts = surface_forms
            lines = []
            current_line = parts[0]
            for part in parts[1:]:
                if len(current_line) + len(part) + 2 < 70:
                    current_line += f"; {part}"
                else:
                    lines.append(current_line)
                    current_line = part
            lines.append(current_line)
            formatted = "\n    ".join(lines)
        
        print(f"  {formatted}")
    
    print(f"\n(Generated from {aliases_path})")


if __name__ == "__main__":
    main()
