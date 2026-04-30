#!/usr/bin/env bash
#
# CCoP 2.0 Evaluation Framework — Local Environment Orchestrator
#
# Brings up (or tears down) the full local stack required to run evaluations:
#   1. Qdrant vector store       (docker compose service)
#   2. Ollama model server       (local process)
#   3. Llama-Primus-Reasoning    (verified present in Ollama)
#   4. Qdrant collection         (ingested from ccop-official/ if missing or empty)
#
# Idempotent: safe to run repeatedly. Only ingests if collection is missing or empty.
#
# Usage:
#   ./src/scripts/start_local.sh          # start / verify everything
#   ./src/scripts/start_local.sh --stop   # tear down services started by this script
#   ./src/scripts/start_local.sh --help
#

set -euo pipefail

# ─── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SRC_DIR/.." && pwd)"

# ─── Config (overridable via env) ───────────────────────────────────────────
QDRANT_URL="${CCOP_QDRANT_URL:-http://localhost:6333}"
QDRANT_COLLECTION="${CCOP_QDRANT_COLLECTION_NAME:-ccop_clauses_hybrid}"
OLLAMA_HOST="${CCOP_OLLAMA_HOST:-http://localhost:11434}"
MODEL_NAME="${CCOP_MODEL_NAME:-primus-reasoning}"
CCOP_DIR="${CCOP_DIR:-$REPO_ROOT/ccop-official}"

OLLAMA_PIDFILE="/tmp/ccop-ollama.pid"
OLLAMA_LOGFILE="/tmp/ccop-ollama.log"

QDRANT_READY_TIMEOUT_SEC=60
OLLAMA_READY_TIMEOUT_SEC=30

# ─── Colors ─────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

# ─── Help ───────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
CCoP 2.0 Local Environment Orchestrator

Usage:
  $(basename "$0")                    Start / verify all services (idempotent)
  $(basename "$0") --stop             Stop services started by this script
  $(basename "$0") --status           Report state; exit 0 if all green, 1 otherwise
  $(basename "$0") --status --deep    Also run retrieval + generation smoke tests
  $(basename "$0") --help             Show this help

