## MODIFIED Requirements

### Requirement: Remediation Configuration

The system SHALL accept YAML configuration specifying remediation mode, categories, and output options under the `remediation.audio` section.

#### Scenario: Remediation disabled by default
- **WHEN** user provides config without `remediation.audio` section
- **THEN** remediation is disabled; no output file written

#### Scenario: Enable silence mode
- **WHEN** config specifies `remediation.audio.mode: "silence"`
- **THEN** detected audio is silenced (not bleeped)

#### Scenario: Enable bleep mode
- **WHEN** config specifies `remediation.audio.mode: "bleep"`
- **THEN** detected audio is bleeped with tone

#### Scenario: Validate remediation config
- **WHEN** config specifies invalid mode (e.g., "buzz" instead of "silence"/"bleep")
- **THEN** system raises ConfigError during pipeline initialization

#### Scenario: Categories must be valid
- **WHEN** config specifies `remediation.audio.categories: ["InvalidCategory"]`
- **THEN** system validates categories match enabled detection categories
