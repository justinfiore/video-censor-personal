# remediation-mode-none Specification

## Purpose

Provides support for a "none" mode in video and audio remediation configuration, allowing users to explicitly skip remediation for specific content categories while applying different modes (blank/cut/bleep/silence) to others. This enables selective and granular control over which content types are remediated and how.

## Requirements

### Requirement: None Mode Support

The system SHALL support a "none" mode for both audio and video remediation that completely skips processing for configured categories.

#### Scenario: Video none mode skips remediation
- **WHEN** video remediation is enabled with `category_modes: { Violence: "none" }`
- **THEN** violence segments are completely excluded from video remediation (no blanking or cutting)

#### Scenario: Audio none mode skips remediation
- **WHEN** audio remediation is enabled with `categories: ["Profanity"]` and a segment is labeled only with "Violence"
- **THEN** violence segment audio is not remediated (not silenced or bleeped)

#### Scenario: Global default none mode
- **WHEN** config specifies `remediation.video.mode: "none"` as global default
- **THEN** all segments use none mode unless overridden by category or segment-level config

#### Scenario: None mode in category_modes
- **WHEN** config specifies `remediation.video.category_modes: { Profanity: "none", Violence: "cut" }`
- **THEN** profanity segments skip video remediation; violence segments are cut

#### Scenario: None mode in per-segment override
- **WHEN** segment has `"video_remediation": "none"`
- **THEN** that specific segment is not remediated regardless of category or global defaults

### Requirement: Mode Precedence with None

The system SHALL implement correct precedence when a segment has multiple labels with different modes, treating "none" as the least restrictive.

#### Scenario: Cut takes precedence over none
- **WHEN** segment has labels ["Nudity", "Violence"] with `category_modes: { Nudity: "cut", Violence: "none" }`
- **THEN** segment is cut (cut is more restrictive than none)

#### Scenario: Blank takes precedence over none
- **WHEN** segment has labels ["Profanity", "Violence"] with `category_modes: { Profanity: "blank", Violence: "none" }`
- **THEN** segment is blanked (blank is more restrictive than none)

#### Scenario: None with multiple none labels
- **WHEN** segment has labels ["Violence", "Weapons"] with `category_modes: { Violence: "none", Weapons: "none" }`
- **THEN** segment uses none mode (no remediation applied)

#### Scenario: Precedence order
- **WHEN** resolving mode for segments with mixed labels
- **THEN** precedence is: cut > blank > none (most to least restrictive)

### Requirement: None Mode Filtering

The system SHALL exclude segments with mode "none" from all remediation processing, ensuring no unnecessary computation or quality degradation.

#### Scenario: None segments excluded from video grouping
- **WHEN** segments are grouped for video remediation and some have mode "none"
- **THEN** none-mode segments are completely excluded from blank and cut processing groups

#### Scenario: None segments excluded from audio processing
- **WHEN** audio remediation processes segments and label is not in categories
- **THEN** segment is skipped (equivalent to none mode)

#### Scenario: Allow flag does not affect none filtering
- **WHEN** segment has `"allow": false` AND `"video_remediation": "none"`
- **THEN** segment is still excluded from remediation (mode filtering occurs after allow filtering)

#### Scenario: Performance efficiency
- **WHEN** many segments have mode "none"
- **THEN** none-mode segments impose zero processing overhead (not encoded, not concatenated)

### Requirement: Mixed Category Remediation

The system SHALL correctly handle segments with multiple content category labels when some categories are remediated and others are not.

#### Scenario: Multi-label segment with selective remediation
- **WHEN** segment has labels ["Profanity", "Violence"] and audio remediation categories=["Profanity"]
- **THEN** audio is remediated for profanity (if enabled); violence is ignored

#### Scenario: Video and audio independent remediation
- **WHEN** audio config has `categories: ["Profanity"]` and video config has `category_modes: { Violence: "none" }`
- **THEN** audio and video remediation operate independently on their respective configs

#### Scenario: Multi-label with different video modes
- **WHEN** segment has labels ["Nudity", "Violence"] with `category_modes: { Nudity: "cut", Violence: "none" }`
- **THEN** segment is cut (most restrictive mode wins)

