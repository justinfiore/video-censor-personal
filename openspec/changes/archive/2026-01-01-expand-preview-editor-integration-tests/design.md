# Integration Testing Design

## Context

The Preview Editor UI implementation (`add-preview-editor-ui`) achieved 98 unit tests covering individual component behavior in isolation. However, the 7 existing integration tests focus narrowly on the `SegmentManager` class (file I/O and state mutations) without exercising the full UI application.

Integration testing requires:
1. **Multi-component workflows** (user interactions across segment list → details → video player)
2. **File I/O under realistic conditions** (missing files, external modifications, JSON schema variations)
3. **Error paths** (graceful degradation, helpful error messages, recovery options)
4. **State consistency** (all UI panes remain in sync after operations)
5. **Resource management** (cleanup, no leaks, proper lifecycle)

## Goals

- Achieve >= 80% code coverage for `video_censor_personal.ui` module (current: unknown, likely < 60%)
- Document testable workflows for future UI features (part of `ui-full-workflow` change)
- Validate that user-facing error scenarios are handled with helpful feedback
- Ensure data safety (no JSON corruption, atomic updates, recovery options)
- Create test patterns/fixtures for rapid integration test development

## Non-Goals

- Performance testing (load, stress tests)
- Visual/rendering regression tests (covered by unit tests of component layout)
- Multi-process/concurrent app instances
- Real VLC integration testing (VLC mocked; video playback tested separately in unit tests)

## Decisions

### 1. Test Organization: Feature-Based Grouping
```
test_integration.py (expanded)
├── File I/O Tests (10 tests)
├── Cross-Component Sync Tests (8 tests)
├── State Consistency Tests (8 tests)
├── Error Recovery Tests (6 tests)
└── Window Lifecycle Tests (4 tests)
```

**Why**: Mirrors user workflows (open file → interact with UI → close app). Easier to read and extend.

Alternatives considered:
- By component (SegmentListPane, SegmentDetailsPane, etc.) - Too granular; misses interactions
- By operation (toggle, save, navigate) - Too scattered; hard to understand test purpose
- Flat list - Becomes unmanageable at 36 tests

### 2. Fixtures Strategy: Layered Composition
- **Layer 1 (Atomic)**: `sample_video_file`, `sample_json_payloads`, `temp_workspace`
- **Layer 2 (Composite)**: `app_with_files` = app fixture + video + JSON loaded
- **Layer 3 (Scenario)**: `app_with_large_segments`, `app_with_invalid_json`, etc.

**Why**: 
- Atomic fixtures are reusable across test categories
- Composite fixtures reduce boilerplate in tests
- Scenario fixtures map to user stories

**Risk mitigation**:
- Fixture cleanup must be explicit (temp files, mock video)
- Use `tmpdir_factory` for video file (stable across function scope)
- Auto-cleanup via pytest's `tmp_path` fixture

### 3. Mock Strategy: Minimal Mocking
- **Real implementations**: File I/O (JSON read/write), Tkinter widget hierarchy, SegmentManager
- **Justification**: Integration tests should exercise real code paths; mocking defeats the purpose

### 4. Headless/Headed Execution Modes
```
Default (Headless):        pytest tests/ui/
- No display required
- Tests run in CI/CD
- Fixtures hide windows or render off-screen
- ~5-10ms per test

Debugging (Headed):        PYTEST_HEADED=1 pytest tests/ui/ --headed
- Display windows visible
- Slow execution (500ms pauses between actions)
- Window titles identify test name
- Developer can interact with windows
```

**Implementation**:
- conftest.py: Check `os.environ.get('PYTEST_HEADED')` or pytest config for `--headed` flag
- Fixture `app_window` respects mode: 
  - Headless: Create hidden window or use off-screen rendering
  - Headed: Create visible window, add delays between actions for observation
- Each test can optionally override mode via fixture parameter
- CI configuration: No special setup needed (defaults to headless)

