## MODIFIED Requirements

### Requirement: JSON Output Segment Structure
The system SHALL generate JSON output with detected video segments, where each segment contains temporal bounds, classification labels, confidence scores, detection details, and an optional allow override flag for user remediation control.

#### Scenario: Standard segment without allow override
- **WHEN** analysis completes and a segment is detected
- **THEN** the segment SHALL include `start_time`, `end_time`, `duration_seconds`, `labels`, `confidence`, `description`, and `detections` array
- **AND** the segment MUST NOT include an `allow` property (equivalent to `allow: false`)
- **AND** this segment will be eligible for remediation (audio bleep/silence, chapters)

#### Scenario: Segment marked as allowed (false positive)
- **WHEN** a user manually adds `"allow": true` to a segment in the JSON file
- **THEN** the segment's original detection data (`labels`, `confidence`, `description`, `detections`) SHALL be preserved unchanged
- **AND** this segment MUST be excluded from all downstream remediation processing
- **AND** the user can change the allow flag without re-analyzing the video

#### Scenario: Segment explicitly marked as not allowed
- **WHEN** a user sets `"allow": false` on a segment
- **THEN** the segment SHALL be treated identically to segments without an allow property
- **AND** this segment will be eligible for remediation

#### Scenario: JSON schema validation with allow property
- **WHEN** the system processes a JSON file containing segments with `allow` property
- **THEN** the `allow` value SHALL be a boolean (`true` or `false`)
- **AND** missing `allow` property SHALL be treated as `false` for backward compatibility
- **AND** non-boolean values for `allow` MUST cause validation error

#### Scenario: Backward compatibility with existing JSON files
- **WHEN** an existing JSON file from prior analysis (without `allow` property) is used as input
- **THEN** all segments MUST be treated as `allow: false` (eligible for remediation)
- **AND** the system SHALL NOT fail due to missing `allow` property

## ADDED Requirements

### Requirement: Bulk Allow Override via CLI Flag
The system SHALL support a `--allow-all-segments` CLI flag that automatically marks all detected segments as allowed during the analysis phase.

#### Scenario: Analysis with --allow-all-segments flag
- **WHEN** analysis is run with `--allow-all-segments` flag
- **THEN** all detected segments in the output JSON SHALL have `"allow": true`
- **AND** original detection data (`labels`, `confidence`, `description`, `detections`) MUST be preserved
- **AND** this is purely a convenience feature for pre-populating the allow status during analysis

#### Scenario: Flag has no effect during remediation
- **WHEN** `--allow-all-segments` flag is provided alongside `--input-segments` (remediation phase)
- **THEN** the flag MUST be ignored
- **AND** segments will use their existing `allow` property values from the input JSON

#### Scenario: Use case - preview mode analysis
- **WHEN** user wants to analyze a video without intending to remediate yet
- **THEN** they can use `--allow-all-segments` during analysis to prevent accidental remediation
- **AND** they can later un-allow specific segments by setting `"allow": false` and running remediation
