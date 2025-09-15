#!/bin/bash
# Usage: ./run.sh "<query>" <max_results> <output_dir>
set -euo pipefail

if [ $# -ne 3 ]; then
  echo "Usage: $0 <query> <max_results> <output_dir>"
  exit 1
fi

QUERY="$1"
MAX_RESULTS="$2"
OUTPUT_DIR="$3"

# Validate that max_results is an integer between 1 and 100
if ! [[ "$MAX_RESULTS" =~ ^[0-9]+$ ]]; then
  echo "Error: max_results must be an integer"
  exit 1
fi
if [ "$MAX_RESULTS" -lt 1 ] || [ "$MAX_RESULTS" -gt 100 ]; then
  echo "Error: max_results must be between 1 and 100"
  exit 1
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Resolve OUTPUT_DIR to an absolute, physical path in pure bash
# This avoids relying on host 'python' or 'python3'
OLDPWD="$(pwd)"
cd "$OUTPUT_DIR"
HOST_OUT="$(pwd -P)"
cd "$OLDPWD"

# Run container with mounted output directory
docker run --rm \
  --name arxiv-processor \
  -v "${HOST_OUT}":/data/output \
  arxiv-processor:latest \
  "$QUERY" "$MAX_RESULTS" "/data/output"
