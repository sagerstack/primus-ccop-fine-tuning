#!/usr/bin/env bash
#
# run_eval.sh — thin wrapper for the 18-case report comparison runs.
#
# Bakes in the boilerplate that's identical across every comparison run:
#   --model <MODEL>, the 18-case stratified sample (bdc4927d), --out-dir <OUT_DIR>,
#   --verbose + --verbose-io (full granularity), a per-run log, and macOS caffeinate.
# Everything YOU pass is forwarded verbatim to `ccop-eval evaluate run`.
#
# Per run you get, under OUT_DIR:
#   <month>/<run_id>.json           — scores + D1-D6 + Q&A + provenance
#   <month>/<run_id>-contexts.json  — retrieved contexts per case
#   logs/eval-<mode><flags>-<ts>.log — retrieval diagnostics + filter funnel (stderr)
#
# Usage (no need to pass --verbose/--verbose-io — they're forced on):
#   scripts/run_eval.sh <evaluate-run flags...>
#
# The 4 report modes:
#   scripts/run_eval.sh --mode hybrid --no-contextual
#   scripts/run_eval.sh --mode hybrid --contextual
#   scripts/run_eval.sh --mode graphont
#   scripts/run_eval.sh --mode graphont-agentic --corrective
#
# Overridable via env vars:
#   MODEL=<name>       (default: primus-reasoning)
#   OUT_DIR=<path>     (default: results/evaluations/final)
#
set -euo pipefail

# Resolve the src/ root from this script's location (scripts/ is a child of src/)
# so the wrapper works regardless of the caller's cwd, and relative paths
# (out-dir, config/.env.local) resolve correctly.
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SRC_DIR"

MODEL="${MODEL:-primus-reasoning}"
OUT_DIR="${OUT_DIR:-results/evaluations/final}"

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <evaluate-run flags...>" >&2
  echo "  e.g. $0 --mode hybrid --contextual --verbose-io" >&2
  exit 1
fi

# 18-case stratified sample (bdc4927d) — one case per active benchmark.
# Keep in sync with FIXED_18_TEST_IDS in
# application/use_cases/clause_hit_harness.py (note B07 is B07-006).
TEST_IDS=(
  B01-001 B02-001 B03-001 B04-001 B05-001 B06-001 B07-006 B08-001 B09-001
  B10-001 B12-001 B13-001 B14-001 B18-001 B21-001 B22-001 B23-001 B24-001
)
IDS=()
for id in "${TEST_IDS[@]}"; do IDS+=(--test-ids "$id"); done

# Build an identifiable log filename from the mode + differentiating flags so
# each run's full console transcript is preserved next to its JSON results.
_mode="run"; _tag=""
_args=("$@")
for _i in "${!_args[@]}"; do
  case "${_args[$_i]}" in
    -m|--mode) _mode="${_args[$((_i + 1))]:-run}" ;;
    --mode=*)  _mode="${_args[$_i]#--mode=}" ;;
    --contextual) _tag="${_tag}-ctx" ;;
    --corrective) _tag="${_tag}-corr" ;;
  esac
done
LOG_DIR="$OUT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/eval-${_mode}${_tag}-$(date -u +%Y%m%d-%H%M%S).log"

# --verbose (retrieval filter funnel: RRF, rerank, grading, agentic filter) and
# --verbose-io (per-case prompts + retrieved contexts) are forced ON so the
# report captures full granularity.
#
# Stream split so the terminal keeps Rich colours while the log stays clean:
#   stdout — Rich summary tables / per-case panels (COLOURED) — goes straight to
#     the terminal. We deliberately do NOT pipe it: piping makes Rich detect a
#     non-TTY and strip all colour (that was the bug).
#   stderr — the --verbose diagnostic funnel (retrieval, RRF, rerank, grading,
#     agentic filter) — is tee'd to the terminal AND the clean $LOG.
# Structured per-case data (scores, D1-D6, Q&A, chunks) already lives in the JSON.
echo "▶ ccop-eval evaluate run --model $MODEL --verbose --verbose-io $* [+${#TEST_IDS[@]} test-ids] --out-dir $OUT_DIR" >&2
echo "  log (diagnostics): $LOG" >&2

# caffeinate -i prevents idle sleep mid-run (macOS only; skipped elsewhere).
if command -v caffeinate >/dev/null 2>&1; then
  caffeinate -i poetry run ccop-eval evaluate run \
    --model "$MODEL" --verbose --verbose-io "$@" "${IDS[@]}" --out-dir "$OUT_DIR" 2> >(tee "$LOG" >&2)
else
  poetry run ccop-eval evaluate run \
    --model "$MODEL" --verbose --verbose-io "$@" "${IDS[@]}" --out-dir "$OUT_DIR" 2> >(tee "$LOG" >&2)
fi
