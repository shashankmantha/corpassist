#!/usr/bin/env bash
# CorpAssist smoke test — infra checks from the host, then functional checks
# inside the app container. Run from the repo root with the stack up:
#   docker compose up -d --build     # (or without -d in another terminal)
#   bash smoke_test.sh
set -uo pipefail

APP=corpassist-app
OLLAMA=corpassist-ollama
UI_PORT=8501
fail=0

pass() { echo "[PASS] $1"; }
bad()  { echo "[FAIL] $1"; fail=1; }

echo "== infra =="

# 1. containers up
if docker ps --format '{{.Names}}' | grep -q "^${APP}$"; then pass "app container running"; else bad "app container not running"; fi
if docker ps --format '{{.Names}}' | grep -q "^${OLLAMA}$"; then pass "ollama container running"; else bad "ollama container not running"; fi

# 2. Streamlit health endpoint
if curl -sf "http://localhost:${UI_PORT}/_stcore/health" >/dev/null 2>&1; then
  pass "Streamlit healthy on :${UI_PORT}"
else
  bad "Streamlit not answering on :${UI_PORT}"
fi

# 3. Ollama lists a model
if docker exec "${OLLAMA}" ollama list 2>/dev/null | tail -n +2 | grep -q .; then
  pass "Ollama has at least one model"
else
  bad "Ollama lists no models (first-run pull may be in progress)"
fi

echo
echo "== functional (inside the app container) =="
if docker exec -e SMOKE_POISON="${SMOKE_POISON:-0}" -i "${APP}" python smoke_test.py; then
  pass "functional suite passed"
else
  bad "functional suite reported failures"
fi

echo
if [ "${fail}" -eq 0 ]; then
  echo "SMOKE TEST: all green."
else
  echo "SMOKE TEST: failures above — see the integration guide's troubleshooting table."
fi
exit "${fail}"
