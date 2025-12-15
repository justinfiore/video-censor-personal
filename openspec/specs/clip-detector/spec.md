# clip-detector Specification

## Purpose
TBD - created by archiving change add-clip-detector. Update Purpose after archive.
## Requirements
### Requirement: CLIP Detector Implementation

The system SHALL implement a concrete Detector that uses OpenAI's CLIP model to analyze video frames and detect multiple content categories via configurable text prompts.

#### Scenario: Detector loads model at initialization
- **WHEN** CLIPDetector is instantiated with valid config
- **THEN** CLIP model is loaded from HuggingFace cache (or custom path) and ready for inference

#### Scenario: Detector validates model exists before use
- **WHEN** CLIPDetector is instantiated and model files not found
- **THEN** detector raises ValueError with download instructions including `--download-models` flag option

#### Scenario: Missing dependencies fail fast
- **WHEN** transformers/torch/PIL libraries not installed
- **THEN** detector raises ValueError instructing user to install via pip

#### Scenario: Model downloaded when --download-models flag specified
- **WHEN** CLI is invoked with `--download-models` flag
- **THEN** detector downloads CLIP model from HuggingFace before starting analysis
- **AND** logs download progress at INFO level

#### Scenario: Download skipped if model already exists
- **WHEN** CLI is invoked with `--download-models` flag and model already cached
- **THEN** detector skips download and uses existing model

#### Scenario: Download failure provides clear error
- **WHEN** model download fails (network error, disk space, etc.)
- **THEN** detector logs error with details and raises ValueError; analysis does not proceed

#### Scenario: Detector analyzes frame with CLIP
- **WHEN** detect() is called with frame data (numpy array, BGR format)
- **THEN** frame is converted to RGB, processed by CLIP image encoder, and analyzed against text prompts

#### Scenario: Detector returns multi-category results
- **WHEN** CLIP analysis completes
- **THEN** detector returns DetectionResult for each configured category with similarity scores

#### Scenario: Confidence scores from CLIP embeddings
- **WHEN** detector computes similarity between image and text prompts
- **THEN** confidence scores reflect maximum similarity across prompt candidates for each category (0.0-1.0 range)

#### Scenario: Detector handles inference failures gracefully
- **WHEN** inference fails (OOM, timeout, etc.)
- **THEN** error is logged, empty result list returned, pipeline continues with other detectors

### Requirement: Configurable Text Prompts

The system SHALL support configurable text prompts per category, enabling users to define detection semantics without code changes.

#### Scenario: Prompts defined inline in config
- **WHEN** detector config includes `prompts` list with category and text fields
- **THEN** detector loads prompts from config and uses them for classification

#### Scenario: Multiple prompt candidates per category
- **WHEN** detector config specifies category with text list (e.g., ["fight", "punch", "combat"])
- **THEN** detector computes similarity against all candidates and returns maximum score for that category

#### Scenario: Prompt validation on initialization
- **WHEN** detector is created with config
- **THEN** detector validates each prompt has `category` and `text` fields; raises ValueError if invalid

#### Scenario: Category coverage validation
- **WHEN** detector initializes
- **THEN** detector verifies all configured categories (from detector config) have corresponding prompts; raises ValueError if missing

#### Scenario: Text prompts are list of strings
- **WHEN** prompt is parsed from config
- **THEN** text field must be a list of strings; raises ValueError if not

### Requirement: Model Size Configuration

The system SHALL support multiple CLIP model variants via configuration.

#### Scenario: Model selection via config
- **WHEN** detector config specifies model_name ("openai/clip-vit-base-patch32" or "openai/clip-vit-large-patch14")
- **THEN** detector loads the specified model variant

#### Scenario: Default model is ViT-Base
- **WHEN** model_name not specified in config
- **THEN** detector defaults to openai/clip-vit-base-patch32

#### Scenario: Custom model cache path
- **WHEN** detector config includes model_path
- **THEN** detector loads model from custom path instead of HuggingFace cache

### Requirement: Optional Model Download

The system SHALL support downloading CLIP models via the `--download-models` CLI flag when models are not yet cached locally.

#### Scenario: Download all configured models
- **WHEN** CLI is invoked with `--download-models` flag
- **THEN** system downloads all CLIP models specified in detector configs before analysis starts

