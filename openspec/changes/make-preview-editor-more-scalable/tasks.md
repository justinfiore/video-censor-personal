# Implementation Tasks: Make Preview Editor More Scalable

## 1. Profiling & Instrumentation

- [x] 1.1 Add detailed timing instrumentation at app startup:
  - JSON file loading time
  - Segment list population time (separate: parsing vs widget creation)
  - Video player initialization time
  - Total UI initialization time
- [x] 1.2 Create a `PerformanceProfiler` utility class to log and track timing metrics
- [ ] 1.3 Add detailed profiling/debug logging around segment list UI creation:
  - Log time to parse JSON segment data (before widget creation)
  - Log time to CREATE each individual segment widget (at TRACE level)
  - Log cumulative time for all widget creation
  - Log time for frame layout/rendering after all widgets added
  - Log memory usage before/after segment list population
  - Add phase-level DEBUG logs: "Segment list: started parsing", "Segment list: widget creation started", "Segment list: X widgets created in Yms", "Segment list: layout complete"
- [ ] 1.4 Run profiler on small video (15 segments) and large video (206 segments); capture logs and compare bottleneck
- [ ] 1.5 Analyze logs and identify the longest single operation blocking the main thread
- [x] 1.6 Document findings in a `SCALING_ANALYSIS.md` file with specific timings and recommendations

## 2. Virtualization of Segment List

- [ ] 2.1 Study existing `SegmentListPaneImpl` implementation in `segment_list_pane.py` and understand current layout
- [ ] 2.2 Design a virtual list container using CustomTkinter Canvas (mock it out in comments/pseudocode first)
- [ ] 2.3 Refactor `SegmentListPaneImpl` to use Canvas-based scrolling with visible-items-only rendering
- [ ] 2.4 Implement dynamic widget creation/destruction on scroll events (render items on viewport + buffer zone)
- [ ] 2.5 Ensure selection tracking works across scroll (highlight current segment even when off-screen initially)
- [ ] 2.6 Test virtualization with both small and large videos; verify no visual regressions
- [ ] 2.7 Measure and document performance improvement (target: ~75% reduction in widget creation time)

## 3. Background Threading (If Needed)

- [ ] 3.1 Assess if virtualization alone meets performance target; only proceed if still slow after 2.7
- [ ] 3.2 If proceeding: Create a `SegmentLoaderThread` class to handle JSON parsing and segment list population in background
- [ ] 3.3 Implement queue-based communication between loader thread and main UI thread (use `queue.Queue`)
- [ ] 3.4 Add a "Loading segments..." spinner/progress indicator while background thread works
- [ ] 3.5 Implement cancellation mechanism (e.g., if user closes window during load)
- [ ] 3.6 Test thread safety: rapid file open/close, file changes during load, concurrent operations
- [ ] 3.7 Verify UI remains responsive throughout load process

## 4. Audio Loading Optimization

- [ ] 4.1 Review current audio extraction and caching in `PyAVVideoPlayer` and `VideoPlayerPaneImpl`
- [ ] 4.2 If audio is extracted/cached multiple times, consolidate to single load during initialization
- [ ] 4.3 Defer non-essential audio processing (e.g., normalization for waveform display) to background thread
- [ ] 4.4 Measure audio load time before and after optimization
- [ ] 4.5 Verify audio playback quality and sync are unchanged

## 5. Integration Tests for Large Videos

- [ ] 5.1 Create test data generator to produce synthetic JSON files with N segments (50, 100, 206)
- [ ] 5.2 Create integration test file `tests/test_preview_editor_scaling.py` with:
  - Test case: Load 50-segment video, assert UI responsive
  - Test case: Load 206-segment video, assert initial display < 3s, full load < 10s
  - Test case: Scroll through large segment list, verify no lag or crashes
  - Test case: Select and play segments in large video, verify all features work
- [ ] 5.3 Add timing assertions to catch performance regressions in CI
- [ ] 5.4 Document how to run scaling tests locally (for debugging before commits)
- [ ] 5.5 Consider adding benchmark mode to measure exact timings (can be excluded from regular test runs)

## 6. Logging Optimization

- [ ] 6.1 Audit current logging in `PyAVVideoPlayer`, `SegmentListPaneImpl`, and `PreviewEditorApp` for chatty/dense logs
- [ ] 6.2 Move frame-by-frame logs (e.g., audio frame extraction, widget creation) to TRACE level
- [ ] 6.3 Keep phase-transition logs at DEBUG level (e.g., "Audio extraction started", "Segment list population complete")
- [ ] 6.4 Implement log level configuration via environment variable (e.g., `VIDEO_CENSOR_LOG_LEVEL=TRACE`)
- [ ] 6.5 Test with large video at each log level (INFO, DEBUG, TRACE) and measure log file size reduction
- [ ] 6.6 Update logging documentation in code to explain when to use each level
- [ ] 6.7 Verify that default log level (DEBUG) produces <100KB log file for 206-segment video

## 7. Documentation & Cleanup

- [ ] 7.1 Add code comments in `segment_list_pane.py` explaining virtualization strategy
- [ ] 7.2 Add code comments in `PyAVVideoPlayer` and audio loading explaining optimization rationale
- [ ] 7.3 Update `TESTING_GUIDE.md` with section on testing large videos
- [ ] 7.4 Create or update `PERFORMANCE_TUNING.md` documenting scaling decisions and log level guidance
- [ ] 7.5 Document how to enable TRACE logging for troubleshooting (environment variable, example)
- [ ] 7.6 Review and clean up any temporary test files or debug output

## 8. Final Validation

- [ ] 8.1 Test with the actual 1.5-hour, 206-segment video from logs
- [ ] 8.2 Verify UI loads and is responsive (no hangs)
- [ ] 8.3 Verify all segment operations work: selection, playback, marking allow/disallow
- [ ] 8.4 Run full test suite to ensure no regressions
- [ ] 8.5 Get user feedback on load time and responsiveness

---

**Acceptance Criteria**:
- UI is responsive with 200+ segment videos (no freezing during initial load)
- Initial UI display < 3 seconds
- Full segment list population < 10 seconds
- All segment operations remain fully functional
- Integration tests pass on macOS and (ideally) Windows/Linux
- No performance regressions on small videos (15 segments should load in < 500ms as before)
