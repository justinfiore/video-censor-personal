## MODIFIED Requirements

### Requirement: Audio Support Infrastructure

The system SHALL support passing audio data to detectors (both visual and audio-based detectors) via the analysis pipeline, enabling multi-modal detection on the same content.

#### Scenario: Extract and cache audio at pipeline start
- **WHEN** pipeline detects audio-capable detectors in configuration
- **THEN** audio is extracted once at pipeline initialization and cached for frame-level slicing

#### Scenario: Pass audio segments to detectors per frame
- **WHEN** frame is analyzed and audio detectors are configured
- **THEN** audio segment (matching frame timecode) is passed to detector.detect() alongside frame data

#### Scenario: Audio extraction failure does not halt pipeline
- **WHEN** audio extraction fails (missing audio, unsupported codec, I/O error)
- **THEN** warning is logged; pipeline continues with visual-only detection; audio_data=None passed to detectors

#### Scenario: Detector handles missing audio gracefully
- **WHEN** video has no audio but audio detector is configured
- **THEN** detector receives audio_data=None; detector either skips audio analysis or returns empty results

#### Scenario: Visual-only detectors skip audio parameter
- **WHEN** detector is visual-only (does not use audio_data)
- **THEN** audio_data parameter is ignored; detector continues as before

#### Scenario: Audio-visual detectors use both modalities
- **WHEN** multi-modal detector receives both frame_data and audio_data
- **THEN** detector can fuse information (e.g., violence detection from motion + impact sound)

#### Scenario: Cleanup releases cached audio
- **WHEN** pipeline analysis completes or cleanup() is called
- **THEN** cached audio is released from memory
