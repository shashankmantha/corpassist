#!/usr/bin/env bash
#
# Rebuild the CorpAssist image and restart — run after `git pull` or any code change.
# The model cache, chat history (data/) and vector store (chroma/) are preserved.
#
#   ./rebuild.sh              real lab
#   ./rebuild.sh standalone   dev/off-lab (self-contained MySQL)
#
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }

MODE="${1:-real}"
if [ "$MODE" = "standalone" ]; then
  FILES=(-f docker-compose.yml -f docker-compose.standalone.yml)
else
  FILES=(-f docker-compose.yml)
fi

echo "Rebuilding CorpAssist image (${MODE} mode)..."
docker compose "${FILES[@]}" up -d --build

echo
echo "Rebuilt and restarted."
echo "  UI:    http://localhost:8501"
echo "  Logs:  docker compose ${FILES[*]} logs -f app"
