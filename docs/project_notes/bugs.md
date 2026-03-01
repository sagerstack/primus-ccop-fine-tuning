# Bug Log

This file logs bugs, their solutions, and prevention notes. Keep entries brief and chronological.

## Format

Each bug entry should include:
- Date (YYYY-MM-DD)
- Brief description of the bug/issue
- Solution or fix applied
- Any prevention notes (optional)

Use bullet lists for simplicity. Older entries can be manually removed when they become irrelevant.

---

## Entries

### 2026-02-04 - Hallucination Detection False Positives
- **Issue**: `ModelResponse.contains_hallucination_indicators()` flags legitimate uncertainty language as hallucinations
- **Root Cause**: Overly aggressive regex patterns treating hedging language ("may require", "depends on context") as hallucination indicators
- **Status**: Known issue (documented in .planning/codebase/CONCERNS.md)
- **Workaround**: None currently - requires distinguishing uncertainty language from fabrication indicators
- **Prevention**: Separate uncertainty detection from fabrication detection in future refactor

### 2026-02-04 - Grounding Score Discontinuity
- **Issue**: Grounding scores jump discontinuously (1.0, 0.7, 0.0) based on discrete violation thresholds
- **Root Cause**: Hardcoded discrete thresholds in `_calculate_grounding_score()` without gradual penalty
- **Status**: Known issue
- **Impact**: Minor grounding issues cause disproportionate score drops
- **Prevention**: Replace discrete thresholds with continuous penalty function

---

## Tips

- Keep descriptions under 2-3 lines
- Focus on what was learned, not exhaustive details
- Include enough context for future reference
- Date entries so you know how recent the issue is
- Periodically clean out very old entries (6+ months)
