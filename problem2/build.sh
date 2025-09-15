#!/bin/bash
# Build Docker image for the ArXiv processor
set -euo pipefail

docker build -t arxiv-processor:latest "$(dirname "$0")"
echo "Build completed: arxiv-processor:latest"
