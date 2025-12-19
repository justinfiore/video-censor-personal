# Change: Add UI Testing Framework for CI/CD Integration

## Why

The `add-desktop-ui-bootstrap` change introduces a new CustomTkinter-based desktop UI. To ensure reliability and enable continuous integration, an automated testing framework is needed that can run in headless CI environments (GitHub Actions, etc.) without requiring a display server. Testing CustomTkinter applications requires a specialized approach due to their graphical nature, making it essential to establish testing patterns early.

## What Changes

- **NEW** Create a UI testing framework using pytest with headless display emulation for CI
- **NEW** Define a `ui-testing` capability with requirements for test infrastructure and patterns
- **NEW** Add test dependencies (pytest-mock, pyvirtualdisplay for Linux headless testing) to requirements.txt
- **NEW** Create test fixtures and utilities for UI initialization and component testing
- **NEW** Configure GitHub Actions CI to run UI tests on Windows, Linux, and macOS
- **NEW** Establish testing patterns for application initialization, window lifecycle, and future widget testing

## Impact

- **Affected specs**: New `ui-testing` capability (non-breaking addition); updates to `ci-cd` capability
- **Affected code**: 
  - `requirements.txt` - Add test dependencies (pytest-mock, pyvirtualdisplay)
  - `pytest.ini` - Configure UI test discovery and markers
  - `.github/workflows/` - Update CI configuration to run UI tests with headless display on Linux
  - `tests/ui/` - New test directory with fixtures and test files
  - `video_censor_personal/ui/main.py` - Add testable initialization patterns (dependency injection)

## Design Rationale

**Testing Strategy**:
- **Unit tests** of UI logic (initialization, state management) without display rendering
- **Integration tests** of window lifecycle with virtual display on Linux (xvfb)
- **Mocking** of Tkinter/CustomTkinter display components where possible to avoid display server dependency
- **Fixture-based** test setup to enable consistent, isolated test environments

**CI Approach**:
- Use xvfb-run wrapper on Linux for headless rendering
- Native display support on macOS and Windows (no special setup needed)
- Pytest markers to distinguish headless vs. display-requiring tests
- Coverage reporting for UI code

**Tool Selection**:
- pytest: Existing project test framework, familiar patterns
- pytest-mock: Mock external dependencies
- pyvirtualdisplay: Python wrapper for xvfb on Linux
- GitHub Actions: Existing CI/CD infrastructure
