#!/usr/bin/env bash
# CorpAssist app container entrypoint:
#   1. wait for the Ollama service
#   2. ensure the model is present (first run downloads it; needs internet once)
#   3. (re)build the RAG index from docs/
#   4. launch the Streamlit UI
set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434}"

echo "[entrypoint] waiting for Ollama at ${OLLAMA_HOST} ..."
until curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; do
  sleep 2
done
echo "[entrypoint] Ollama is up."

echo "[entrypoint] ensuring model is present (first run downloads ~4.7 GB) ..."
python - <<'PY'
import ollama, config
c = ollama.Client(host=config.OLLAMA_HOST)
try:
    c.pull(config.MODEL)          # idempotent; fast if already cached
    print(f"[entrypoint] model ready: {config.MODEL}")
except Exception as e:
    print(f"[entrypoint] WARNING: could not pull {config.MODEL}: {e}")
PY

echo "[entrypoint] building RAG index ..."
python ingest.py || echo "[entrypoint] WARNING: ingest failed (continuing)"

echo "[entrypoint] starting Streamlit on :8501 ..."
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0
