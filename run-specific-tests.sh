#!/bin/bash
# Run specific tests by file, class, or test name for video-censor-personal
#
# Usage:
#   ./run-specific-tests.sh "tests/test_module.py"                    # Run all tests in file
#   ./run-specific-tests.sh "tests/test_module.py::TestClass"         # Run all tests in class
#   ./run-specific-tests.sh "tests/test_module.py::TestClass::test_method"  # Run specific test
#   ./run-specific-tests.sh "test_function_name"                      # Run tests matching name pattern
#   ./run-specific-tests.sh "tests/test_module.py::TestClass" -v      # Run with additional pytest flags

set -e

# Check if test pattern provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <test_path_or_pattern> [pytest_options]"
    echo ""
    echo "Examples:"
    echo "  $0 'tests/test_module.py'                           # Run all tests in file"
    echo "  $0 'tests/test_module.py::TestClass'                # Run all tests in class"
    echo "  $0 'tests/test_module.py::TestClass::test_method'   # Run specific test"
    echo "  $0 'test_function_name'                             # Run tests matching name pattern"
    echo "  $0 'tests/test_module.py' -v                        # Run with additional flags"
    exit 1
fi

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get test pattern (first argument)
TEST_PATTERN="$1"
shift

# Run pytest with the specified pattern and any additional arguments
python -m pytest "$TEST_PATTERN" -v "$@"

# Exit code from pytest is automatically propagated
exit $?
