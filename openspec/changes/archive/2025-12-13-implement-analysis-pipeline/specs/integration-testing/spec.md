# integration-testing Specification Delta

## ADDED Requirements

### Requirement: Mock Detector for Testing

The system SHALL provide a `MockDetector` that returns deterministic detection results for testing the pipeline without requiring model downloads.

#### Scenario: Mock detector returns configured categories
- **WHEN** `MockDetector` is configured with categories `["Profanity", "Violence"]`
- **THEN** detector returns results only for those categories

#### Scenario: Mock detector deterministic behavior based on frame
- **WHEN** mock detector analyzes frames with indices 0, 1, 2, ...
- **THEN** detector returns consistent, deterministic results (e.g., detect violence on even frames)

#### Scenario: Mock detector is registered in detector registry
- **WHEN** detector registry is checked
- **THEN** "mock" type is available and can be instantiated with config

#### Scenario: Mock detector skips disabled categories
- **WHEN** config disables a category via `enabled: false`
- **THEN** mock detector does not return results for that category

### Requirement: Integration Test Fixtures

The system SHALL provide fixtures and utilities for integration testing the analysis pipeline without model dependencies.

#### Scenario: Test video file available
- **WHEN** integration tests run
- **THEN** a minimal test video file is available (3-5 seconds, ~1 MB, any format ffmpeg supports)

#### Scenario: Test configuration files available
- **WHEN** integration tests need configs
- **THEN** fixture configs are available:
  - Config with mock detector
  - Config with invalid parameters (for error testing)
  - Config with various frame sampling strategies

#### Scenario: Temporary directory for test output
- **WHEN** pipeline tests write output files
- **THEN** pytest fixture provides isolated temp directory that is auto-cleaned after test

#### Scenario: Test fixtures cleaned up automatically
- **WHEN** test completes (pass or fail)
- **THEN** temporary files, video frames, and temp directories are automatically removed

### Requirement: End-to-End Pipeline Integration Tests

The system SHALL provide comprehensive integration tests that validate the complete analysis pipeline without requiring models.

#### Scenario: Pipeline analyzes video successfully
- **WHEN** integration test calls `AnalysisPipeline.analyze()` on test video with mock detector
- **THEN** analysis completes without errors and returns DetectionResult list

#### Scenario: Output JSON matches schema
- **WHEN** pipeline analysis is complete
- **THEN** generated JSON has correct structure:
  - `metadata` with file, duration, processed_at, config
  - `segments` array with start_time, end_time, labels, confidence, detections
  - `summary` with total_segments_detected, total_flagged_duration, detection_counts

#### Scenario: Frame sampling is respected
- **WHEN** config specifies `sample_rate: 2.0`
- **THEN** pipeline analyzes approximately every 2 seconds (verifiable by frame count in logs)

#### Scenario: Segment merging combines nearby detections
- **WHEN** config specifies `merge_threshold: 2.0` and detections occur at t=0.5s and t=1.5s
- **THEN** output merges these into single segment from t=0.5s to t=1.5s

#### Scenario: Empty detections for video with no triggers
- **WHEN** pipeline analyzes video with mock detector not returning any results
- **THEN** output contains empty segments list and summary shows `total_segments_detected: 0`

#### Scenario: Pipeline cleanup happens on success
- **WHEN** pipeline.analyze() completes successfully
- **THEN** cleanup() is automatically called (detectors freed, temp files removed)

#### Scenario: Pipeline cleanup happens on error
- **WHEN** pipeline encounters error during analysis (e.g., detector fails)
- **THEN** cleanup() is still called to release resources

#### Scenario: Invalid configuration raises error
- **WHEN** pipeline is initialized with invalid config (missing required fields, bad detector type)
- **THEN** descriptive error is raised before analysis begins

#### Scenario: Missing video file raises error
- **WHEN** pipeline is given path to non-existent video file
- **THEN** FileNotFoundError is raised with helpful message

#### Scenario: Detector failure is logged but pipeline continues
- **WHEN** detector raises exception during frame analysis
- **THEN** error is logged to logger, other detectors still analyze that frame

### Requirement: Integration Test Coverage

The system SHALL have comprehensive integration tests covering major pipeline paths and edge cases.

#### Scenario: Test pipeline with real detector (deferred activation)
- **WHEN** LLaVA model is downloaded and PYTEST_RUN_WITH_MODELS=1
- **THEN** integration tests can optionally run with real LLaVA detector instead of mock

#### Scenario: Test pipeline with multiple detectors
- **WHEN** config specifies multiple detector types
- **THEN** integration test verifies all detectors run and results are aggregated

#### Scenario: Test pipeline resource cleanup
- **WHEN** integration test monitors file handles and memory
- **THEN** no leaks are detected after pipeline runs (deferred: memray/pytest-memray)

#### Scenario: Test CLI end-to-end
- **WHEN** integration test invokes CLI (subprocess or direct import)
- **THEN** full end-to-end flow works: config → analysis → JSON output written

#### Scenario: Test error reporting in CLI
- **WHEN** CLI is given invalid config or missing files
- **THEN** appropriate error is logged and exit code is non-zero
