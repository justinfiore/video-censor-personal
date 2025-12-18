# Implementation Tasks: add-ui-testing-framework

## 1. Dependency and Configuration Setup
- [ ] 1.1 Add pytest-mock to requirements.txt (for mocking external dependencies)
- [ ] 1.2 Add pyvirtualdisplay to requirements.txt (for Linux headless testing)
- [ ] 1.3 Update pytest.ini with ui test markers and configuration
- [ ] 1.4 Verify pytest and coverage versions are compatible with new dependencies

## 2. Test Fixtures and Utilities
- [ ] 2.1 Create `tests/ui/conftest.py` with shared fixtures
- [ ] 2.2 Implement `app` fixture for application instance creation/cleanup
- [ ] 2.3 Implement `app_window` fixture for window-based testing
- [ ] 2.4 Create fixture for checking resource cleanup (file handles, memory)
- [ ] 2.5 Document fixture usage in conftest.py docstrings

## 3. Bootstrap Tests
- [ ] 3.1 Create `tests/ui/test_app_bootstrap.py`
- [ ] 3.2 Implement test: Application initializes without errors
- [ ] 3.3 Implement test: Window title is set to "Video Censor Personal"
- [ ] 3.4 Implement test: Window is created successfully on first initialization
- [ ] 3.5 Implement test: No module import errors when initializing UI

## 4. Window Lifecycle Tests
- [ ] 4.1 Create `tests/ui/test_window_lifecycle.py`
- [ ] 4.2 Implement test: Window can be opened and closed without errors
- [ ] 4.3 Implement test: Cleanup code executes on window close
- [ ] 4.4 Implement test: No resource leaks (file handles) after window close
- [ ] 4.5 Implement test: Multiple window create/destroy cycles succeed

## 5. Headless Display Support
- [ ] 5.1 Create test utility function to detect display availability
- [ ] 5.2 Implement pyvirtualdisplay integration for non-display environments
- [ ] 5.3 Create pytest marker for display-requiring tests (`@pytest.mark.ui`)
- [ ] 5.4 Create pytest marker for logic-only tests (`@pytest.mark.unit`)
- [ ] 5.5 Test fixture behavior in both display and headless modes locally

## 6. GitHub Actions CI Integration
- [ ] 6.1 Create/update `.github/workflows/test-ui.yml` workflow file
- [ ] 6.2 Configure matrix strategy for [ubuntu-latest, macos-latest, windows-latest]
- [ ] 6.3 Add xvfb installation step for Linux runner
- [ ] 6.4 Add xvfb-run wrapper for Linux test execution
- [ ] 6.5 Configure native display execution for macOS and Windows
- [ ] 6.6 Add coverage reporting step in workflow
- [ ] 6.7 Test workflow manually on all platforms (dry-run or actual)

## 7. Test Execution and Validation
- [ ] 7.1 Run UI tests locally on macOS with display
- [ ] 7.2 Run UI tests on Linux container/VM with xvfb (if available)
- [ ] 7.3 Verify test execution in GitHub Actions for all platforms
- [ ] 7.4 Verify coverage is reported correctly (minimum 80% for UI code)
- [ ] 7.5 Verify tests fail appropriately when code has bugs (inject test bug, verify failure)

## 8. Documentation and Integration
- [ ] 8.1 Document how to run UI tests locally: `pytest tests/ui/`
- [ ] 8.2 Document headless display behavior in CONTRIBUTING.md or testing guide
- [ ] 8.3 Add comments to conftest.py explaining fixture setup/teardown
- [ ] 8.4 Document pytest markers usage for future test writers
- [ ] 8.5 Update README.md with testing section if necessary
- [ ] 8.6 Verify existing tests still pass (no breakage of core test infrastructure)

## 9. Code Review and Quality
- [ ] 9.1 Verify all test files follow PEP 8 and project style guidelines
- [ ] 9.2 Verify test functions have clear names (test_X_when_Y_then_Z pattern)
- [ ] 9.3 Verify no hardcoded paths or platform-specific code without proper guards
- [ ] 9.4 Ensure test isolation (no shared state between tests)
- [ ] 9.5 Check for proper error handling and cleanup in all fixtures