#### Scenario: Some labels remediated, others not
- **WHEN** segment has labels ["Profanity", "Violence"] and only Violence is configured for remediation
- **THEN** only violence remediation logic applies; profanity label is ignored

### Requirement: Configuration Validation

The system SHALL validate that "none" is accepted as a valid remediation mode in all configuration tiers.

#### Scenario: Video global default accepts none
- **WHEN** config specifies `remediation.video.mode: "none"`
- **THEN** configuration is valid and processed correctly

#### Scenario: Category mode accepts none
- **WHEN** config specifies `remediation.video.category_modes: { Violence: "none" }`
- **THEN** configuration is valid and processed correctly

#### Scenario: Valid mode values
- **WHEN** validating remediation mode configuration
- **THEN** accepted values are: "blank", "cut", "none" for video; "silence", "bleep" for audio

#### Scenario: Invalid mode rejected
- **WHEN** config specifies `remediation.video.mode: "blur"` (invalid)
- **THEN** system raises ConfigError with message listing valid options

### Requirement: Analysis Pipeline Integration

The system SHALL apply none mode correctly when running detection and remediation together in analysis mode.

#### Scenario: None mode in analysis pipeline
- **WHEN** running analysis with config containing `category_modes: { Weapons: "none" }`
- **THEN** weapons segments are detected but not remediated in output

#### Scenario: Detections recorded regardless of mode
- **WHEN** segment has mode "none"
- **THEN** detection is still recorded in output JSON with full metadata

### Requirement: Remediation-Only Mode Integration

The system SHALL apply none mode correctly when using `--input-segments` with pre-existing detections (remediation-only mode).

#### Scenario: None mode in remediation-only mode
- **WHEN** running with `--input-segments` and config has `category_modes: { Profanity: "none" }`
- **THEN** profanity segments in input JSON are not remediated in output

#### Scenario: Allow flag respected in remediation-only
- **WHEN** input segment has `"allow": true`
- **THEN** segment is skipped regardless of mode configuration

#### Scenario: Video remediation applied in remediation-only
- **WHEN** running with `--input-segments` and video remediation config
- **THEN** video remediation is applied with none mode filtering

### Requirement: None Mode Documentation and Examples

The system configuration documentation SHALL include comprehensive examples and use cases for "none" mode.

#### Scenario: Audio-only remediation example
- **WHEN** user wants to bleep profanity but not modify video
- **THEN** config can specify `remediation.video.mode: "none"` with audio bleep enabled

#### Scenario: Selective cutting example
- **WHEN** user wants to cut only nudity and sexual content
- **THEN** config specifies `remediation.video.mode: "none"` with `category_modes: { Nudity: "cut", Sexual Theme: "cut" }`

#### Scenario: Mixed modes example
- **WHEN** user wants different remediation per category
- **THEN** config can specify default mode with category-level and segment-level overrides

### Requirement: None Mode Testing Coverage

The system SHALL include comprehensive test coverage for none mode scenarios.

#### Scenario: Audio none mode test
- **WHEN** testing audio remediation with mixed categories
- **THEN** segments not in categories are not remediated

#### Scenario: Video none mode test
- **WHEN** testing video remediation with `category_modes` containing "none"
- **THEN** none-mode segments are excluded from blank and cut groups

#### Scenario: Mode precedence test
- **WHEN** testing segments with multiple labels and mixed modes
- **THEN** most restrictive mode is correctly selected

#### Scenario: Mixed category test
- **WHEN** testing segment with multiple labels and selective remediation
- **THEN** each system (audio/video) correctly applies its independent config

#### Scenario: Integration test
- **WHEN** running full pipeline with none mode config
- **THEN** detections are recorded; output has correct remediation applied

### Requirement: Backward Compatibility

The system SHALL maintain full backward compatibility with existing configurations that do not use "none" mode.

#### Scenario: Existing config unchanged
- **WHEN** using config without "none" mode
- **THEN** behavior is identical to pre-none-mode version

#### Scenario: Default mode not affected
- **WHEN** no mode specified in config
- **THEN** system uses existing defaults (blank for video)

#### Scenario: Existing tests pass
- **WHEN** running existing test suite
- **THEN** all tests pass without modification

#### Scenario: Optional feature
- **WHEN** deploying none mode feature
- **THEN** existing users are unaffected; feature is opt-in via configuration
