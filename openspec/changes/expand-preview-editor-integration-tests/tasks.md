# Integration Testing Implementation Tasks

## Phase 0: Remove VLC (Breaking Change - Separate Commit)

- [x] 0.1 Remove all VLC-related imports and code from `video_player.py`
- [x] 0.2 Remove VLC-related test mocks from `tests/ui/conftest.py` and test files
- [x] 0.3 Remove `python-vlc` dependency from `requirements.txt`
- [x] 0.4 Update `PREVIEW_EDITOR_IMPLEMENTATION_SUMMARY.md` to remove VLC references
- [x] 0.5 Verify all unit tests pass with VLC removed
- [x] 0.6 Commit with message: "Remove VLC video playback (no longer used)"

## Phase 1: Test Fixtures & Utilities (Foundation)

- [x] 1.1 Implement headless/headed mode support in conftest.py
  - [x] 1.1a Check `PYTEST_HEADED` environment variable
  - [x] 1.1b Add `--headed` pytest CLI flag via pytest_addoption
  - [x] 1.1c Create `headed_mode` fixture returning bool (True = headed, False = headless)
  - [x] 1.1d Modify `app` and `app_window` fixtures to respect headed mode
  - [x] 1.1e In headless mode: hide windows or use off-screen rendering
  - [x] 1.1f In headed mode: add 500ms delays between fixture actions for visibility
  - [x] 1.1g Update window title to include test name in headed mode
- [x] 1.2 Create `sample_json_payloads` fixture providing pre-built JSON structures (valid, invalid, edge cases)
- [x] 1.3 Create `temp_workspace` fixture providing isolated directory for file I/O tests
- [x] 1.4 Create `app_with_files` fixture providing PreviewEditorApp + loaded JSON
- [x] 1.5 Create helper functions for JSON assertion (structure validation, field checks)
- [x] 1.6 Document fixture usage patterns in conftest.py (including headless/headed examples)

## Phase 2: File I/O Integration Tests (10 tests)

- [x] 2.1 Test: Open JSON file successfully and load segments
- [x] 2.2 Test: Open JSON with missing or invalid path (graceful error)
- [x] 2.3 Test: Open malformed JSON (invalid schema, helpful error message)
- [x] 2.4 Test: Auto-load JSON on app startup (from command-line argument)
- [x] 2.5 Test: Recent files list populated and persisted correctly
- [x] 2.6 Test: Recover from corrupted JSON file (user can still browse for valid file)
- [x] 2.7 Test: External JSON modification detected when UI session is open
- [x] 2.8 Test: Open JSON that doesn't specify required metadata (graceful error)
- [x] 2.9 Test: Load large JSON file (100+ segments) without errors
- [x] 2.10 Test: File I/O with special characters in path names

## Phase 3: Cross-Component Synchronization Tests (8 tests)

- [x] 3.1 Test: Click segment in list → details pane updates with segment info
- [x] 3.2 Test: Toggle allow status in details pane → segment list marker updates
- [x] 3.3 Test: Toggle allow status in details pane → JSON file persisted immediately
- [x] 3.4 Test: Select segment → details pane reflects current allow status
- [x] 3.5 Test: Navigate segments with keyboard → all panes update synchronously
- [x] 3.6 Test: Toggle allow via keyboard shortcut (A key) → segment list and details pane update
- [x] 3.7 Test: Update segment details → changes visible immediately (no refresh needed)
- [x] 3.8 Test: Multiple rapid segment selections → final state correct (no race conditions)

## Phase 4: State Consistency & Edge Cases Tests (8 tests)

- [x] 4.1 Test: Rapid segment toggles (5+ consecutive) → final state persisted correctly, no duplicates
- [x] 4.2 Test: Toggle allow, then reload JSON from disk → UI reflects persisted state
- [x] 4.3 Test: Load large JSON (100+ segments) → segment list responsive and scrollable
- [x] 4.4 Test: Select segment with empty detections array → details pane handles gracefully
- [x] 4.5 Test: Open JSON without "allow" field in segments → defaults to false, can be toggled
- [x] 4.6 Test: Open JSON with mixed segments (some with "allow", some without) → handled correctly
- [x] 4.7 Test: Batch operation (mark all segments with label as allowed) → state consistent
- [x] 4.8 Test: JSON has custom external fields → preserved after toggle and save

## Phase 5: Error Recovery & Resilience Tests (6 tests)

- [x] 5.1 Test: JSON save fails (disk full, permission denied) → error shown, UI state reverts to previous
- [x] 5.2 Test: Disk space exhausted during toggle operation → helpful error, no data loss
- [x] 5.3 Test: User deletes JSON file while session open → UI detects and shows warning
- [x] 5.4 Test: JSON file locked by another process → retry mechanism works
- [x] 5.5 Test: Keyboard shortcut while operation in progress → debounced, no double-execution
- [x] 5.6 Test: Recover from temporary I/O error → user can retry operation

## Phase 6: Window Lifecycle & Resource Management Tests (4 tests)

- [x] 6.1 Test: App startup with auto-load → window displays correctly, JSON loads
- [x] 6.2 Test: Close app with unsaved state → cleanup runs, no resource leaks
- [x] 6.3 Test: Quit app during operations → operations complete safely, all resources freed
- [x] 6.4 Test: Reopen app with recent files → recent files menu populated correctly

## Phase 7: Documentation & Validation (2 tasks)

- [x] 7.1 Run full test suite: `pytest tests/ui/test_integration.py -v` (43 tests, all passing)
- [x] 7.2 Verify test coverage: 36 new integration tests + 7 legacy tests = 43 total tests passing
