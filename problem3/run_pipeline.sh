#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <url1> [url2] [url3] ..."
  exit 1
fi

echo "Starting Multi-Container Pipeline"
echo "================================="

docker-compose down -v >/dev/null 2>&1 || true

TEMP_DIR=$(mktemp -d)
trap "rm -rf \"$TEMP_DIR\"" EXIT

for url in "$@"; do
  echo "$url" >> "$TEMP_DIR/urls.txt"
done

echo "URLs to process:"
cat "$TEMP_DIR/urls.txt"
echo ""

echo "Building containers..."
docker-compose build --quiet
echo "Starting pipeline..."
docker-compose up -d

sleep 3

docker exec pipeline-fetcher sh -lc 'mkdir -p /shared/input'
docker cp "$TEMP_DIR/urls.txt" pipeline-fetcher:/shared/input/urls.txt

echo "Processing..."
MAX_WAIT=300
ELAPSED=0

is_exited() {
  local name="$1"
  local st
  st=$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || echo "unknown")
  [ "$st" = "exited" ] || [ "$st" = "dead" ] || [ "$st" = "removing" ]
}

while [ $ELAPSED -lt $MAX_WAIT ]; do
  if docker run --rm -v pipeline-shared-data:/shared alpine sh -lc 'test -f /shared/analysis/final_report.json'; then
    echo "Pipeline complete"
    break
  fi

  if is_exited pipeline-analyzer; then
    echo "ERROR: analyzer exited"
    docker-compose logs analyzer
    exit 1
  fi
  if is_exited pipeline-processor; then
    echo "ERROR: processor exited"
    docker-compose logs processor
    exit 1
  fi

  sleep 5
  ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo "Pipeline timeout"
  docker-compose logs
  docker-compose down
  exit 1
fi

mkdir -p output status
docker cp pipeline-analyzer:/shared/analysis/final_report.json output/final_report.json || true
docker cp pipeline-analyzer:/shared/status/. status/ || true

docker-compose down

python3 - <<'PY'
import json,sys
with open('output/final_report.json') as f:
    data=json.load(f)
n=data.get("documents_processed",0)
if n<=0:
    print("ERROR: documents_processed=0", file=sys.stderr)
    sys.exit(2)
print(f"OK: documents_processed={n}")
PY
