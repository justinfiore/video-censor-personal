## MODIFIED Requirements

### Requirement: Segment Allow Override

The system SHALL support an optional `allow` property on segments to enable users to exclude false-positive detections from remediation without re-analyzing video.

#### Scenario: Segment includes allow property
- **WHEN** output is generated
- **THEN** each segment includes boolean `allow` property (defaults to false)

#### Scenario: Allowed segment default is false
- **WHEN** detection is processed
- **THEN** segment is initialized with `"allow": false` by default

#### Scenario: Manual override with allow true
- **WHEN** user edits output JSON to set `"allow": true` for false-positive segment(s)
- **THEN** system accepts the modified JSON for remediation use

#### Scenario: Allow flag excludes from remediation
- **WHEN** audio remediation processes segments with `"allow": true`
- **THEN** those segments are skipped (audio not modified)

#### Scenario: Allow flag excludes from chapters
- **WHEN** chapter generation processes segments with `"allow": true`
- **THEN** those segments do not generate chapter markers

#### Scenario: Allow-all-segments CLI flag
- **WHEN** analysis is run with `--allow-all-segments` flag
- **THEN** all detected segments are automatically set to `"allow": true` in output JSON
- **AND** flag only applies during analysis phase (no effect when using `--input-segments` for remediation)

#### Scenario: Allow-all-segments flag ignored in remediation mode
- **WHEN** `--allow-all-segments` flag is provided alongside `--input-segments`
- **THEN** the flag is ignored
- **AND** segments use their existing `allow` property values from the loaded JSON file
- **AND** system logs info: `"--allow-all-segments ignored in remediation mode; using allow values from input segments"`

## MODIFIED Requirements

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
- **AND** system logs info: `"--allow-all-segments ignored in remediation mode; using allow values from input segments"`

#### Scenario: Use case - preview mode analysis
- **WHEN** user wants to analyze a video without intending to remediate yet
- **THEN** they can use `--allow-all-segments` during analysis to prevent accidental remediation
- **AND** they can later un-allow specific segments by setting `"allow": false` and running remediation
