## ADDED Requirements

### Requirement: GPU Device Support for Audio Detectors

The system SHALL automatically detect and use available GPU acceleration for audio model inference, falling back to CPU when no GPU is available.

#### Scenario: AudioClassificationDetector uses GPU
- **WHEN** AudioClassificationDetector initializes with GPU available
- **THEN** model is loaded and moved to available GPU device

#### Scenario: SpeechProfanityDetector uses GPU
- **WHEN** SpeechProfanityDetector initializes with GPU available
- **THEN** transformers pipeline is configured with GPU device

#### Scenario: Fallback to CPU for audio detectors
- **WHEN** no GPU is available
- **THEN** audio models run on CPU

#### Scenario: Device logged at startup
- **WHEN** audio detector initializes
- **THEN** selected device is logged at INFO level

### Requirement: Configurable Device Override for Audio Detectors

The system SHALL allow users to override automatic device detection via configuration for audio detectors.

#### Scenario: Manual device selection
- **WHEN** audio detector config includes `device` option
- **THEN** detector uses specified device instead of auto-detection

#### Scenario: Audio tensor device placement
- **WHEN** audio detector processes audio data
- **THEN** input tensors are moved to model's device before inference
