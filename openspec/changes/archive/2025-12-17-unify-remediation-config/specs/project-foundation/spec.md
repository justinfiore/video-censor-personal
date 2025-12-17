## MODIFIED Requirements

### Requirement: Command-Line Interface

The system SHALL provide a command-line interface with required arguments for input, config, and output paths, as well as optional arguments for video output and segment filtering.

#### Scenario: Add --output-video CLI argument
- **WHEN** user runs main entry point
- **THEN** `--output-video` argument is available to accept output video path

#### Scenario: Output-video is optional when remediation disabled
- **WHEN** user does not provide `--output-video` and both audio and video remediation are disabled
- **THEN** argument is optional; analysis proceeds without video output

#### Scenario: Fail-fast if remediation enabled without output-video
- **WHEN** config has `remediation.audio.enabled: true` or `remediation.video.enabled: true` but `--output-video` is not provided
- **THEN** system exits immediately with exit code 1 (before analysis begins)
- **AND** error message clearly explains:
  - Which remediation is enabled in config
  - `--output-video` argument is required
  - Example command showing correct usage
  - Alternative: how to disable remediation in config

#### Scenario: Fail-fast if output-video provided but remediation disabled
- **WHEN** user provides `--output-video` but both audio and video remediation are disabled in config
- **THEN** system exits immediately with exit code 1 (before analysis begins)
- **AND** error message clearly explains:
  - `--output-video` was provided but no remediation is enabled
  - Either enable `remediation.audio` or `remediation.video` in config
  - Or remove `--output-video` argument
