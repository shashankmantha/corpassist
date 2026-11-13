#!/usr/bin/env bash
#
# Start CorpAssist (uses the already-built image; run ./rebuild.sh after code changes).
#
#   ./corp-assist.sh              real lab  — connects to the db-net MySQL VM (DB_HOST in .env)
#   ./corp-assist.sh standalone   dev/off-lab — self-contained throwaway MySQL
#   ./corp-assist.sh stop         stop the running stack
#
set -euo pipefail
cd "$(dirname "$0")"

# first run: seed .env from the example
[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }

MODE="${1:-real}"
if [ "$MODE" = "standalone" ]; then
  FILES=(-f docker-compose.yml -f docker-compose.standalone.yml)
else
  FILES=(-f docker-compose.yml)
fi

if [ "$MODE" = "stop" ]; then
  docker compose -f docker-compose.yml -f docker-compose.standalone.yml down 2>/dev/null || true
  docker compose -f docker-compose.yml down
  echo "CorpAssist stopped."
  exit 0
fi

docker compose "${FILES[@]}" up -d

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo
echo "CorpAssist is starting (${MODE} mode)."
echo "  UI:        http://localhost:8501${IP:+   or   http://$IP:8501}"
echo "  Accounts:  hradmin / admin123   ·   employee / employee123"
echo "  Logs:      docker compose ${FILES[*]} logs -f app"
echo
echo "First run pulls the model (~4.7 GB); the UI is up once the logs show"
echo "'starting Streamlit on :8501'."