**Why Two Modes**:
- **Headless for CI**: Fast, deterministic, no display dependency
- **Headed for debugging**: Visual feedback helps quickly identify state issues (layout, timing, sync problems)

### 5. Error Scenarios: User-Centric
Test errors from user perspective:
- "I clicked Open but video file not found" → Test: browse dialog shown, recovery works
- "I toggled allow but got error" → Test: error message displayed, state reverts
- "I edited JSON externally" → Test: warning shown, safe to overwrite option

### 6. State Assertion: Multi-Level
```python
# Level 1: File state (JSON on disk)
assert json_data['segments'][0]['allow'] == True

# Level 2: UI state (in-memory segment)
assert app.segment_manager.segments[0].allow == True

# Level 3: Widget state (visible in UI)
assert "✓" in segment_list_widget.get_text()

# Level 4: Cross-component (all three in sync)
assert_consistent_state(json_data, manager, ui_widgets)
```

**Why**: Catches different failure modes (save failures, UI update failures, sync issues)

## Testing Patterns

### Pattern 1: File I/O Workflow
```python
# Arrange: Create temp files
json_file = create_temp_json(payload)
video_file = create_temp_video()

# Act: Open files in UI
app.open_json(json_file)

# Assert: Verify state at all levels
assert_state_consistent(app, json_file)
```

### Pattern 2: Multi-Pane Interaction
```python
# Arrange: App with loaded files
app_with_files.segment_list.click_segment(0)

# Act: Toggle allow in details pane
app_with_files.segment_details.toggle_allow()

# Assert: Verify all panes updated
assert app_with_files.segment_list.get_marker(0) == "✓"  # Marker updated
assert json_at_path(json_file)['segments'][0]['allow'] == True  # Persisted
```

### Pattern 3: Error Recovery
```python
# Arrange: Setup error condition
json_file_missing_video = create_temp_json(no_video_path)

# Act: Attempt to load
app.open_json(json_file_missing_video)

# Assert: Error handled gracefully
assert browse_dialog_shown
assert can_enter_review_only_mode
assert json_remains_loadable
```

## Fixtures to Create

### conftest.py Additions

```python
@pytest.fixture
def sample_video_file(tmp_path):
    """Create minimal MP4 file (3s, h264 codec)."""
    # Use ffmpeg to create test video
    
@pytest.fixture
def sample_json_payloads():
    """Pre-built JSON structures for different scenarios."""
    return {
        'valid_full': {...},
        'valid_no_allow_field': {...},
        'valid_no_video_path': {...},
        'invalid_missing_segments': {...},
        'invalid_bad_schema': {...},
        'edge_case_100_segments': {...},
    }
    
@pytest.fixture
def temp_workspace(tmp_path, sample_video_file):
    """Isolated directory with video + JSON files."""
    
@pytest.fixture
def app_with_files(app, sample_json_payloads, sample_video_file):
    """PreviewEditorApp with video and JSON pre-loaded."""
```

## Validation Criteria

All 36 new tests must:
1. **Pass on macOS, Linux, Windows**
2. **Complete in < 30s total** (5-10ms per test)
3. **Leave no temp files** (cleanup verified)
4. **Exercise real code paths** (no mocking of app logic)
5. **Have clear assertion messages** (failures are actionable)

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| Temp files leak on test failures | Use pytest's `tmp_path` fixture, explicit cleanup verification |
| Flaky tests (timing-dependent) | Avoid `time.sleep()`; use explicit waits (widget updates polled) |
| macOS/Windows-only paths | Skip file path tests on platforms; use `os.path` abstractions |

## Future Extensions

This design enables:
- **Full workflow testing** (analysis → review → remediation, when `ui-full-workflow` is built)
- **Performance testing** (100+, 1000+ segment scenarios)
- **Accessibility testing** (keyboard-only workflows)
- **Concurrent instance testing** (multiple apps editing same JSON)
- **Video playback testing** (when video player framework is finalized)
