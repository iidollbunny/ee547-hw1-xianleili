#!/bin/bash
# Run a set of test queries for validation
set -euo pipefail

# Test 1: Machine Learning category
./run.sh "cat:cs.LG" 5 output_ml/

# Test 2: Specific author
./run.sh "au:LeCun" 3 output_author/

# Test 3: Keyword in title
./run.sh "ti:transformer" 10 output_title/

# Test 4: Complex query with date filter
./run.sh "cat:cs.LG AND ti:transformer AND submittedDate:[2020 TO 2025]" 5 output_complex/

echo "Test completed. Check output directories for results."
