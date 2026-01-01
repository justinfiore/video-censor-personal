# Integration Testing Proposal Summary

## Executive Summary

The Preview Editor UI (`add-preview-editor-ui`) implemented 10+ components with 98 unit tests but only 7 narrow integration tests covering the segment manager in isolation. This proposal adds 36+ new integration tests organized into 5 test categories, covering complete user workflows, error recovery, and state consistency across the three-pane UI.

## Test Coverage Gap Analysis

### Current State
- ✅ Unit tests: 98 tests covering individual components (segment manager, keyboard shortcuts, etc.)
- ✅ Component isolation verified: Each pane tested independently
- ⚠️ Integration tests: 7 tests focused only on SegmentManager (file load/save)
- ❌ Missing: Cross-component workflows (segment list → details pane sync)
- ❌ Missing: File I/O edge cases (malformed JSON, external modifications)
- ❌ Missing: Error recovery (what happens when operations fail)
- ❌ Missing: State consistency validation (all panes in sync)

### Example Gaps
| Workflow | Currently Tested | Gap |
|----------|------------------|-----|
| Open JSON → segments displayed | ❌ | Need test; JSON loading scenario untested |
| User clicks segment → all panes update | ❌ | Tested per-component; cross-pane sync untested |
| Toggle allow → JSON persisted → reload | ✅ | Covered by test_integration_load_and_toggle |
| Rapid toggles (5+) → final state consistent | ❌ | Concurrency, atomic writes untested |
| JSON save fails → state reverts | ❌ | Error recovery untested |
| External JSON modification → warning shown | ❌ | File watch scenario untested |
| Malformed JSON → helpful error shown | ❌ | Error path untested |
| Large JSON (100+ segments) + UI responsive | ✅ | Covered by test_integration_large_segment_list |

## Proposed Test Structure

### 5 Test Categories (36 tests total)

1. **File I/O Workflows** (10 tests)
   - JSON + video with various path types (absolute, relative)
   - Missing files and recovery (browse for video, review-only mode)
   - JSON schema validation and helpful errors
   - Auto-load from command-line argument
   - Recent files persistence
   - External modifications detection

2. **Cross-Component Synchronization** (8 tests)
   - Segment selection → all panes update synchronously
   - Video playback position → segment list auto-highlights
   - Keyboard navigation → full UI update
   - Batch operations → consistent across all panes
   - Rapid clicks/toggles → correct final state

3. **State Consistency & Edge Cases** (8 tests)
   - Large segment lists (100+)
   - Rapid consecutive toggles (5+)
   - JSON with missing/mixed "allow" fields
   - Custom external fields preservation
   - Segments with empty detections array

4. **Error Recovery & Resilience** (6 tests)
   - Video playback failure → UI remains functional
   - JSON save failure (disk full, permissions) → helpful error, state reverts
   - User deletes JSON while session open → graceful handling
   - Concurrent operations → no conflicts
   - Debounced keyboard shortcuts

5. **Window Lifecycle & Resources** (4 tests)
   - App startup with auto-load
   - Cleanup on close (file handles, memory)
   - Graceful shutdown during playback
   - Resource leak verification

## Key Design Decisions

1. **Minimal Mocking**: Test real file I/O, real segment state management. Mock only VLC (already partially done in unit tests).

2. **Multi-Level State Assertion**: Verify at file level (JSON on disk), manager level (in-memory state), and widget level (UI display).

3. **User-Centric Error Testing**: Test errors from user perspective ("my video disappeared") rather than code-level errors.

4. **Reusable Fixtures**: Create atomic fixtures (sample video, JSON payloads, temp workspace) and composite fixtures (app with files pre-loaded) for DRY testing.

5. **Feature-Based Organization**: Group tests by user workflow, not by component. Makes tests easier to understand and extend.

## Benefits

- **Higher Confidence**: Production-ready UI; user workflows validated
- **Better Error Messages**: Error scenarios tested; users get helpful feedback
- **Future-Proof**: Test patterns enable rapid testing of new UI features (e.g., `ui-full-workflow`)
- **Data Safety**: Atomic persistence, crash recovery, no corruption validated
- **Performance Baseline**: Large segment lists (100+) tested for responsiveness
- **Debugging Support**: Headed mode allows visual observation of test execution, speeding up failure diagnosis
- **CI/CD Ready**: Headless mode requires no display server, runs cleanly in automated environments

## Implementation Effort

- **Phase 0 (VLC Removal)**: 1 hour - Remove VLC code, tests, dependencies (separate commit)
- **Phase 1 (Fixtures)**: 3-4 hours - Headless/headed mode support + JSON payloads, fixtures, helpers
  - 1 hour: Implement headless/headed mode infrastructure
  - 2-3 hours: Create fixtures and helpers
- **Phase 2 (File I/O)**: 3-4 hours - 10 tests covering JSON load/save workflows
- **Phase 3 (Sync)**: 2-3 hours - 8 tests validating cross-pane updates
- **Phase 4 (Consistency)**: 2-3 hours - 8 tests for edge cases and state
- **Phase 5 (Error Recovery)**: 2-3 hours - 6 tests for error paths
- **Phase 6 (Lifecycle)**: 1-2 hours - 4 tests for startup/shutdown
- **Phase 7 (Validation)**: 1-2 hours - Coverage reporting, gap analysis

**Total**: 15-22 hours (1-2 days of focused work)

## Test Execution Examples

### Running Tests (Headless - Default)
```bash
# All integration tests (headless, CI mode)
pytest tests/ui/test_integration.py -v

# Single test (headless)
pytest tests/ui/test_integration.py::test_file_io_open_json -v

# With coverage (headless)
pytest tests/ui/ --cov=video_censor_personal.ui --cov-report=term-missing
```

### Running Tests (Headed - Debugging)
```bash
# All tests with visual output (500ms delays between actions)
PYTEST_HEADED=1 pytest tests/ui/test_integration.py -v

# Single test with visual output and debugger
PYTEST_HEADED=1 pytest tests/ui/test_integration.py::test_segment_selection_updates_details -v --pdb

# Using CLI flag instead of environment variable
pytest tests/ui/test_integration.py --headed -v

# Headed + verbose + show print statements
PYTEST_HEADED=1 pytest tests/ui/test_integration.py -vv -s
```

### Headed Mode Benefits for Debugging
```
Developer encounters test failure:
  ❌ test_rapid_toggles_persist_state

Traditional approach (headless):
  - Read assertion message
  - Add print statements
  - Rerun test
  - Repeat until found

With headed mode:
  PYTEST_HEADED=1 pytest tests/ui/test_integration.py::test_rapid_toggles_persist_state -v --pdb
  → Window displays in real time
  → Developer sees visual state (UI, segment list, details pane)
  → Can interact with window while paused in debugger
  → Diagnoses issue in minutes instead of iterations
```

## Approval Gate

This proposal requires approval before implementation begins. Once approved, implementation will follow the task list in `tasks.md` sequentially.

**Important**: Phase 0 removes VLC entirely (breaking change). This is a separate commit that must complete before other phases begin.

**Blocking questions** (to clarify before approval):
1. Confirm VLC removal timing: should Phase 0 run immediately or can we defer?
2. Coverage target: maintain 80% or aim higher (e.g., 85-90%)? (Proposal: 80%, report actual metrics)
3. Should we add tests for future video playback when a replacement framework is chosen?
