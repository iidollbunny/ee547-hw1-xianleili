#!/bin/bash
# Problem 1 - Part C: Build Docker image
set -euo pipefail
docker build -t http-fetcher:latest .
