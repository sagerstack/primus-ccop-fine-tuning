#!/usr/bin/env python3
"""Build corrected ground-truth mapping from agent-team reviewer outputs."""
import json, glob, re

corrections = {}
for f in sorted(glob.glob('/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/agents/*-reviewer.json')):
    d = json.load(open(f))
    tid = d['test_id']
    raw = d.get('recommended_clause_reference', [])

    def norm(s):
        s = str(s).strip()
        for prefix in ['CCoP 2.0::', 'Cybersecurity Act 2018::', 'CCoP Response to Feedback::', 'Auditing Guidelines::', 'Risk Assessment Guide::', 'Threat Modelling Guide::', 'Security By Design::']:
            if s.startswith(prefix):
                s = s[len(prefix):]
                break
        return s

    ccop_only = []
    external = []
    for c in raw:
        n = norm(c)
        if re.match(r'^\d+(\.\d+)*(\([a-z]\))?$', n):
            ccop_only.append(n)
        else:
            external.append(n)

    corrections[tid] = {
        'verdict': d.get('overall_verdict', ''),
        'recommended_full': raw,
        'recommended_ccop_only': ccop_only,
        'recommended_external': external,
    }

with open('/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/agents/corrected-gt.json', 'w') as f:
    json.dump(corrections, f, indent=2)

orig = json.load(open('/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/agents/30-cases.json'))
print(f"{'test_id':12} {'orig':5} {'new_ccop':9} {'new_ext':8} verdict")
print('-'*80)
for tid in sorted(corrections.keys()):
    o = orig[tid]['clause_reference']
    c = corrections[tid]
    print(f"{tid:12} {len(o):5} {len(c['recommended_ccop_only']):9} {len(c['recommended_external']):8} {c['verdict'][:42]}")

total_orig = sum(len(orig[tid]['clause_reference']) for tid in corrections)
total_new_ccop = sum(len(c['recommended_ccop_only']) for c in corrections.values())
total_new_ext = sum(len(c['recommended_external']) for c in corrections.values())
print(f"\nTotals — orig: {total_orig}, new CCoP: {total_new_ccop}, new external: {total_new_ext}")
