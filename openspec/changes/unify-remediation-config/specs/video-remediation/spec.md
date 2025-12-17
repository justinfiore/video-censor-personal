## MODIFIED Requirements

### Requirement: Video Remediation Configuration

The system SHALL accept YAML configuration specifying video remediation default mode, categories, and options under the `remediation.video` section.

#### Scenario: Video remediation disabled by default
- **WHEN** user provides config without `remediation.video` section
- **THEN** video remediation is disabled; video output is unchanged (audio may still be remediated)

#### Scenario: Enable with blank as global default mode
- **WHEN** config specifies `remediation.video.enabled: true` and `mode: "blank"`
- **THEN** segments without category or segment override are blanked with black screen

#### Scenario: Enable with cut as global default mode
- **WHEN** config specifies `remediation.video.enabled: true` and `mode: "cut"`
- **THEN** segments without category or segment override are removed entirely

#### Scenario: Global default mode when not specified
- **WHEN** config specifies `remediation.video.enabled: true` but omits `mode`
- **THEN** global default mode is "blank" (safer option that preserves timing)

#### Scenario: Configure category_modes
- **WHEN** config specifies `category_modes: { Nudity: "cut", Violence: "blank" }`
- **THEN** category defaults are applied before falling back to global default

#### Scenario: Validate category_modes values
- **WHEN** config specifies `category_modes: { Nudity: "blur" }` (invalid mode)
- **THEN** system raises ConfigError during pipeline initialization

#### Scenario: Configure blank_color
- **WHEN** config specifies `blank_color: "#FF0000"` (red)
- **THEN** blank frames use red color instead of black

#### Scenario: Validate blank_color format
- **WHEN** config specifies `blank_color: "invalid-color"`
- **THEN** system raises ConfigError with helpful message about hex color format
