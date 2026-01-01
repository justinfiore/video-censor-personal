# Headless/Headed Mode Feature Added to Integration Test Proposal

## Overview

The integration testing proposal has been enhanced with support for **headless** and **headed** test execution modes. This enables:
- **Headless (default)**: Fast automated testing in CI/CD with no display required
- **Headed (debugging)**: Visual observation of test execution for rapid failure diagnosis

## What Was Added

### 1. New Requirement in spec (ui-testing/spec.md)

**"Integration tests for the Preview Editor UI SHALL support both headless and headed execution modes"**

Covers 5 scenarios:
- Tests run headless by default (no display needed)
- Tests run in headed mode via `PYTEST_HEADED=1` environment variable
- Tests run in headed mode via `pytest --headed` CLI flag
- Headed mode aids visual debugging (real-time observation, pausing, window interaction)
- Headless mode compatible with CI/CD (no xvfb setup needed)

### 2. Design Section (design.md)

New **Decision 4: Headless/Headed Execution Modes**

```
Headless (Default):        pytest tests/ui/
- No display required
- Tests run in CI/CD
- Fixtures hide windows or off-screen rendering
- ~5-10ms per test

Headed (Debug):            PYTEST_HEADED=1 pytest tests/ui/ --headed
- Display windows visible
- 500ms pauses between actions
- Window titles show test name
- Developer can interact with windows
```

Implementation approach:
- `conftest.py`: Check `PYTEST_HEADED` env var + `--headed` CLI flag
- `app_window` fixture respects mode (hidden vs visible, with/without delays)
- CI config: No special setup (defaults to headless)

### 3. Tasks (tasks.md)

New **Task 1.1: Implement headless/headed mode support** with 7 subtasks:

```
1.1a Check PYTEST_HEADED environment variable
1.1b Add --headed pytest CLI flag via pytest_addoption
1.1c Create headed_mode fixture returning bool
1.1d Modify app and app_window fixtures to respect headed mode
1.1e In headless mode: hide windows or use off-screen rendering
1.1f In headed mode: add 500ms delays between actions for visibility
1.1g Update window title to include test name in headed mode
```

Effort: ~1 hour (part of Phase 1 which is now 3-4 hours total)

### 4. Usage Examples (SUMMARY.md)

**Headless (CI/Automated):**
```bash
pytest tests/ui/test_integration.py -v
pytest tests/ui/ --cov=video_censor_personal.ui
```

**Headed (Developer Debugging):**
```bash
PYTEST_HEADED=1 pytest tests/ui/test_integration.py -v
PYTEST_HEADED=1 pytest tests/ui/test_integration.py::test_segment_selection_updates_details -v --pdb
pytest tests/ui/test_integration.py --headed -v
```

**Benefits for Debugging:**
```
Without headed mode:
  - Read assertion message
  - Add print statements
  - Rerun test
  - Repeat until found

With headed mode:
  - Window displays in real time
  - Developer sees actual UI state
  - Can pause with debugger and inspect
  - Diagnoses issue in minutes (not iterations)
```

## Files Modified

1. **openspec/changes/expand-preview-editor-integration-tests/specs/ui-testing/spec.md**
   - Added 5 new scenarios for headless/headed requirement

2. **openspec/changes/expand-preview-editor-integration-tests/design.md**
   - Added Decision 4: Headless/Headed Execution Modes
   - Includes implementation strategy and rationale

3. **openspec/changes/expand-preview-editor-integration-tests/tasks.md**
   - Expanded Phase 1 Task 1.1 with 7 subtasks for implementation
   - Renumbered subsequent fixtures to 1.2-1.6

4. **openspec/changes/expand-preview-editor-integration-tests/SUMMARY.md**
   - Added "Test Execution Examples" section with command examples
   - Updated benefits list (added debugging and CI/CD support)
   - Updated effort estimate (Phase 1: 3-4 hours, total: 15-22 hours)

## Implementation Highlights

### How It Works

**Headless Mode (Default - No Code Change Needed):**
```python
# In conftest.py
@pytest.fixture
def app():
    app = DesktopApp()
    if not is_headed_mode():
        app.root.withdraw()  # Hide window
    yield app
```

**Headed Mode (Developer-Activated):**
```bash
# Environment variable
PYTEST_HEADED=1 pytest tests/ui/test_integration.py -v

# Or CLI flag
pytest tests/ui/test_integration.py --headed -v

# In conftest.py
@pytest.fixture
def headed_mode():
    headed = os.environ.get('PYTEST_HEADED') == '1'
    headed = headed or pytest.config.getoption('--headed', default=False)
    return headed

@pytest.fixture
def app_window(headed_mode):
    app = PreviewEditorApp()
    if headed_mode:
        app.root.deiconify()  # Show window
        time.sleep(0.5)  # Pause for visibility
    yield app.root
```

### Test Names in Window Titles

In headed mode, window titles help identify which test is running:
```
"Test: test_file_io_open_json - Video Censor Personal - Preview Editor"
"Test: test_segment_selection_updates_details - Video Censor Personal - Preview Editor"
```

## Benefits Summary

| Aspect | Headless | Headed |
|--------|----------|--------|
| **Speed** | ~5-10ms per test | ~500-1000ms per test |
| **CI/CD** | ✅ No setup needed | ❌ Not for CI |
| **Display** | ❌ Not visible | ✅ Visible in real-time |
| **Debugging** | ⚠️ Read logs | ✅ Watch it happen |
| **Interaction** | ❌ Automated only | ✅ Can pause & inspect |
| **Use Case** | Automated testing, coverage, validation | Developer debugging, failure diagnosis |

## Approval Gate

This addition to the proposal **does not change the approval decision**, but adds:
- More robust testing infrastructure
- Better debugging capabilities for developers
- Faster failure diagnosis (critical for test maintenance)

The proposal remains ready for approval with 3 blocking questions.
