## 1. CLI Argument Addition

- [ ] 1.1 Add `--input-segments <path>` argument to CLI parser
- [ ] 1.2 Update CLI help text with usage examples
- [ ] 1.3 Add validation: `--input-segments` requires `--input` video file
- [ ] 1.4 Add validation: warn when `--output` (JSON) is specified with `--input-segments`

## 2. Segments JSON Loading

- [ ] 2.1 Create `load_segments_from_json(path)` function
- [ ] 2.2 Parse JSON and validate required structure (metadata, segments array)
- [ ] 2.3 Return structured segment data compatible with existing remediation pipeline

## 3. Input Validation

- [ ] 3.1 Validate `metadata.file` matches input video filename (warning if mismatch)
- [ ] 3.2 Optionally validate `metadata.duration` matches video duration (within 1s tolerance)
- [ ] 3.3 Fail gracefully with clear error message if JSON is malformed or unreadable

## 4. Main Entry Point Integration

- [ ] 4.1 Detect `--input-segments` mode in main entry point
- [ ] 4.2 Skip `AnalysisPipeline` initialization and analysis when in segments mode
- [ ] 4.3 Load segments from JSON instead of running detection
- [ ] 4.4 Pass loaded segments directly to remediation phase

## 5. Remediation Phase Integration

- [ ] 5.1 Ensure audio remediation works with loaded segments
- [ ] 5.2 Ensure skip chapters generation works with loaded segments
- [ ] 5.3 Ensure `"allow": true` segments are skipped during remediation
- [ ] 5.4 Ensure `--allow-all-segments` flag is ignored in remediation mode

## 6. Testing

- [ ] 6.1 Unit test: `--input-segments` parses correctly
- [ ] 6.2 Unit test: JSON loading validates structure
- [ ] 6.3 Unit test: metadata validation warns on mismatch
- [ ] 6.4 Integration test: remediation-only workflow produces expected output
- [ ] 6.5 Integration test: allow overrides are respected in remediation mode
- [ ] 6.6 Integration test: `--allow-all-segments` is ignored when `--input-segments` is used

## 7. Documentation

- [ ] 7.1 Update README with three-phase workflow examples
- [ ] 7.2 Update QUICK_START.md with remediation-only usage
- [ ] 7.3 Update CONFIGURATION_GUIDE.md if needed
