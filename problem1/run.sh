#!/bin/bash
# Problem 1 - Part C: Run Docker container
set -euo pipefail

# Check arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <input_file> <output_directory>"
  exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="$2"

# Verify input file exists
if [ ! -f "$INPUT_FILE" ]; then
  echo "Error: Input file $INPUT_FILE does not exist"
  exit 1
fi

# Ensure output dir exists
mkdir -p "$OUTPUT_DIR"

# realpath required by guide (macOS: brew install coreutils)
if ! command -v realpath >/dev/null 2>&1; then
  echo "Error: realpath not found. On macOS: brew install coreutils"
  exit 1
fi

INPUT_ABS="$(realpath "$INPUT_FILE")"
OUTPUT_ABS="$(realpath "$OUTPUT_DIR")"

# Run container with mounted input/output
docker run --rm \
  --name http-fetcher \
  -v "${INPUT_ABS}":/data/input/urls.txt:ro \
  -v "${OUTPUT_ABS}":/data/output \
  http-fetcher:latest
