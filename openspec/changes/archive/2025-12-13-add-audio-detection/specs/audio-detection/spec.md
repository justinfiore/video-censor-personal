## ADDED Requirements

### Requirement: Audio Extraction and Caching

The system SHALL extract audio from video once and cache it in memory for reuse across detectors, avoiding repeated expensive I/O operations.

#### Scenario: Extract audio on first call
- **WHEN** AudioExtractor is called with video path
- **THEN** audio is extracted using ffmpeg or librosa and cached in memory

#### Scenario: Return cached audio on subsequent calls
- **WHEN** AudioExtractor.extract() is called a second time
- **THEN** cached audio is returned without re-extraction

#### Scenario: Resample audio to 16kHz standard
- **WHEN** extracted audio has different sample rate than 16kHz
- **THEN** audio is resampled to 16kHz (required for Whisper and most audio classifiers)

#### Scenario: Get audio segment aligned with frame timecode
- **WHEN** AudioExtractor.get_audio_segment(start_time=10.5, duration=0.033) is called
- **THEN** audio slice from timecode 10.5 to 10.533 is returned as numpy array

#### Scenario: Handle missing audio gracefully
- **WHEN** video has no audio track
- **THEN** extract() returns empty array or None; detectors handle gracefully with no profanity/sound detections

#### Scenario: Cleanup releases memory
- **WHEN** AudioExtractor.cleanup() is called
- **THEN** cached audio is released from memory

### Requirement: Speech Profanity Detection

The system SHALL detect profanity in speech by transcribing audio using Whisper and matching against language-specific keyword lists.

#### Scenario: Transcribe speech to text
- **WHEN** SpeechProfanityDetector.detect(audio_data=audio) is called with speech audio
- **THEN** Whisper model transcribes audio to text

#### Scenario: Match keywords in transcription
- **WHEN** transcription is obtained from Whisper
- **THEN** transcription is checked against loaded profanity keyword lists for configured languages

#### Scenario: Return high-confidence profanity detection
- **WHEN** keyword is found in transcription
- **THEN** DetectionResult is returned with label="Profanity", confidence=0.95, and reasoning showing matched keyword

#### Scenario: Skip non-speech audio
- **WHEN** audio segment contains only music or silence (no speech)
- **THEN** transcription is empty or confidence is very low; no profanity results returned

#### Scenario: Support multiple languages
- **WHEN** detector is configured with languages: ["en", "es", "fr"]
- **THEN** detector loads keyword lists for all configured languages and checks all

#### Scenario: Return empty results for silent audio
- **WHEN** audio_data is None or empty
- **THEN** detect() returns empty list with no profanity detections

#### Scenario: Handle transcription failure gracefully
- **WHEN** Whisper transcription fails (corrupted audio, unsupported codec)
- **THEN** error is logged and empty results returned (not fatal)

### Requirement: Audio Classification Detection

The system SHALL detect sound effects and music using pre-trained audio classification models and map results to content categories.

#### Scenario: Classify audio using pre-trained model
- **WHEN** AudioClassificationDetector.detect(audio_data=audio) is called
- **THEN** audio is classified using HuggingFace audio classification model

#### Scenario: Map audio labels to content categories
- **WHEN** audio is classified as "gunshot" or "scream"
- **THEN** detector maps to "Violence" category (or "Sexual Theme" for "moaning", etc.)

#### Scenario: Return detection for mapped category
- **WHEN** audio label maps to configured target category
- **THEN** DetectionResult is returned with detected category and model confidence score

#### Scenario: Skip unmapped audio labels
- **WHEN** audio is classified but label does not map to any configured target category
- **THEN** result is not included in detections

#### Scenario: Return empty results for silence
- **WHEN** audio_data is None, empty, or mostly silence
- **THEN** detect() returns empty list with no sound/music detections

#### Scenario: Confidence score reflects model uncertainty
- **WHEN** audio classification has low confidence (e.g., 0.45 for ambiguous sound)
- **THEN** DetectionResult includes this confidence score; caller can filter based on threshold

#### Scenario: Handle model inference failure gracefully
- **WHEN** audio classification model fails (OOM, bad input)
- **THEN** error is logged and empty results returned; pipeline continues

### Requirement: Multi-Language Profanity Keywords

The system SHALL support profanity detection in multiple languages with configurable language selection.

#### Scenario: Load English profanity keywords
- **WHEN** detector is initialized with languages: ["en"]
- **THEN** English profanity keyword list is loaded

#### Scenario: Load Spanish profanity keywords
- **WHEN** detector is initialized with languages: ["es"]
- **THEN** Spanish profanity keyword list is loaded

#### Scenario: Load French profanity keywords
- **WHEN** detector is initialized with languages: ["fr"]
- **THEN** French profanity keyword list is loaded

#### Scenario: Support multiple languages simultaneously
- **WHEN** detector is configured with languages: ["en", "es"]
- **THEN** profanity in both English and Spanish is detected in same transcription

#### Scenario: Case-insensitive keyword matching
- **WHEN** transcription contains "Damn" or "DAMN" and keyword list has "damn"
- **THEN** keyword is matched despite case difference