Configuration (override via environment):
  CCOP_QDRANT_URL              (default: http://localhost:6333)
  CCOP_QDRANT_COLLECTION_NAME  (default: ccop_clauses_hybrid)
  CCOP_OLLAMA_HOST             (default: http://localhost:11434)
  CCOP_MODEL_NAME              (default: primus-reasoning)
  CCOP_DIR                     (default: <repo>/ccop-official)
EOF
}

# ─── Preflight ──────────────────────────────────────────────────────────────
preflight() {
    local missing=()
    have docker || missing+=("docker")
    have curl   || missing+=("curl")
    have poetry || missing+=("poetry")

    if ((${#missing[@]} > 0)); then
        error "Missing required tools: ${missing[*]}"
        exit 1
    fi

    if ! docker info >/dev/null 2>&1; then
        error "Docker daemon not reachable. Start Docker Desktop and retry."
        exit 1
    fi
}

# ─── Qdrant ─────────────────────────────────────────────────────────────────
qdrant_healthy() {
    curl -fsS "$QDRANT_URL/healthz" >/dev/null 2>&1
}

start_qdrant() {
    info "Qdrant: starting via docker compose..."
    (cd "$REPO_ROOT" && docker compose up -d qdrant) >/dev/null

    info "Qdrant: waiting for health (up to ${QDRANT_READY_TIMEOUT_SEC}s)..."
    local waited=0
    until qdrant_healthy; do
        if (( waited >= QDRANT_READY_TIMEOUT_SEC )); then
            error "Qdrant did not become healthy within ${QDRANT_READY_TIMEOUT_SEC}s"
            (cd "$REPO_ROOT" && docker compose logs --tail=30 qdrant) || true
            exit 1
        fi
        sleep 2
        waited=$((waited + 2))
    done
    success "Qdrant healthy at $QDRANT_URL"
}

ensure_qdrant() {
    if qdrant_healthy; then
        success "Qdrant already running at $QDRANT_URL"
    else
        start_qdrant
    fi
}

stop_qdrant() {
    info "Qdrant: stopping..."
    (cd "$REPO_ROOT" && docker compose stop qdrant) >/dev/null
    success "Qdrant stopped"
}

# ─── Ollama ─────────────────────────────────────────────────────────────────
ollama_healthy() {
    curl -fsS "$OLLAMA_HOST/api/tags" >/dev/null 2>&1
}

start_ollama() {
    if ! have ollama; then
        error "Ollama not installed. Run: ./src/scripts/setup_ollama.sh"
        exit 1
    fi

    info "Ollama: starting serve in background (log: $OLLAMA_LOGFILE)..."
    nohup ollama serve >"$OLLAMA_LOGFILE" 2>&1 &
    echo $! > "$OLLAMA_PIDFILE"

    info "Ollama: waiting for API (up to ${OLLAMA_READY_TIMEOUT_SEC}s)..."
    local waited=0
    until ollama_healthy; do
        if (( waited >= OLLAMA_READY_TIMEOUT_SEC )); then
            error "Ollama did not become ready within ${OLLAMA_READY_TIMEOUT_SEC}s"
            rm -f "$OLLAMA_PIDFILE"
            exit 1
        fi
        sleep 1
        waited=$((waited + 1))
    done
    success "Ollama ready at $OLLAMA_HOST (pid $(cat "$OLLAMA_PIDFILE"))"
}

ensure_ollama() {
    if ollama_healthy; then
        if [[ -f "$OLLAMA_PIDFILE" ]]; then
            success "Ollama already running (managed, pid $(cat "$OLLAMA_PIDFILE"))"
        else
            success "Ollama already running (externally managed)"
        fi
    else
        start_ollama
    fi
}

verify_model() {
    if ! have ollama; then
        warn "ollama CLI unavailable — cannot verify model '$MODEL_NAME' is loaded"
        return
    fi

    if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qE "^${MODEL_NAME}(:|$)"; then
        success "Model '$MODEL_NAME' present in Ollama"
    else
        warn  "Model '$MODEL_NAME' NOT found in Ollama"
        warn  "Run one-time setup: cd src && poetry run ccop-eval setup model"
    fi
}

stop_ollama() {
    if [[ ! -f "$OLLAMA_PIDFILE" ]]; then
        info "Ollama: not started by this script — leaving it running"
        return
    fi

    local pid
    pid="$(cat "$OLLAMA_PIDFILE")"
    if kill -0 "$pid" 2>/dev/null; then
        info "Ollama: stopping pid $pid..."
        kill -TERM "$pid" 2>/dev/null || true
        # grace period
        local waited=0
        while kill -0 "$pid" 2>/dev/null && (( waited < 10 )); do
            sleep 1
            waited=$((waited + 1))
        done
        if kill -0 "$pid" 2>/dev/null; then
            warn "Ollama did not exit gracefully, sending SIGKILL"
            kill -KILL "$pid" 2>/dev/null || true
        fi
        success "Ollama stopped"
    else
        warn "Ollama pidfile present but pid $pid not running"
    fi
    rm -f "$OLLAMA_PIDFILE"
}

# ─── Qdrant collection / ingestion ──────────────────────────────────────────
# Returns 0 if collection needs ingestion (missing or empty), 1 if populated.
collection_needs_ingestion() {
    local body http
    body="$(mktemp)"
    http="$(curl -s -o "$body" -w '%{http_code}' "$QDRANT_URL/collections/$QDRANT_COLLECTION" || echo "000")"

    if [[ "$http" == "404" ]]; then
        rm -f "$body"
        info "Collection '$QDRANT_COLLECTION' does not exist"
        return 0
    fi

    if [[ "$http" != "200" ]]; then
        rm -f "$body"
        error "Unexpected HTTP $http from Qdrant when checking collection"
        return 0
    fi

    # Parse points_count without jq dependency.
    local points
    points="$(grep -oE '"points_count"[[:space:]]*:[[:space:]]*[0-9]+' "$body" | grep -oE '[0-9]+$' | head -1)"
    rm -f "$body"

    if [[ -z "$points" ]] || [[ "$points" == "0" ]]; then
        info "Collection '$QDRANT_COLLECTION' exists but is empty (points_count=${points:-unknown})"
        return 0
    fi

    success "Collection '$QDRANT_COLLECTION' already populated (points_count=$points)"
    return 1
}

run_ingestion() {
    if [[ ! -d "$CCOP_DIR" ]]; then
        error "CCoP documents directory not found: $CCOP_DIR"
        error "Set CCOP_DIR or place documents at <repo>/ccop-official"
        exit 1
    fi

    info "Ingesting CCoP documents from $CCOP_DIR into '$QDRANT_COLLECTION'..."
    info "This takes several minutes (Docling parse + BGE embeddings)."

    (cd "$SRC_DIR" && poetry run python -m rag.ingestion.run_ingestion --ccop-dir "$CCOP_DIR")

    success "Ingestion complete"
}

ensure_collection() {
    if collection_needs_ingestion; then
        run_ingestion
    fi
}

# ─── Status / health ────────────────────────────────────────────────────────
# Prints a human-readable report AND returns a proper exit code:
#   0 — all checks green
#   1 — at least one check degraded (DOWN / missing / not loaded / smoke failed)
#
# Accumulates failures in FAILURES[] so a summary can be emitted at the end.

declare -a FAILURES=()

fail_check() {
    warn "$1"
    FAILURES+=("$1")
}

smoke_retrieval() {
    info "Smoke: hybrid retrieval round-trip..."
    local tmp
    tmp="$(mktemp)"
    if (cd "$SRC_DIR" && poetry run ccop-eval query ask \
            "What are the access control requirements?" --mode rag-only \
            >"$tmp" 2>&1); then
        success "Smoke: retrieval OK"
        rm -f "$tmp"
        return 0
    fi
    fail_check "Smoke: retrieval FAILED (see output below)"
    sed 's/^/       /' "$tmp" | tail -20
    rm -f "$tmp"
    return 1
}

smoke_generation() {
    info "Smoke: Ollama generation round-trip..."
    # Short prompt, capped output — should return within ~15s.
    local payload response
    payload="$(printf '{"model":"%s","prompt":"Reply with OK.","stream":false,"options":{"num_predict":4}}' "$MODEL_NAME")"
    response="$(curl -fsS --max-time 30 "$OLLAMA_HOST/api/generate" \
                     -H 'Content-Type: application/json' \
                     -d "$payload" 2>&1 || true)"

    if [[ -n "$response" ]] && echo "$response" | grep -q '"response"'; then
        success "Smoke: generation OK"
        return 0
    fi
    fail_check "Smoke: generation FAILED"
    return 1
}

status() {
    local deep="${1:-false}"
    FAILURES=()
    echo "── CCoP Local Environment Status ──"

    # Qdrant service
    if qdrant_healthy; then
        success "Qdrant: UP at $QDRANT_URL"
    else
        fail_check "Qdrant: DOWN at $QDRANT_URL"
    fi

    # Ollama service
    if ollama_healthy; then
        if [[ -f "$OLLAMA_PIDFILE" ]]; then
            success "Ollama: UP (managed, pid $(cat "$OLLAMA_PIDFILE"))"
        else
            success "Ollama: UP (externally managed)"
        fi
    else
        fail_check "Ollama: DOWN at $OLLAMA_HOST"
    fi

    # Qdrant collection
    if qdrant_healthy; then
        local body http
        body="$(mktemp)"
        http="$(curl -s -o "$body" -w '%{http_code}' "$QDRANT_URL/collections/$QDRANT_COLLECTION" || echo "000")"
        if [[ "$http" == "200" ]]; then
            local points
            points="$(grep -oE '"points_count"[[:space:]]*:[[:space:]]*[0-9]+' "$body" | grep -oE '[0-9]+$' | head -1)"
            if [[ -z "$points" ]] || [[ "$points" == "0" ]]; then
                fail_check "Collection '$QDRANT_COLLECTION': empty (points_count=${points:-unknown})"
            else
                success "Collection '$QDRANT_COLLECTION': present (points_count=$points)"
            fi
        elif [[ "$http" == "404" ]]; then
            fail_check "Collection '$QDRANT_COLLECTION': missing"
        else
            fail_check "Collection '$QDRANT_COLLECTION': unexpected HTTP $http"
        fi
        rm -f "$body"
    fi

    # Model presence in Ollama
    if have ollama && ollama_healthy; then
        if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qE "^${MODEL_NAME}(:|$)"; then
            success "Model '$MODEL_NAME': loaded"
        else
            fail_check "Model '$MODEL_NAME': NOT loaded"
        fi
    fi

    # Deep smoke tests — only when requested
    if [[ "$deep" == "true" ]]; then
        echo "── Deep smoke tests ──"
        if qdrant_healthy && ollama_healthy; then
            smoke_retrieval || true
            smoke_generation || true
        else
            warn "Skipping smoke tests: prerequisite services DOWN"
        fi
    fi

    # Summary + exit code
    echo "──────────────────────────────────"
    if ((${#FAILURES[@]} == 0)); then
        success "All checks passed"
        return 0
    fi
    error "${#FAILURES[@]} check(s) degraded:"
    local f
    for f in "${FAILURES[@]}"; do
        echo "        - $f"
    done
    return 1
}

# ─── Flows ──────────────────────────────────────────────────────────────────
do_start() {
    echo -e "${BLUE}═══ Starting CCoP Local Environment ═══${NC}"
    preflight
    ensure_qdrant
    ensure_ollama
    verify_model
    ensure_collection
    echo -e "${GREEN}═══ Ready ═══${NC}"
    echo
    echo "Next: cd src && poetry run ccop-eval evaluate run --model $MODEL_NAME --test-ids B3-001"
}

do_stop() {
    echo -e "${BLUE}═══ Stopping CCoP Local Environment ═══${NC}"
    stop_ollama
    stop_qdrant
    echo -e "${GREEN}═══ Stopped ═══${NC}"
}

# ─── Arg parsing ────────────────────────────────────────────────────────────
CMD="${1:-start}"
case "$CMD" in
    start|"") do_start ;;
    --stop|stop) do_stop ;;
    --status|status)
        DEEP="false"
        if [[ "${2:-}" == "--deep" ]]; then DEEP="true"; fi
        status "$DEEP"
        exit $?
        ;;
    --help|-h|help) usage ;;
    *)
        error "Unknown argument: $CMD"
        usage
        exit 2
        ;;
esac
