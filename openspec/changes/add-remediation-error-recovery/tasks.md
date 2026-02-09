## 1. Error Pattern Registry and Diagnostics Module

- [ ] 1.1 Create `video_censor_personal/remediation_diagnostics.py` with:
  - `FileOrigin` enum (`USER_INPUT`, `PIPELINE_INTERMEDIATE`)
  - `ErrorPattern` dataclass (regex, diagnosis_template, suggested_fix, recovery_strategy, typical_origin)
  - `Diagnosis` dataclass (pattern, diagnosis, suggested_fix, file_path, file_origin, recovery_strategy)
- [ ] 1.2 Define error pattern registry list with all known patterns:
  - moov atom not found
  - Invalid data found when processing input
  - non-existing PPS / decode_slice_header error / no frame (corrupt H.264)
  - Non-monotonous DTS in output stream
  - Could not write header / incorrect codec parameters
  - No space left on device
  - Permission denied
  - PES packet size mismatch
  - Unknown encoder / Encoder not found
  - Empty output file (0 bytes)
- [ ] 1.3 Implement `diagnose_error(stderr: str, file_path: str, file_origin: FileOrigin) -> Diagnosis` that matches stderr against registry and tailors message based on origin
- [ ] 1.4 Implement `check_output_file(path: str) -> Optional[Diagnosis]` for detecting empty/missing output
- [ ] 1.5 Write unit tests for each known error pattern diagnosis (both user-input and pipeline-intermediate variants)

## 2. Bug Report Generator

- [ ] 2.1 Implement `generate_bug_report(phase: str, error_msg: str, file_path: str, command: str, config_file: str, input_file: str) -> str` that produces a copy-pasteable GitHub issue (title + description) with:
  - ffmpeg version (detected at runtime)
  - OS/platform info
  - Python version
  - Link to https://github.com/justinfiore/video-censor-personal/issues
- [ ] 2.2 Store the original CLI command in `RemediationManager` for inclusion in bug reports
- [ ] 2.3 Write tests for bug report formatting

## 3. Warnings Collector

- [ ] 3.1 Add `warnings` list to `RemediationManager` storing structured objects (phase, message, file_origin, bug_report)
- [ ] 3.2 Add `add_warning(phase: str, message: str, file_origin: FileOrigin, bug_report: Optional[str])` method
- [ ] 3.3 Add `get_warnings_summary() -> Optional[str]` that formats all warnings and appends any bug reports at the end
- [ ] 3.4 Write tests for warnings collection, summary formatting, and bug report inclusion

## 4. Recovery Strategies

- [ ] 4.1 Implement recovery for metadata application: skip metadata on corrupt intermediate, preserve output, generate bug report
- [ ] 4.2 Implement recovery for muxing: retry with re-encoding (`-c:v libx264 -c:a aac`) if stream copy fails
- [ ] 4.3 Implement recovery for video remediation: retry with `-err_detect ignore_err` for corrupt frames, generate bug report (intermediate)
- [ ] 4.4 Implement recovery for timestamp disorder: retry with `-fflags +genpts`
- [ ] 4.5 Implement recovery for codec header mismatch: retry with explicit re-encoding
- [ ] 4.6 Write tests for each recovery strategy (both source-attribution paths)

## 5. Integration

- [ ] 5.1 Pass `FileOrigin.USER_INPUT` in `_apply_audio_remediation()` and `_mux_remediated_audio()` (for the original video input)
- [ ] 5.2 Pass `FileOrigin.PIPELINE_INTERMEDIATE` in `_apply_video_remediation()` and `_apply_final_metadata()` (for pipeline-produced files)
- [ ] 5.3 Wire diagnostics + recovery + bug report generation into all four phase error handlers in `remediation.py`
- [ ] 5.4 Store original CLI command (sys.argv) in `RemediationManager` for bug reports
- [ ] 5.5 Print warnings summary (including bug reports) at end of processing in CLI main (`video_censor_personal.py`)
- [ ] 5.6 Write integration test: simulate intermediate file corruption → verify diagnosis attributes it to pipeline, recovery attempted, bug report generated

## 6. Documentation

- [ ] 6.1 Update `VIDEO_PROCESSING_ERROR_DETECTION_AND_REMEDIATION.md` with source attribution and bug report sections
- [ ] 6.2 Update brief description in README.md if needed
