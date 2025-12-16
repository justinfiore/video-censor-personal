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
