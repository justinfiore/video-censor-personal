# Change: Add Detection Framework

## Why

The system needs a flexible detection architecture that supports multiple detector implementations (LLMs, APIs, local models) while enabling each detector to identify multiple content categories in a single pass. A framework enables pluggable detectors, efficient multi-category detection, and future extensibility without reprocessing frames.

## What Changes

- Define detector interface and lifecycle (initialize, detect, cleanup)
- Implement detector registry to support multiple detector implementations
- Build frame/audio analysis pipeline to invoke detectors on extracted content
- Support multi-category results from single detector (one LLM identifies Profanity, Nudity, Violence simultaneously)
- Aggregate results across multiple detectors if needed
- Handle detector configuration and model selection
- Implement error handling and graceful fallback for detector failures

## Key Architectural Decision

**Multi-category per detector**: Each detector can identify multiple content categories in a single inference pass. This differs from per-category detectors and reduces computational cost while maintaining flexibility. Users can configure which detector(s) to use and which categories each detector should analyze.

## Impact

- **New capability**: detection-framework (detector abstraction, orchestration, multi-category analysis)
- **Affected specs**: detection-framework (new spec)
- **Code changes**: video_censor_personal/detection.py (framework), video_censor_personal/detectors/ (detector implementations)
- **Tests**: tests/test_detection.py (comprehensive framework and detector tests)
