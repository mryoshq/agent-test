#!/usr/bin/env bash
# The checks CI runs, in one place. Agents and the lead run the same commands.
#
# Usage: bash .github/scripts/check.sh <step> [options]
#   lint        ruff check + ruff format --check
#   types       mypy
#   test        unit tests (not acceptance, not e2e) with coverage, then the coverage floor
#   security    bandit on app code + pip-audit on requirements.txt
#   e2e         start uvicorn, run tests/e2e over real HTTP
#   acceptance  [goal] [-k EXPR] [--junit FILE]
#               start uvicorn, run tests/acceptance (or tests/acceptance/<goal>)
#   all         lint, types, test, security, e2e (acceptance is separate: it fails until a goal is built)
#
# Run it from the repository root. PY is a python with requirements-dev.txt installed
# (default: python), for example PY=/tmp/venv/bin/python.
# The e2e and acceptance server listens on a free port the OS picks (bind to port 0).
# The PORT environment variable is ignored: agent sandboxes set PORT for their own server.
set -euo pipefail

PY="${PY:-python}"
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_PID=""

stop_server() { [[ -n "$SERVER_PID" ]] && kill "$SERVER_PID" 2>/dev/null || true; SERVER_PID=""; }
trap stop_server EXIT

# Print a port that is free right now: the OS picks it when binding to port 0.
free_port() {
  "$PY" -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()'
}

# Start uvicorn on a free port and export E2E_BASE_URL. Another process can take the port between
# free_port and uvicorn's bind, so a server that exits early is retried on a new port.
start_server() {
  local attempt port log
  for attempt in 1 2 3; do
    port="$(free_port)"
    log="${TMPDIR:-/tmp}/check-server-$port.log"
    "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$port" --log-level warning >"$log" 2>&1 &
    SERVER_PID=$!
    for _ in $(seq 1 100); do
      kill -0 "$SERVER_PID" 2>/dev/null || break
      if "$PY" -c "import httpx, sys; sys.exit(httpx.get('http://127.0.0.1:$port/health', timeout=1).status_code != 200)" 2>/dev/null; then
        export E2E_BASE_URL="http://127.0.0.1:$port"
        return 0
      fi
      sleep 0.2
    done
    echo "server did not start on port $port (attempt $attempt of 3):" >&2
    cat "$log" >&2
    stop_server
  done
  return 1
}

lint()     { "$PY" -m ruff check . && "$PY" -m ruff format --check .; }
types()    { "$PY" -m mypy .; }
unit()     {
  "$PY" -m pytest -q -p no:cacheprovider --ignore=tests/acceptance --ignore=tests/e2e \
    --cov --cov-report=term-missing --cov-report=json:coverage.json \
    && "$PY" "$SCRIPTS/coverage_gate.py" coverage.json quality/coverage-baseline.json
}
security() { "$PY" -m bandit -q -c pyproject.toml -r . -x ./.github,./tests,./mutants,./.venv,./test_*.py && "$PY" -m pip_audit -r requirements.txt; }
e2e()      {
  start_server || return 1
  local rc=0
  "$PY" -m pytest -q -p no:cacheprovider tests/e2e || rc=$?
  stop_server
  return "$rc"
}

acceptance() {
  local target="tests/acceptance" kexpr="" junit=""
  while (($#)); do
    case "$1" in
      -k) kexpr="$2"; shift 2 ;;
      --junit) junit="$2"; shift 2 ;;
      *) target="tests/acceptance/$1"; shift ;;
    esac
  done
  if [[ ! -d "$target" ]] || ! find "$target" -name 'test_*.py' | grep -q .; then
    echo "no acceptance tests in $target"
    [[ -n "$junit" ]] && printf '<?xml version="1.0"?>\n<testsuites></testsuites>\n' >"$junit"
    return 0
  fi
  start_server || return 1
  local args=(-q -p no:cacheprovider "$target")
  [[ -n "$kexpr" ]] && args+=(-k "$kexpr")
  [[ -n "$junit" ]] && args+=("--junitxml=$junit")
  local rc=0
  "$PY" -m pytest "${args[@]}" || rc=$?
  stop_server
  return "$rc"
}

step="${1:-}"; shift || true
case "$step" in
  lint) lint ;;
  types) types ;;
  test) unit ;;
  security) security ;;
  e2e) e2e ;;
  acceptance) acceptance "$@" ;;
  all)
    failed=()
    for s in lint types unit security e2e; do
      echo "== $s"
      if "$s"; then echo "== $s: PASS"; else echo "== $s: FAIL"; failed+=("$s"); fi
    done
    if ((${#failed[@]})); then echo "FAILED: ${failed[*]}"; exit 1; fi
    echo "ALL PASS"
    ;;
  *) echo "usage: $0 lint|types|test|security|e2e|acceptance [goal] [-k EXPR] [--junit FILE]|all" >&2; exit 2 ;;
esac
