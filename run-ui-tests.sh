#!/bin/bash
# Run only UI tests for video-censor-personal

set -e

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run pytest for tests/ui directory only
python -m pytest tests/ui -v

# Exit code from pytest is automatically propagated
exit $?
