## ADDED Requirements

### Requirement: Remediation-Only Mode via Input Segments

The system SHALL support a remediation-only mode that skips all analysis and loads detection segments from an existing JSON file, enabling decoupled three-phase workflows.

#### Scenario: CLI accepts --input-segments argument
- **WHEN** user runs `python -m video_censor --input video.mp4 --input-segments segments.json --output-video output.mp4 --config config.yaml`
- **THEN** CLI parses `--input-segments` argument with the path to existing segments JSON

#### Scenario: Skip analysis when --input-segments is provided
- **WHEN** `--input-segments` is provided
- **THEN** system MUST NOT initialize `AnalysisPipeline`
- **AND** system MUST NOT run any detection (vision models, audio analysis, etc.)
- **AND** system loads segments directly from the specified JSON file

#### Scenario: Proceed to remediation with loaded segments
- **WHEN** segments are loaded from JSON file
- **THEN** system proceeds to remediation phase based on config settings
- **AND** all remediation modes work (audio bleep/silence, skip chapters)

#### Scenario: Validate --input-segments requires --input
- **WHEN** user provides `--input-segments` without `--input` video file
- **THEN** system exits with error: `"--input-segments requires --input video file for remediation"`

#### Scenario: Warn when --output is specified with --input-segments
- **WHEN** user provides `--input-segments` alongside `--output` (JSON output path)
- **THEN** system logs warning: `"--output is ignored in remediation mode; segments are loaded from --input-segments, not generated"`
- **AND** no new JSON output is written

### Requirement: Segments JSON File Loading

The system SHALL load and validate pre-existing segments JSON files for use in remediation-only mode.

#### Scenario: Load valid segments JSON
- **WHEN** valid segments JSON file is provided via `--input-segments`
- **THEN** system parses JSON and extracts `segments` array
- **AND** each segment retains all properties: `start_time`, `end_time`, `labels`, `confidence`, `allow`, etc.

#### Scenario: Validate JSON structure
- **WHEN** JSON file is missing required `segments` array
- **THEN** system exits with error: `"Invalid segments file: missing 'segments' array"`

#### Scenario: Handle malformed JSON
- **WHEN** JSON file is syntactically invalid
- **THEN** system exits with error: `"Failed to parse segments file: <json error details>"`

#### Scenario: Handle missing file
- **WHEN** `--input-segments` path does not exist
- **THEN** system exits with error: `"Segments file not found: <path>"`

### Requirement: Input Video Validation Against Segments

The system SHALL validate that the segments JSON file matches the input video to prevent accidental misuse.

#### Scenario: Warn on filename mismatch
- **WHEN** `metadata.file` in segments JSON does not match input video filename
- **THEN** system logs warning: `"Warning: Segments file was generated for '<metadata.file>' but input video is '<actual filename>'. Proceeding anyway."`
- **AND** remediation continues (non-fatal warning)

#### Scenario: Optional duration validation
- **WHEN** `metadata.duration` is present in segments JSON
- **THEN** system compares against input video duration
- **AND** if difference exceeds 1 second, logs warning: `"Warning: Video duration mismatch. Segments: <X>, Video: <Y>"`
- **AND** remediation continues (non-fatal warning)

#### Scenario: Missing metadata is acceptable
- **WHEN** segments JSON has no `metadata` section (e.g., manually created)
- **THEN** system skips validation and proceeds with remediation
