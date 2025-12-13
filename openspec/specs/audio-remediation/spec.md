# audio-remediation Specification

## Purpose
TBD - created by archiving change add-audio-detection. Update Purpose after archive.
## Requirements
### Requirement: Audio Silence Remediation

The system SHALL apply silence (zero amplitude) to detected audio segments when remediation is enabled and silence mode is selected.

#### Scenario: Silence profanity segment
- **WHEN** profanity is detected at timecodes 10.5-11.0 and remediation mode is "silence" with categories=["Profanity"]
- **THEN** audio samples from 10.5 to 11.0 seconds are zeroed (muted) in remediated output

#### Scenario: Skip categories not in remediation list
- **WHEN** profanity (10.5-11.0) and violence (12.0-12.5) are detected, but remediation categories=["Profanity"]
- **THEN** profanity is silenced; violence sound remains unchanged

#### Scenario: Handle overlapping detections
- **WHEN** multiple overlapping detections target same audio segment
- **THEN** segment is silenced once (no double-processing)

#### Scenario: Preserve audio sample rate
- **WHEN** audio is silenced and written to file
- **THEN** output file has same sample rate as input (typically 16 kHz)

### Requirement: Audio Bleep Remediation

The system SHALL apply a tone (sine wave) to detected audio segments when remediation is enabled and bleep mode is selected.

#### Scenario: Generate bleep tone for profanity
- **WHEN** profanity is detected at timecodes 10.5-11.0 and remediation mode is "bleep"
- **THEN** audio samples from 10.5 to 11.0 seconds are replaced with sine wave at configured frequency (default 1000 Hz)

#### Scenario: Configure bleep frequency
- **WHEN** remediation config specifies bleep_frequency=800
- **THEN** bleep tone is generated at 800 Hz instead of default 1000 Hz

#### Scenario: Bleep amplitude is reasonable
- **WHEN** bleep tone is generated
- **THEN** amplitude is set to 0.2 (peak) to avoid clipping and ensure audibility

#### Scenario: Bleep tone covers full detection duration
- **WHEN** detection spans 0.5 seconds at 16 kHz
- **THEN** bleep tone is exactly 8000 samples (0.5 × 16000), filling the entire duration

### Requirement: Per-Category Remediation Control

The system SHALL allow users to specify which detection categories to remediate, enabling selective censoring.

#### Scenario: Remediate only profanity
- **WHEN** config specifies remediation categories=["Profanity"]
- **THEN** only profanity detections are silenced/bleeped; violence, sexual content, etc. are left unchanged

#### Scenario: Remediate multiple categories
- **WHEN** config specifies remediation categories=["Profanity", "Sexual Theme"]
- **THEN** both profanity and sexual content are remediated; other categories unaffected

#### Scenario: Remediate all detected categories
- **WHEN** config specifies remediation categories=["Profanity", "Violence", "Sexual Theme"]
- **THEN** all detected inappropriate audio is censored

#### Scenario: Empty remediation categories
- **WHEN** config specifies remediation enabled=true but categories=[]
- **THEN** no audio is remediated; detections are still recorded

### Requirement: Remediated Audio Output

The system SHALL write remediated audio to a separate output file, allowing users to test before integration.

#### Scenario: Write remediated audio to file
- **WHEN** remediation is enabled and analysis completes
- **THEN** remediated audio is written to configured output_path (e.g., "./remediated_audio.wav")

#### Scenario: Use configured output path
- **WHEN** remediation config specifies output_path="/path/to/custom_audio.wav"
- **THEN** remediated audio is written to that exact path

#### Scenario: Output file format is WAV
- **WHEN** remediated audio is written
- **THEN** output file is in WAV format with same sample rate as input (16 kHz)

#### Scenario: Overwrite existing output file
- **WHEN** output file already exists
- **THEN** existing file is overwritten with new remediated audio

#### Scenario: Include output path in results
- **WHEN** remediation is enabled and completes
- **THEN** detection results include `remediated_audio_path` field with path to output file

### Requirement: Remediation Configuration

The system SHALL accept YAML configuration specifying remediation mode, categories, and output options.

#### Scenario: Remediation disabled by default
- **WHEN** user provides config without remediation section
- **THEN** remediation is disabled; no output file written

#### Scenario: Enable silence mode
- **WHEN** config specifies `audio.remediation.mode: "silence"`
- **THEN** detected audio is silenced (not bleeped)

#### Scenario: Enable bleep mode
- **WHEN** config specifies `audio.remediation.mode: "bleep"`
- **THEN** detected audio is bleped with tone

#### Scenario: Validate remediation config
- **WHEN** config specifies invalid mode (e.g., "buzz" instead of "silence"/"bleep")
- **THEN** system raises ConfigError during pipeline initialization

#### Scenario: Categories must be valid
- **WHEN** config specifies unknown category (e.g., "GoreMeter" which doesn't exist)
- **THEN** system logs warning but allows config to load; unknown category is ignored during remediation

### Requirement: Audio Remediation Error Handling

The system SHALL handle audio processing errors gracefully without stopping analysis.

#### Scenario: Handle audio file write failure
- **WHEN** remediated audio write fails (disk full, permission denied)
- **THEN** error is logged; detection results are still returned; pipeline notes remediation failure

#### Scenario: Continue on bleep generation failure
- **WHEN** bleep tone generation fails (OOM, invalid parameters)
- **THEN** error is logged; detection segments are left unchanged; analysis continues

#### Scenario: Handle invalid detection timecodes
- **WHEN** detection has invalid timecode (greater than video duration or negative)
- **THEN** detection is skipped with warning; other detections remediated normally