#### Scenario: Download only missing models
- **WHEN** some models are cached and others are missing, and `--download-models` flag is specified
- **THEN** system downloads only the missing models

#### Scenario: User instructed to use download flag
- **WHEN** model is missing and `--download-models` flag is NOT specified
- **THEN** error message explicitly suggests running with `--download-models` flag to auto-download

#### Scenario: Download respects custom cache path
- **WHEN** detector config includes custom model_path and `--download-models` flag is specified
- **THEN** model is downloaded to custom path, not default HuggingFace cache

#### Scenario: Download progress visible to user
- **WHEN** model download is in progress
- **THEN** system logs progress (model name, size, download percentage) at INFO level

#### Scenario: Interrupted download is handled gracefully
- **WHEN** download is interrupted (Ctrl+C, network failure)
- **THEN** partial files are cleaned up and error is logged with clear message

### Requirement: Frame Format Handling

The system SHALL convert video frames from OpenCV BGR format to RGB for CLIP processing.

#### Scenario: BGR to RGB conversion
- **WHEN** detect() receives frame_data in BGR format (from video_extraction)
- **THEN** frame is converted to RGB before CLIP image encoding

#### Scenario: Frame to PIL Image conversion
- **WHEN** frame is in RGB format
- **THEN** frame is converted to PIL Image for CLIP processor

#### Scenario: Invalid frame data raises error
- **WHEN** frame_data is None or wrong shape
- **THEN** detector raises ValueError with details

### Requirement: Resource Management

The system SHALL manage model memory efficiently across multiple frame analyses.

#### Scenario: Single model instance reuse
- **WHEN** detector analyzes multiple frames
- **THEN** same CLIP model instance is reused (not reloaded)

#### Scenario: Cleanup releases model
- **WHEN** detector.cleanup() is called
- **THEN** model is unloaded from memory, allowing garbage collection

#### Scenario: Out-of-memory handling
- **WHEN** inference raises RuntimeError due to OOM
- **THEN** error is caught, logged, and empty results returned

#### Scenario: GPU memory released on cleanup
- **WHEN** detector.cleanup() is called with model on GPU
- **THEN** model is moved to CPU before dereferencing to release GPU memory

### Requirement: GPU Device Support

The system SHALL automatically detect and use available GPU acceleration (CUDA, MPS) for model inference, falling back to CPU when no GPU is available.

#### Scenario: Auto-detect CUDA GPU
- **WHEN** CLIPDetector initializes on a system with NVIDIA GPU
- **THEN** model is loaded and moved to CUDA device

#### Scenario: Auto-detect MPS (Apple Silicon)
- **WHEN** CLIPDetector initializes on Apple Silicon Mac
- **THEN** model is loaded and moved to MPS device

#### Scenario: Fallback to CPU
- **WHEN** no GPU is available
- **THEN** model runs on CPU with warning logged about slower performance

#### Scenario: Device logged at startup
- **WHEN** detector initializes
- **THEN** selected device is logged at INFO level

### Requirement: Configurable Device Override

The system SHALL allow users to override automatic device detection via configuration.

#### Scenario: Manual device selection
- **WHEN** detector config includes `device: "cpu"` (or "cuda", "mps")
- **THEN** detector uses specified device instead of auto-detection

#### Scenario: Invalid device raises error
- **WHEN** config specifies unavailable device (e.g., "cuda" on Mac)
- **THEN** detector raises ValueError with available options

### Requirement: Integration with Detection Framework

The system SHALL integrate seamlessly with the Detector interface and DetectionPipeline orchestration.

#### Scenario: Detector inherits from Detector ABC
- **WHEN** CLIPDetector is defined
- **THEN** it implements Detector abstract base class fully

#### Scenario: Categories specified in config
- **WHEN** detector config includes categories list
- **THEN** detector declares supported categories matching configured prompt categories

#### Scenario: Pipeline orchestrates detector lifecycle
- **WHEN** DetectionPipeline is created with CLIP config
- **THEN** pipeline initializes detector, runs it on frames, calls cleanup

#### Scenario: Results aggregated by pipeline
- **WHEN** detector returns multi-category results
- **THEN** pipeline aggregates with results from other detectors

