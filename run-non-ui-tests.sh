#!/bin/bash
# Run all tests EXCEPT UI tests for video-censor-personal

set -e

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run pytest excluding tests/ui directory
python -m pytest tests/ --ignore=tests/ui -v

# Exit code from pytest is automatically propagated
exit $?
