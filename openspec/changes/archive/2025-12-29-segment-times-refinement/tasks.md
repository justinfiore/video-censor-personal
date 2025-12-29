# Implementation Tasks: Segment Times Refinement

## 1. Update Time Formatting and Parsing
- [x] 1.1 Modify `format_time()` in `output.py` to output HH:MM:SS.mmm format (e.g., "00:01:23.456")
- [x] 1.2 Update `_parse_time_string()` in `segments_loader.py` to accept both HH:MM:SS and HH:MM:SS.mmm formats
- [x] 1.3 Add unit tests for millisecond parsing: valid formats, edge cases (0ms, 999ms)
- [x] 1.4 Add unit tests for millisecond output formatting

## 2. Update Output Generation
- [x] 2.1 Modify `generate_json_output()` to use new `format_time()` for `start_time` and `end_time` fields
- [x] 2.2 Update test expectations in `test_output.py` to reflect millisecond format
- [x] 2.3 Verify JSON output integration test produces correct millisecond timestamps

## 3. Duration Invariant Validation
- [x] 3.1 Create new test file `tests/test_duration_invariant.py` 
- [x] 3.2 Add test: duration field not used in audio remediation
- [x] 3.3 Add test: duration field not used in video remediation
- [x] 3.4 Add test: segments loaded from JSON recalculate duration from start/end times
- [x] 3.5 Verify existing tests don't accidentally rely on duration for remediation decisions

## 4. Backward Compatibility Testing
- [x] 4.1 Test loading segments with old format (no milliseconds in HH:MM:SS)
- [x] 4.2 Test loading segments with numeric `start_time_seconds`/`end_time_seconds` only
- [x] 4.3 Test mixed format (some segments with milliseconds, some without)
- [x] 4.4 Run full integration test suite to ensure no regressions

## 5. Documentation Update
- [x] 5.1 Document millisecond output format in spec delta
- [x] 5.2 Note that input accepts both formats for flexibility
- [x] 5.3 Clarify that duration is derived from start/end times
