#!/bin/bash
# Run all tests for video-censor-personal

set -e

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run pytest with verbose output
python -m pytest tests/ -v

# Exit code from pytest is automatically propagated
exit $?
