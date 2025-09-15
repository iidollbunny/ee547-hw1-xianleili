#!/bin/bash
set -e

echo "Test 1: Single URL"
./run_pipeline.sh https://www.example.com

echo ""
echo "Test 2: Multiple URLs from file"
./run_pipeline.sh $(cat test_urls.txt)

echo ""
echo "Test 3: Verify output structure"
python3 - <<'PY'
import json, sys
with open('output/final_report.json') as f:
    data = json.load(f)
for key in ('documents_processed','top_100_words','document_similarity'):
    assert key in data, f"missing key: {key}"
print("Output validation passed")
PY
