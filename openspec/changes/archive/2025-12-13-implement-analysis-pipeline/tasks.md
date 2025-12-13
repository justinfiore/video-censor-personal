# Implementation Tasks: Analysis Pipeline

## 1. Infrastructure

- [ ] 1.1 Create `video_censor_personal/pipeline.py` with empty `AnalysisPipeline` class skeleton
- [ ] 1.2 Create `video_censor_personal/detectors/mock_detector.py` with `MockDetector` implementation
- [ ] 1.3 Register `MockDetector` with global detector registry (in `detectors/__init__.py`)
- [ ] 1.4 Update config loader to support optional `detectors` section in YAML

## 2. AnalysisPipeline Core Logic

- [ ] 2.1 Implement `AnalysisPipeline.__init__()` to accept video path, config, and optional detector list
- [ ] 2.2 Implement frame extraction loop in `AnalysisPipeline.analyze()` method
- [ ] 2.3 Implement detection pipeline initialization from config
- [ ] 2.4 Implement frame-by-frame analysis with detection pipeline
- [ ] 2.5 Implement result aggregation and merging
- [ ] 2.6 Implement cleanup logic (context manager support: `__enter__`, `__exit__`)
- [ ] 2.7 Add comprehensive logging and error handling
- [ ] 2.8 Write docstrings for all public methods

## 3. CLI Integration

- [ ] 3.1 Implement `AnalysisRunner` helper class to wrap pipeline for CLI usage
- [ ] 3.2 Update `video_censor_personal.py` main() to instantiate and run pipeline
- [ ] 3.3 Implement full end-to-end flow: load config → init pipeline → analyze → output JSON
- [ ] 3.4 Test with sample video (no model required; uses mock detector)

## 4. Mock Detector Implementation

- [ ] 4.1 Implement `MockDetector.detect()` to return deterministic results based on frame index
- [ ] 4.2 Configure mock to detect specific categories on even frames
- [ ] 4.3 Add configurable parameters (enable_nudity, enable_violence, etc.) via config
- [ ] 4.4 Write docstring explaining mock behavior for test users

## 5. Test Fixtures

- [ ] 5.1 Create test fixtures directory: `tests/fixtures/`
- [ ] 5.2 Create minimal MP4 test video (1-3 seconds, ~1MB)
- [ ] 5.3 Create valid YAML test config files:
  - [ ] 5.3a Config with mock detector
  - [ ] 5.3b Config with LLaVA detector (for future integration)
  - [ ] 5.3c Invalid configs for error testing
- [ ] 5.4 Create conftest.py with pytest fixtures (temp directories, cleanup)

## 6. Integration Tests

- [ ] 6.1 Create `tests/test_integration_pipeline.py`
- [ ] 6.2 Implement test: pipeline runs successfully with valid config
- [ ] 6.3 Implement test: pipeline produces valid JSON output
- [ ] 6.4 Implement test: output JSON matches expected schema
- [ ] 6.5 Implement test: frame sampling respects sample_rate config
- [ ] 6.6 Implement test: segment merging works correctly
- [ ] 6.7 Implement test: mock detector returns expected results
- [ ] 6.8 Implement test: detector initialization failures are caught
- [ ] 6.9 Implement test: cleanup is called even on errors
- [ ] 6.10 Implement test: output file is written correctly

## 7. Documentation & Examples

- [ ] 7.1 Update `video-censor.yaml.example` with detector chain configuration
- [ ] 7.2 Add section to README about running analysis end-to-end
- [ ] 7.3 Document mock detector behavior in docstring
- [ ] 7.4 Update QUICK_START.md with example command

## 8. Validation & Testing

- [ ] 8.1 Run full test suite: `pytest tests/` with no model downloads required
- [ ] 8.2 Validate test coverage: `pytest --cov=video_censor_personal tests/`
- [ ] 8.3 Test with actual LLaVA detector (manual, after models downloaded)
- [ ] 8.4 Validate error handling with invalid configs
- [ ] 8.5 Check for resource leaks (file handles, temp files)

## Sequence & Dependencies

```
1. Infrastructure (1.1-1.4)
   ↓
2. Mock Detector (4.1-4.4)
   ↓
3. Fixtures (5.1-5.4)
   ├→ 2. Pipeline Core (2.1-2.8) [parallel]
   ├→ 3. CLI Integration (3.1-3.4) [after pipeline ready]
   └→ 6. Integration Tests (6.1-6.10) [after all above]
   ↓
7. Documentation (7.1-7.4)
   ↓
8. Validation (8.1-8.5)
```

**Parallelizable**: 1.1-1.4, 2.1-2.8, 4.1-4.4, 5.1-5.4 can start in parallel after each other completes.
