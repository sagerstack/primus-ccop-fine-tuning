#!/usr/bin/env python3
"""
Apply agent-team-corrected ground truth to test suite JSONL files.

For each of the 30 sample test cases:
  1. Read corrected_gt.json (agent-team output)
  2. Find the matching test_case in ground-truth/test-suite/*.jsonl
  3. Save original clause_reference under metadata.clause_reference_original
  4. Replace metadata.clause_reference with the agent-team's recommendation
  5. Write back

Idempotent: if clause_reference_original is already set, don't double-back-up.
"""
import glob
import json
import os
import shutil
from datetime import datetime

BASE = "/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc"


def main():
    corrected = json.load(open(f"{BASE}/.lab/workspace/agents/corrected-gt.json"))
    print(f"Loaded {len(corrected)} corrected GT entries")

    files = glob.glob(f"{BASE}/ground-truth/test-suite/*.jsonl")
    files = [f for f in files if ".bak" not in f]

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    n_updated = 0
    n_skipped = 0

    for fp in files:
        rows = []
        with open(fp) as f:
            for line in f:
                if not line.strip():
                    continue
                rows.append(json.loads(line))

        any_updated = False
        for row in rows:
            tid = row.get("test_id", "")
            if tid not in corrected:
                continue
            entry = corrected[tid]
            new_refs = entry.get("recommended_ccop_only", [])
            if not new_refs:
                # Some cases (e.g. B21-001) are correct refusal — skip
                continue

            md = row.setdefault("metadata", {})
            current = md.get("clause_reference", [])
            # Idempotent: only back up if not already
            if "clause_reference_original" not in md:
                md["clause_reference_original"] = current
            md["clause_reference"] = new_refs
            md["clause_reference_corrected_by"] = "agent-team-2026-04-26"
            md["clause_reference_corrected_verdict"] = entry.get("verdict", "")
            any_updated = True
            n_updated += 1

        if any_updated:
            # Backup file then write
            bak = f"{fp}.{timestamp}.bak"
            shutil.copy(fp, bak)
            print(f"Backed up {os.path.basename(fp)} → {os.path.basename(bak)}")
            with open(fp, "w") as f:
                for row in rows:
                    f.write(json.dumps(row) + "\n")
            print(f"  ✓ updated")
        else:
            n_skipped += 1

    print(f"\nDone. {n_updated} test cases updated. {n_skipped} files unchanged.")


if __name__ == "__main__":
    main()
