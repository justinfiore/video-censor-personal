# Testing Instructions

When testing locally, do NOT run all of the UI tests, as they will take too long.
Instead, use one of the testing scripts below based on your needs.

## Testing Scripts

### Run All Tests
```bash
./run-all-tests.sh
```
Runs all tests in the `tests/` directory including UI tests. Don't use this, only CI or humans should use this.

### Run Non-UI Tests (Recommended)
```bash
./run-non-ui-tests.sh
```
Runs all tests EXCEPT those in `tests/ui`. Use this during development for fast iteration.

### Run UI Tests Only
```bash
./run-ui-tests.sh
```
Runs only tests in `tests/ui`. Don't use this, only CI or humans should use this.

### Run Specific Tests
```bash
# Run all tests in a file
./run-specific-tests.sh "tests/test_module.py"

# Run all tests in a class
./run-specific-tests.sh "tests/test_module.py::TestClass"

# Run a specific test method
./run-specific-tests.sh "tests/test_module.py::TestClass::test_method"

# Run tests matching a pattern
./run-specific-tests.sh "test_function_name"

# Run with additional pytest flags
./run-specific-tests.sh "tests/test_module.py" -v --tb=short
```
Use this for targeted testing during development or debugging.

## Recommended Workflow

1. **During development**: Run specific test file with `./run-specific-tests.sh "tests/test_module.py"`
2. **Before commit**: Run specific test file with `./run-specific-tests.sh "tests/test_module.py"`
3. **When debugging UI**: Use `./run-specific-tests.sh "tests/ui/test_file.py"`

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->