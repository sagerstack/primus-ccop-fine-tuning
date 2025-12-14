# Archive - Historical Test Cases

This directory contains the original test case directories that were consolidated into `../test-suite/`.

**Archived on**: December 14, 2025
**Reason**: Consolidated into single standardized test-suite directory

---

## Contents

### test-cases-old/
Original test cases directory from initial benchmark development
- **8 JSONL files** (6 active, 2 deprecated)
- **44 active test cases** (B1, B2, B4, B5, B7, B21)
- **13 deprecated cases** (old B3, old B5)

### test-cases-old-new/
Newly created test cases for updated B1-B21 framework
- **15 JSONL files**
- **72 test cases** (B3, B6, B8-B20)

---

## Current Active Directory

**Use this instead**: `../test-suite/`
- **21 JSONL files** (one per benchmark B1-B21)
- **116 test cases** total
- **Standardized naming**: b01_ through b21_
- **Status**: Production ready

---

## Purpose of Archive

These directories are preserved for:
- **Historical reference**
- **Audit trail** of test case development
- **Comparison** against consolidated version
- **Recovery** if needed (backup)

**Do not use for baseline testing** - use `../test-suite/` instead.

---

## Migration

All active test cases from both archived directories have been:
- ✅ Copied to `../test-suite/` with standardized naming
- ✅ Deprecated files (b3_clause_citation, b5_singapore_terminology) excluded
- ✅ File names standardized (b01-b21)
- ✅ No data loss - all 116 active test cases preserved

See `../test-suite/CONSOLIDATION_SUMMARY.md` for detailed mapping.

---

*Archived: December 14, 2025*
*Consolidated into: test-suite/*
