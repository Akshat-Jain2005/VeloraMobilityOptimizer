#!/bin/bash
set -e
echo "Running full validation pipeline..."
./build.sh
python3 scripts/test_runner.py
echo "Pipeline complete."
