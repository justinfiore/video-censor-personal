## ADDED Requirements

### Requirement: LLaVA Detector Implementation

The system SHALL implement a concrete Detector that uses the LLaVA vision-language model to analyze video frames and detect multiple content categories in a single inference pass.

#### Scenario: Detector loads model at initialization
- **WHEN** LLaVADetector is instantiated with valid config
- **THEN** model is loaded from HuggingFace cache (or custom path) and ready for inference

#### Scenario: Detector validates model exists before use
- **WHEN** LLaVADetector is instantiated
- **THEN** detector verifies model files exist; raises ValueError with download instructions if missing

#### Scenario: Missing dependencies fail fast
- **WHEN** transformers/torch/pillow libraries not installed
- **THEN** detector raises ValueError instructing user to install via pip

#### Scenario: Detector analyzes frame with LLaVA
- **WHEN** detect() is called with frame data (numpy array, BGR format)
- **THEN** frame is converted to RGB, processed by LLaVA, and analyzed

#### Scenario: Detector returns multi-category results
- **WHEN** LLaVA analysis completes
- **THEN** detector returns DetectionResult for each category detected (Nudity, Profanity, Violence, Sexual Theme)

#### Scenario: Confidence scores from LLM
- **WHEN** detector parses LLaVA response
- **THEN** confidence scores come directly from LLM output (0.0-1.0 range)

#### Scenario: Detector handles inference failures gracefully
- **WHEN** inference fails (OOM, timeout, etc.)
- **THEN** error is logged, empty result list returned, pipeline continues with other detectors

### Requirement: Configurable Detection Prompts

The system SHALL load detection prompts from external files, enabling prompt customization without code changes.

#### Scenario: Prompt file referenced in config
- **WHEN** detector config specifies prompt_file path
- **THEN** detector loads prompt template from that file at initialization

#### Scenario: Prompt file missing raises error
- **WHEN** specified prompt file does not exist
- **THEN** detector raises ValueError with path in error message

#### Scenario: Prompt template supports placeholders
- **WHEN** prompt file is loaded
- **THEN** template can include placeholders for dynamic values (future extensibility)

#### Scenario: Multiple prompts can coexist
- **WHEN** different detector configs reference different prompt files
- **THEN** each detector uses its configured prompt independently

### Requirement: Pre-Downloaded Model Assumption

The system SHALL NOT download models automatically. It SHALL assume models are pre-installed and provide clear instructions if they're missing.

#### Scenario: Detector does not auto-download
- **WHEN** model not found in cache
- **THEN** detector raises error; does NOT attempt download

#### Scenario: Clear error message on missing model
- **WHEN** model files not found
- **THEN** error message includes model name, expected location, and download instructions

#### Scenario: Error includes Python download command
- **WHEN** model is missing
- **THEN** error message includes ready-to-run Python code to download model

#### Scenario: Error references documentation
- **WHEN** model loading fails
- **THEN** error message points to QUICK_START.md for detailed setup instructions

### Requirement: Model Size Configuration

The system SHALL support both 7B and 13B model variants via configuration.

#### Scenario: Model selection via config
- **WHEN** detector config specifies model_name ("llava-v1.5-7b" or "...13b")
- **THEN** detector loads the specified model variant

#### Scenario: Default model is 7B
- **WHEN** model_name not specified in config
- **THEN** detector defaults to llava-v1.5-7b

#### Scenario: Custom model cache path
- **WHEN** detector config includes model_path
- **THEN** detector loads model from custom path instead of HuggingFace cache

### Requirement: Frame Format Handling

The system SHALL convert video frames from OpenCV BGR format to formats expected by LLaVA.

#### Scenario: BGR to RGB conversion
- **WHEN** detect() receives frame_data in BGR format (from video_extraction)
- **THEN** frame is converted to RGB before LLaVA processing

#### Scenario: Frame to PIL Image conversion
- **WHEN** frame is in RGB format
- **THEN** frame is converted to PIL Image for LLaVA processor

#### Scenario: Invalid frame data raises error
- **WHEN** frame_data is None or wrong shape
- **THEN** detector raises ValueError with details

### Requirement: Response Parsing

The system SHALL parse LLaVA responses as JSON and extract detection results and confidence scores reliably.

#### Scenario: JSON response parsing
- **WHEN** LLaVA returns response
- **THEN** detector parses response as JSON

#### Scenario: Malformed JSON handled gracefully
- **WHEN** response is not valid JSON
- **THEN** error is logged, empty result list returned, pipeline continues

#### Scenario: Confidence score validation
- **WHEN** parsing confidence scores from response
- **THEN** scores are clamped to [0.0, 1.0] range

#### Scenario: Missing fields in response handled
- **WHEN** response JSON missing expected fields
- **THEN** detector uses default values (confidence=0.5) and logs warning

### Requirement: Resource Management

The system SHALL manage model memory efficiently across multiple frame analyses.

#### Scenario: Single model instance reuse
- **WHEN** detector analyzes multiple frames
- **THEN** same model instance is reused (not reloaded)

#### Scenario: Cleanup releases model
- **WHEN** detector.cleanup() is called
- **THEN** model is unloaded from memory, allowing garbage collection

#### Scenario: Out-of-memory handling
- **WHEN** inference raises RuntimeError due to OOM
- **THEN** error is caught, logged, and empty results returned

### Requirement: Integration with Detection Framework

The system SHALL integrate seamlessly with the Detector interface and DetectionPipeline orchestration.

#### Scenario: Detector inherits from Detector ABC
- **WHEN** LLaVADetector is defined
- **THEN** it implements Detector abstract base class fully

#### Scenario: Categories specified in config
- **WHEN** detector config includes categories list
- **THEN** detector declares supported categories (Nudity, Profanity, Violence, Sexual Theme)

#### Scenario: Pipeline orchestrates detector lifecycle
- **WHEN** DetectionPipeline is created with LLaVA config
- **THEN** pipeline initializes detector, runs it on frames, calls cleanup

#### Scenario: Results aggregated by pipeline
- **WHEN** detector returns multi-category results
- **THEN** pipeline aggregates with results from other detectors
