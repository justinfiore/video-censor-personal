## MODIFIED Requirements

### Requirement: Configuration File Parsing

The system SHALL parse and validate YAML configuration files before processing, enforcing both structural and semantic constraints.

#### Scenario: Valid configuration load
- **WHEN** user provides valid YAML config file with required fields and semantically valid values
- **THEN** configuration is loaded and validated successfully

#### Scenario: Invalid YAML syntax
- **WHEN** user provides YAML file with syntax errors
- **THEN** system reports parse error with line number and helpful message

#### Scenario: Missing required fields
- **WHEN** configuration file is missing required fields (e.g., `detections`, `processing`, `output`)
- **THEN** system reports validation error listing missing fields

#### Scenario: Default configuration fallback
- **WHEN** no config file specified and default location exists
- **THEN** system loads configuration from default location (e.g., `./video-censor.yaml`)

#### Scenario: Detection sensitivity out of range
- **WHEN** a detection category specifies `sensitivity` value outside [0.0, 1.0]
- **THEN** system raises ConfigError indicating valid range and the invalid value provided

#### Scenario: Detection category missing required fields
- **WHEN** a detection category under `detections.<name>` is missing `enabled`, `sensitivity`, or `model` field
- **THEN** system raises ConfigError naming the missing field and detection category

#### Scenario: No detection categories enabled
- **WHEN** configuration has detection categories defined but none have `enabled: true`
- **THEN** system raises ConfigError indicating at least one detection must be enabled

#### Scenario: Invalid output format
- **WHEN** `output.format` is set to unsupported value (e.g., "csv", "xml")
- **THEN** system raises ConfigError indicating only "json" is currently supported

#### Scenario: Invalid frame sampling strategy
- **WHEN** `processing.frame_sampling.strategy` is set to value other than "uniform", "scene_based", or "all"
- **THEN** system raises ConfigError listing valid strategies

#### Scenario: Invalid max_workers value
- **WHEN** `processing.max_workers` is set to value ≤ 0
- **THEN** system raises ConfigError indicating max_workers must be a positive integer

#### Scenario: Invalid merge_threshold value
- **WHEN** `processing.segment_merge.merge_threshold` is set to negative value
- **THEN** system raises ConfigError indicating merge_threshold must be non-negative
