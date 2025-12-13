# Change: Implement Analysis Pipeline for End-to-End Video Processing

## Why

The system currently has isolated components (video extraction, detection framework, output generation) but lacks the orchestration layer to run them end-to-end. Users cannot analyze videos even when models are available because the main analysis pipeline is not implemented. This blocks all functional testing and real-world usage. Additionally, no integration tests exist to validate the complete workflow without requiring actual model downloads.

## What Changes

- Implement `AnalysisPipeline` class that orchestrates video extraction, frame sampling, detector initialization, and result aggregation
- Add CLI integration to wire the pipeline into the main entry point (`video_censor_personal.py`)
- Build mock/stub detectors for testing without model dependencies
- Create comprehensive integration tests that validate the full analysis pipeline end-to-end
- Add test fixtures for video files, configuration, and mock data

### **BREAKING** Changes
- Main entry point now requires `detections` section in YAML config to specify detector chain (currently CLI just validates config existence)

## Impact

- **Affected specs**:
  - `analysis-pipeline` (new capability)
  - `integration-testing` (new capability)
  - `project-foundation` (CLI entrypoint updated)
  
- **Affected code**:
  - `video_censor_personal.py` - Main entry point implementation
  - `video_censor_personal/cli.py` - CLI argument parsing (may add --detector-type flag)
  - `video_censor_personal/detectors/` - Add mock detectors for testing
  - `tests/` - Add integration test suite
  - `video-censor.yaml.example` - Update with full detector chain example

- **New files**:
  - `video_censor_personal/pipeline.py` - Analysis pipeline orchestrator
  - `video_censor_personal/detectors/mock_detector.py` - Mock detector for testing
  - `tests/test_integration_pipeline.py` - Integration tests
  - `tests/fixtures/` - Test fixtures (sample videos, configs)
