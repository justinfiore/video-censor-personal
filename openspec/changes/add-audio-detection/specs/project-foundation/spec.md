## MODIFIED Requirements

### Requirement: Command-Line Interface

The system SHALL accept `--output-video` argument and validate it against audio remediation configuration.

#### Scenario: Add --output-video CLI argument
- **WHEN** user runs main entry point
- **THEN** `--output-video` argument is available to accept output video path

#### Scenario: Output-video is optional when remediation disabled
- **WHEN** user does not provide `--output-video` and audio remediation is disabled
- **THEN** argument is optional; analysis proceeds without video output

#### Scenario: Fail-fast if remediation enabled without output-video
- **WHEN** config has `audio.remediation.enabled: true` but `--output-video` is not provided
- **THEN** system exits immediately with exit code 1 (before analysis begins)
- **AND** error message clearly explains:
  - Audio remediation is enabled in config
  - `--output-video` argument is required
  - Example command showing correct usage
  - Alternative: how to disable remediation in config

#### Scenario: Fail-fast if output-video provided but remediation disabled
- **WHEN** user provides `--output-video` but audio remediation is disabled in config
- **THEN** system exits immediately with exit code 1 (before analysis begins)
- **AND** error message clearly explains:
  - `--output-video` requires audio remediation to be enabled
  - Enable remediation in config or remove the `--output-video` argument
  - No video file is written if remediation is not enabled

#### Scenario: Validate output-video path is writable
- **WHEN** user provides `--output-video` with path in non-existent directory
- **THEN** system raises error indicating directory does not exist

#### Scenario: Config is reusable across runs
- **WHEN** same config is used with different `--output-video` paths
- **THEN** config file contains no hardcoded paths
- **AND** remediation output path is determined by CLI argument, not config

#### Scenario: Help text documents output-video
- **WHEN** user runs with `--help`
- **THEN** help text includes `--output-video` description:
  - Purpose (output video path for audio remediation)
  - Note that it's required if remediation enabled
  - Example usage
