# Change: Expand Preview Editor UI Integration Testing

## Why

The Preview Editor UI (`add-preview-editor-ui` change) implemented 10+ new modules with 98 unit tests covering individual components. However, integration tests are limited—only 7 tests in `test_integration.py` covering the segment manager in isolation. Critical user workflows are not tested:

- **Complete file open/load workflows** (JSON + video path resolution)
- **Cross-component interactions** (segment list → details pane → video player synchronization)
- **State consistency** (all UI updates remain synchronized after operations)
- **Error recovery** (what happens when files missing, corrupted JSON)
- **Keyboard shortcuts and edge cases** (rapid clicks, invalid operations, resource cleanup)

The implementation summary notes the tests are "limited" and designed more for unit coverage. The project's testing strategy requires 80%+ coverage with comprehensive integration tests. Current integration test gaps create risk in production use: users could encounter broken state transitions or data loss scenarios that aren't caught.

## What Changes

- **Add 20+ new integration tests** covering end-to-end UI workflows
- **Test three-pane synchronization** (segment selection, details display, video seeking, timeline updates)
- **Test file I/O workflows** (open with/without video, invalid JSON, missing files, external modifications)
- **Test persistence and data integrity** (concurrent operations, rapid toggles, crash safety)
- **Test error scenarios** and recovery paths
- **Add integration test fixtures** (sample video files, pre-built JSON payloads, temporary workspaces)
- **Improve integration test structure** with better organization and descriptive names
- **Document test patterns** for future UI feature testing

## Impact

- **Affected specs**: `segment-review`, `ui-testing`, `integration-testing`
- **Affected code**: `tests/ui/test_integration.py` (expand), new fixtures in `tests/ui/conftest.py`
- **No breaking changes** to implementation; tests are additive
- **Improves confidence** in UI reliability before user-facing use
- **Provides patterns** for future UI feature testing (e.g., `ui-full-workflow` change)
