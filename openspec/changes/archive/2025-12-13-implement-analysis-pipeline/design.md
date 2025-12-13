# Design: Analysis Pipeline Implementation

## Context

The project has a modular architecture with separate concerns:
1. **Video Extraction** (`VideoExtractor`) - extracts frames and audio from video files
2. **Detection Framework** (`DetectionPipeline`) - orchestrates detectors on individual frames
3. **Output Generation** - formats detection results as JSON

What's missing is the **Analysis Pipeline** that ties these together:
- Iterates through extracted frames at the configured sample rate
- Passes frames to the detection pipeline
- Aggregates results across all frames
- Handles errors and logging
- Integrates with the CLI to run end-to-end analysis

Currently, `video_censor_personal.py` has a TODO placeholder and no actual analysis logic.

## Goals / Non-Goals

### Goals
- Create `AnalysisPipeline` class that orchestrates video extraction → detection → output generation
- Wire the pipeline into the CLI (`video_censor_personal.py`) for end-to-end execution
- Implement mock detectors that return deterministic results for testing without model dependencies
- Create integration tests that validate the full pipeline without downloading models
- Support both visual and audio modalities (infrastructure; actual audio detection deferred to future)
- Properly handle configuration, resource cleanup, and error cases

### Non-Goals
- GPU optimization (deferred to future feature)
- Batch inference (single-frame processing acceptable for MVP)
- Third-party API support (local models only)
- Audio-based detection implementation (framework only)
- Custom detector registration from CLI (programmatic registration only)

## Decisions

### 1. AnalysisPipeline Design
**Decision**: Create a separate `AnalysisPipeline` class in `video_censor_personal/pipeline.py` that orchestrates the workflow.

**Why**: Keeps concerns separated. The main entry point (`video_censor_personal.py`) focuses on CLI/error handling, while `AnalysisPipeline` handles the core analysis logic. This makes it testable and reusable.

**Alternatives Considered**:
- Put logic directly in `video_censor_personal.py` - Mixes CLI concerns with business logic; harder to test
- Create a generic `Orchestrator` base class - Over-engineered for current needs; start simple

### 2. Mock Detector for Testing
**Decision**: Create `MockDetector` class in `video_censor_personal/detectors/mock_detector.py` that returns deterministic results based on frame index.

**Why**: Allows integration tests to run the full pipeline without downloading LLaVA models (~4-26 GB). Tests can validate the pipeline logic in isolation. Registered as detector type `"mock"`.

**Alternatives Considered**:
- Monkeypatch detector registry in tests - Works but less transparent; harder to debug
- Require downloading models for tests - Defeats the purpose; blocks CI/CD
- Create multiple mock detector types - Unnecessary complexity; one is enough

### 3. Configuration Structure for Detectors
**Decision**: Config's `detections` section specifies detector chain as a new optional `detectors` list.

Example:
```yaml
detections:
  nudity: { enabled: true, sensitivity: 0.7, model: "local" }
  # ... other categories ...
  
detectors:
  - type: "llava"
    name: "llava-vision"
    model_name: "liuhaotian/llava-v1.5-7b"
    categories: ["Nudity", "Profanity", "Violence", "Sexual Theme"]
```

Fallback: If `detectors` not present, try to auto-discover from `detections` section (backward compat).

**Why**: Explicit detector chain configuration is clearer and more flexible. Allows multiple detectors, custom ordering, and different models.

**Alternatives Considered**:
- Only derive detectors from category configs - Less flexible; can't specify multiple detectors or custom models
- Require detectors in all configs - Breaking change; fails backward compat

### 4. Frame Iteration and Timecode Assignment
**Decision**: `AnalysisPipeline.analyze()` iterates frames via `VideoExtractor.extract_frames()`, passes each to `DetectionPipeline.analyze_frame()`.

Timecode assignment:
- Frame's timecode is set by `VideoExtractor`
- `DetectionPipeline.analyze_frame()` assigns frame timecode to all results
- Results are aggregated in order

**Why**: Matches the existing architecture. `VideoExtractor` already handles frame timing correctly.

**Alternatives Considered**:
- Manual frame indexing in pipeline - Duplicates extraction logic; error-prone
- Timecode set by detectors - Detectors shouldn't know about timing

### 5. Error Handling Strategy
**Decision**:
- Frame-level detector failures are logged and skipped (partial results acceptable)
- Configuration/initialization errors raise immediately and stop analysis
- Resource cleanup happens in `finally` block (context manager)

**Why**: Analysis is resilient to individual detector failures but fails fast on config errors. Cleanup is guaranteed.

**Alternatives Considered**:
- Stop on first detector error - Too rigid; should be resilient
- Ignore all errors silently - Dangerous; errors go unnoticed

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Mock detector diverges from real behavior** | Document mock behavior clearly; update when detector changes. Tests focus on pipeline logic, not detector accuracy. |
| **Performance regression if iterating all frames** | Config allows frame sampling; default to 1.0 sec intervals. Can optimize later with batch processing. |
| **Memory leak if detectors not cleaned up** | Use context managers and finally blocks. Test with `pytest --memray` to detect leaks. |
| **Config backward compatibility broken** | Provide sensible fallback if `detectors` key missing; auto-infer from category configs. |

## Migration Plan

1. **Backward Compatibility**: If `detectors` key missing from config, generate detector list from enabled categories:
   - Extract category names that have `enabled: true`
   - Create default LLaVA detector covering all enabled categories
   - This keeps existing configs working

2. **Gradual Rollout**:
   - Implement pipeline infrastructure first (no behavior change)
   - Add mock detector support
   - Update CLI to call pipeline
   - Add integration tests
   - All changes go behind new code; existing configs still work

## Confirmed Decisions

1. **Detector chains in config** ✓
   - **Decision**: Yes, support multiple detectors running on same frame
   - **Rationale**: `DetectionPipeline` already supports multiple detectors; config allows list of detectors
   - **Implementation**: Update YAML schema to include `detectors:` list

2. **Audio extraction strategy** ✓
   - **Decision**: Extract audio once, cache it, pass to all detectors
   - **Rationale**: Efficient reuse; simplifies pipeline logic
   - **Deferred**: Fine-grained per-detector audio extraction (future feature)

3. **Mock detector behavior** ✓
   - **Decision**: Simple deterministic behavior (depends on frame index)
   - **Rationale**: Suitable for MVP testing; sufficient to validate pipeline logic
   - **Deferred**: Configurable detection patterns (future enhancement if needed)
