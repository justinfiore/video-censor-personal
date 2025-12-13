# Change: Add Output Generation

## Why

The system needs to serialize detection results into structured JSON output that users can consume, analyze, and integrate with other tools. This includes defining the detection result data model, merging overlapping segments, calculating summary statistics, and formatting output according to user configuration.

## What Changes

- Define `DetectionResult` data class for standardized detection representation
- Implement segment merging strategy to combine nearby detections
- Build JSON output generator respecting config settings (include_confidence, include_frames, pretty_print)
- Calculate summary statistics (total segments, flagged duration, detection counts)
- Support dual time formatting (HH:MM:SS and seconds)
- Create output writer to persist results to file

## Impact

- **New capability**: output-generation (JSON serialization and formatting)
- **Affected specs**: output-generation (new spec)
- **Code changes**: video_censor_personal/output.py (new module), video_censor_personal/frame.py (minor extension for DetectionResult)
- **Tests**: tests/test_output.py (comprehensive output tests)
