## 1. CLI Argument Addition

- [x] 1.1 Add `--input-segments <path>` argument to CLI parser
- [x] 1.2 Update CLI help text with usage examples
- [x] 1.3 Add validation: `--input-segments` requires `--input` video file
- [x] 1.4 Add validation: warn when `--output` (JSON) is specified with `--input-segments`

## 2. Segments JSON Loading

- [x] 2.1 Create `load_segments_from_json(path)` function
- [x] 2.2 Parse JSON and validate required structure (metadata, segments array)
- [x] 2.3 Return structured segment data compatible with existing remediation pipeline

## 3. Input Validation

- [x] 3.1 Validate `metadata.file` matches input video filename (warning if mismatch)
- [x] 3.2 Optionally validate `metadata.duration` matches video duration (within 1s tolerance)
- [x] 3.3 Fail gracefully with clear error message if JSON is malformed or unreadable

## 4. Main Entry Point Integration

- [x] 4.1 Detect `--input-segments` mode in main entry point
- [x] 4.2 Skip `AnalysisPipeline` initialization and analysis when in segments mode
- [x] 4.3 Load segments from JSON instead of running detection
- [x] 4.4 Pass loaded segments directly to remediation phase

## 5. Remediation Phase Integration

- [x] 5.1 Ensure audio remediation works with loaded segments
- [x] 5.2 Ensure skip chapters generation works with loaded segments
- [x] 5.3 Ensure `"allow": true` segments are skipped during remediation
- [x] 5.4 Ensure `--allow-all-segments` flag is ignored in remediation mode

## 6. Testing

- [x] 6.1 Unit test: `--input-segments` parses correctly
- [x] 6.2 Unit test: JSON loading validates structure
- [x] 6.3 Unit test: metadata validation warns on mismatch
- [x] 6.4 Integration test: remediation-only workflow produces expected output
- [x] 6.5 Integration test: allow overrides are respected in remediation mode
- [x] 6.6 Integration test: `--allow-all-segments` is ignored when `--input-segments` is used

## 7. Documentation

- [x] 7.1 Update README with three-phase workflow examples
- [x] 7.2 Update QUICK_START.md with remediation-only usage
- [x] 7.3 Update CONFIGURATION_GUIDE.md if needed
