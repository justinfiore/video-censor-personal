# detection-framework Specification

## Purpose

Define a flexible, pluggable detection framework that enables multiple detector implementations (LLMs, APIs, local models) to identify multiple content categories in a single inference pass. The framework orchestrates detectors sequentially, aggregates results, handles failures gracefully, and supports declarative configuration of detector chains.
## Requirements
### Requirement: Detector Interface

The system SHALL define an abstract detector interface that all detection implementations must follow, enabling pluggable detectors with consistent lifecycle management.

#### Scenario: Implement custom detector
- **WHEN** developer creates a class inheriting from Detector abstract base
- **THEN** they must implement detect() method and can optionally implement cleanup()

#### Scenario: Detector declares supported categories
- **WHEN** detector is initialized with configuration
- **THEN** it declares which content categories it can analyze (e.g., ["Profanity", "Nudity", "Violence"])

#### Scenario: Detector initialization with config
- **WHEN** detector is created with detector_config dict
- **THEN** detector has access to name, model path, threshold, and other implementation-specific parameters

#### Scenario: Detector cleanup
- **WHEN** detection analysis completes or application shuts down
- **THEN** detector.cleanup() is called to release models, temp files, and system resources

### Requirement: Multi-Category Detection Per Detector

The system SHALL enable individual detectors to identify multiple content categories in a single inference pass, maximizing efficiency while maintaining flexibility.

#### Scenario: Single detector identifies multiple categories
- **WHEN** detector analyzes frame with vision model
- **THEN** detector returns DetectionResult objects for all categories it identifies (e.g., both "Profanity" and "Violence" from same analysis)

#### Scenario: Each category result is independent
- **WHEN** detector returns multi-category results
- **THEN** each DetectionResult has independent confidence, reasoning, and timecode

#### Scenario: Detector skips categories not detected
- **WHEN** detector analyzes frame and finds no violence but detects profanity
- **THEN** detector returns only profanity DetectionResult; no empty/zero-confidence results for undetected categories

#### Scenario: Different confidence per category
- **WHEN** same analysis identifies Profanity (0.95 confidence) and Violence (0.65 confidence)
- **THEN** each category can have different confidence reflecting detector's actual assessment

### Requirement: Detector Registry

The system SHALL maintain a registry of available detector implementations to enable runtime registration and instantiation of detectors.

#### Scenario: Register detector implementation
- **WHEN** developer registers new detector type with registry
- **THEN** detector becomes available for instantiation by detector type name

#### Scenario: Create detector instance from config
- **WHEN** pipeline requests detector creation with detector_type="llama-vision" and config dict
- **THEN** registry instantiates correct detector class with provided config

#### Scenario: Unknown detector type raises error
- **WHEN** detector config specifies unknown detector_type
- **THEN** system raises ValueError indicating unknown detector and available types

### Requirement: Detection Pipeline

The system SHALL orchestrate detector execution across multiple detectors, aggregating results and handling errors gracefully.

#### Scenario: Initialize pipeline with multiple detectors
- **WHEN** DetectionPipeline is created with config specifying 2 detectors
- **THEN** pipeline initializes both detectors and tracks them for analysis

#### Scenario: Analyze frame with all detectors
- **WHEN** frame is submitted to pipeline for analysis
- **THEN** pipeline runs all detectors sequentially and returns aggregated DetectionResult list

#### Scenario: Detector failure does not stop pipeline
- **WHEN** first detector raises exception during analysis
- **THEN** error is logged, pipeline continues with remaining detectors

#### Scenario: Set timecode from frame
- **WHEN** detector returns results without timecode
- **THEN** pipeline assigns frame's timecode to all returned results

#### Scenario: Pipeline cleanup releases all detectors
- **WHEN** pipeline.cleanup() is called
- **THEN** cleanup() is called on all detectors in reverse order

#### Scenario: Empty detector list
- **WHEN** pipeline is initialized with no detectors
- **THEN** pipeline.analyze_frame() returns empty result list

### Requirement: Detector Configuration

The system SHALL support declarative configuration of detectors, specifying which detector types to use, which categories each analyzes, and detector-specific parameters.

#### Scenario: Configure detector type and model
- **WHEN** config specifies detector with type="llama-vision" and model="llava-v1.5-7b"
- **THEN** pipeline creates detector of that type using specified model

#### Scenario: Specify detector categories
- **WHEN** detector config includes categories: ["Profanity", "Violence", "Sexual Theme"]
- **THEN** detector knows it should analyze these categories

#### Scenario: Detector-specific parameters
- **WHEN** detector config includes confidence_threshold, languages, or other implementation-specific parameters
- **THEN** detector receives these parameters during initialization

#### Scenario: Multiple detectors in config
- **WHEN** config specifies 2 detectors with different types and categories
- **THEN** both are initialized and can analyze different aspects of content

#### Scenario: Configuration validation
- **WHEN** invalid detector config is provided (missing required fields)
- **THEN** system raises descriptive error during pipeline initialization

### Requirement: Error Handling and Resilience

The system SHALL handle detector failures gracefully, logging errors and continuing with remaining detectors rather than stopping analysis.

#### Scenario: Detector throws exception
- **WHEN** detector.detect() raises exception
- **THEN** error is logged with detector name and exception details, pipeline continues

#### Scenario: Detector initialization failure
- **WHEN** detector initialization fails (model missing, bad config)
- **THEN** error is logged and pipeline raises exception before analysis begins

#### Scenario: Detector timeout (future)
- **WHEN** detector.detect() exceeds timeout threshold
- **THEN** detection is skipped for that detector with timeout error logged

#### Scenario: Partial results handling
- **WHEN** detector returns partial results (1 out of 4 configured categories)
- **THEN** partial results are accepted and included in output

### Requirement: Frame and Audio Analysis

The system SHALL support detecting on both visual (frame) and audio data, with detectors specifying which modalities they handle.

#### Scenario: Visual-only detector
- **WHEN** detector receives frame_data (numpy array)
- **THEN** detector analyzes visual content and returns results

#### Scenario: Audio-capable detector
- **WHEN** detector receives both frame_data and audio_data
- **THEN** detector can use both modalities for analysis (e.g., audio for speech profanity)

#### Scenario: Detector handles None audio gracefully
- **WHEN** audio_data is None and detector is audio-capable
- **THEN** detector either skips audio analysis or raises clear error if audio is required

#### Scenario: Audio-only detector
- **WHEN** detector is configured for audio analysis only (e.g., speech profanity)
- **THEN** detector processes audio_data and may skip or ignore frame_data

