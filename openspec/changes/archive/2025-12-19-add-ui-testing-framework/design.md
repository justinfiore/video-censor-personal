# Design: UI Testing Framework for CI/CD

## Context

The Video Censor project uses pytest for testing with a target coverage of 80% (per `openspec/project.md`). CustomTkinter applications present unique testing challenges because they depend on a graphical display server, which is not available in CI environments. Additionally, the project maintains GitHub Actions CI that currently runs on Windows, Linux, and macOS.

**Key Constraints**:
- Must run on all three platforms (Windows, Linux, macOS) without manual intervention
- Must integrate with existing pytest infrastructure
- Must not require expensive display server setup or licensing
- Must support testing of future UI components (video player, segment lists, dialogs)
- Must maintain low test execution time

## Goals / Non-Goals

### Goals
- Enable UI code to be tested automatically in CI without display hardware
- Establish reusable patterns for unit testing UI initialization and state
- Support future integration testing of complex UI features (video player, segments)
- Maintain existing test infrastructure and pytest conventions
- Achieve minimum 80% code coverage for UI code (consistent with project target)
- Document testing patterns for future UI developers

### Non-Goals
- Visual regression testing (screenshot comparisons) in initial phase
- End-to-end user interaction testing with mouse/keyboard simulation in initial phase
- Custom test reporting UI or advanced analytics
- Cross-browser testing (TKinter is single implementation)

## Decisions

### Decision 1: Headless Display Strategy
**What**: Use xvfb (virtual framebuffer) on Linux, native display on macOS/Windows
**Why**:
- xvfb is standard, lightweight, and free for CI environments
- macOS and Windows runners typically have display support in GitHub Actions
- Allows full Tkinter/CustomTkinter rendering without actual monitor
- Lower setup complexity than alternatives (Docker, VNC servers)

**Implementation Details**:
- Linux CI: Wrap pytest with `xvfb-run` in GitHub Actions workflow
- macOS CI: Run tests directly with native display
- Windows CI: Run tests directly with native display
- Local development: Tests run directly without special configuration

**Alternatives Considered**:
- Docker container with display server: Adds complexity, slower execution
- Screenshot-based assertions: Fragile, platform-dependent, slow to develop
- Mock all display: Reduces real-world coverage, misses integration issues
- VNC server: Overkill, licensing concerns

### Decision 2: Fixture-Based Test Architecture
**What**: Create pytest fixtures for application setup/teardown and common test patterns
**Why**:
- Isolates tests from global state and display server state
- Enables consistent test initialization across all platforms
- Supports easy cleanup and resource management
- Follows pytest conventions already used in project

**Fixture Strategy**:
```python
@pytest.fixture
def app():
    """Application instance for testing."""
    application = DesktopApp()
    yield application
    application.cleanup()  # Ensure proper cleanup

@pytest.fixture
def app_window(app):
    """Application with active window (requires display)."""
    yield app.root
    # Cleanup handled by app fixture
```

**Markers**:
- `@pytest.mark.ui` - Tests that require display (run conditionally)
- `@pytest.mark.unit` - Pure logic tests (always run)

### Decision 3: Test Organization
**What**: Create `tests/ui/` directory mirroring `video_censor_personal/ui/`
**Why**:
- Clear separation of UI tests from core analysis tests
- Maintains project test structure conventions
- Enables parallel test runs by module
- Supports selective test execution (e.g., `pytest tests/ui/`)

**Structure**:
```
tests/
├── ui/
│   ├── conftest.py              # Shared fixtures for UI tests
│   ├── test_app_bootstrap.py    # Tests for DesktopApp initialization
│   ├── test_window_lifecycle.py # Tests for window open/close
│   └── test_components/         # Future: widget-specific tests
├── conftest.py                  # Project-wide fixtures
└── ...existing tests...
```

### Decision 4: CI Workflow Configuration
**What**: Update GitHub Actions to support headless UI testing
**Why**:
- Ensures UI tests run on every commit to all platforms
- Early detection of platform-specific issues
- Integrates with existing CI infrastructure

**Changes to `.github/workflows/`**:
- Add xvfb-run wrapper for Linux test job
- Add pytest-mark filtering for display-requiring tests
- Configure failure notifications if UI tests fail
- Report coverage for UI module separately

**Workflow Pattern**:
```yaml
jobs:
  test-ui:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.13']
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install xvfb (Linux)
        if: runner.os == 'Linux'
        run: sudo apt-get install -y xvfb
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run UI tests (Linux)
        if: runner.os == 'Linux'
        run: xvfb-run -a pytest tests/ui/ -v
      - name: Run UI tests (macOS/Windows)
        if: runner.os != 'Linux'
        run: pytest tests/ui/ -v
```

### Decision 5: Test Content Strategy
**What**: Focus bootstrap phase on initialization tests; support future feature testing
**Why**:
- Validates application can start without errors
- Tests window lifecycle (open, close, cleanup)
- Confirms no resource leaks
- Foundation for testing future UI components

**Initial Test Coverage**:
- ✓ Application initialization succeeds
- ✓ Window title is correctly set
- ✓ Window can be created and destroyed without errors
- ✓ No resource leaks (file handles, memory)
- ✓ Cleanup code executes properly
- (Future) Video player component creation
- (Future) Segment list population
- (Future) Dialog interactions

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| xvfb not available in CI environment | Install explicitly via apt-get; fallback to screenshot-based detection if unavailable |
| Display server conflicts between parallel test runs | Use xvfb-run -a flag (auto-select display number); isolate tests with fixtures |
| Slow test execution in headless mode | Keep UI tests fast by mocking complex dependencies; run UI tests separately from fast unit tests |
| Platform-specific display rendering bugs | Test on all three platforms in CI; document any platform-specific quirks |
| Fixture complexity grows with UI features | Establish clear fixture patterns early; document for future developers |

## Migration Plan

### Phase 1: Bootstrap Testing (This Change)
- Add pytest fixtures for application initialization
- Create basic tests for window creation and lifecycle
- Configure xvfb on GitHub Actions Linux runner
- Validate tests run on all three platforms

### Phase 2: Future Features (with `preview-editor-ui`)
- Extend fixtures for video player component testing
- Add tests for widget state management
- Implement tests for JSON file loading/parsing
- Add tests for segment list population

### Phase 3: Future Integration (with `ui-full-workflow`)
- Add dialog interaction tests
- Test background thread handling (analysis, remediation)
- Add progress indicator verification
- Test error message display

## Open Questions

- Q: Should UI tests be run in parallel with core analysis tests, or in separate job?
  - A (TBD): Evaluate CI execution time; may want separate job for clarity
  
- Q: How should we handle future feature testing that requires complex mocking (e.g., video playback)?
  - A (TBD): Establish patterns in phase 2 when preview-editor-ui is developed
  
- Q: Should snapshot testing be introduced for future widget rendering validation?
  - A (TBD): Assess need based on UI complexity growth; defer unless visual regressions become problem
