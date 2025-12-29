# Change: Segment Times Refinement with Millisecond Precision

## Why

When outputting segment timestamps as HH:MM:SS strings, we currently lose millisecond precision, which is important for accurate remediation. Additionally, the system should accept both formats (with and without milliseconds) when reading segments from JSON files to accommodate manual editing where users may not provide milliseconds. This allows users to manually adjust timestamps for false positives without losing precision in the system's processing.

## What Changes

- **Output precision**: When writing segments to JSON output, `start_time` and `end_time` fields now include milliseconds in HH:MM:SS.mmm format
- **Input flexibility**: When reading segments from JSON input, parse both HH:MM:SS.mmm (with milliseconds) and HH:MM:SS (without milliseconds) formats
- **Duration invariant**: Enforce and validate that `duration_seconds` is never used for remediation processing—only `start_time` and `end_time` are used; add tests to verify this invariant
- **Backward compatibility**: Numeric timestamp fields (`start_time_seconds`, `end_time_seconds`) continue to be supported for reading

## Impact

- Affected specs: `output-generation`
- Affected code:
  - `video_censor_personal/output.py` (`format_time()`, `generate_json_output()`)
  - `video_censor_personal/segments_loader.py` (`_parse_time_string()`)
  - Tests: `tests/test_output.py`, `tests/test_segments_loader.py`
  - Add new test to validate duration is never used in remediation
