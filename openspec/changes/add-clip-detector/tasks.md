# Implementation Tasks: Add CLIP Detector

## 1. Core Detector Implementation

- [x] 1.1 Create `video_censor_personal/detectors/clip_detector.py` with CLIPDetector class
  - Inherit from Detector ABC
  - Implement `__init__()` to validate config, load model, and parse prompts
  - Implement `detect()` to run CLIP inference and return DetectionResults
  - Implement `cleanup()` to release model from memory

- [x] 1.2 Add model loading logic
  - Load CLIP model from HuggingFace (via transformers library)
  - Auto-detect GPU (CUDA/MPS) or CPU
  - Check if model exists before loading
  - If missing and `--download-models` flag is set, download model
  - If missing and flag is NOT set, raise error with suggestion to use `--download-models`
  - Log selected device at INFO level

- [x] 1.2b Add model download functionality
  - Implement model download method that uses HuggingFace's API
  - Support custom cache paths when configured
  - Log download progress at INFO level
  - Handle download errors gracefully (network, disk space, interruptions)
  - Clean up partial files on download failure

- [x] 1.3 Implement prompt parsing and validation
  - Parse `prompts` list from config
  - Validate each prompt has `category` and `text` fields
  - Validate `text` is a list of strings
  - Validate all configured categories have associated prompts
  - Raise ValueError with clear message if validation fails

- [x] 1.4 Implement inference logic
  - Convert BGR frame to RGB
  - Process image with CLIP image encoder
  - Compute text embeddings for all candidate prompts
  - Calculate similarity scores (cosine distance)
  - Return DetectionResult for each category with max similarity score as confidence
  - Handle inference errors gracefully (log, return empty results)

## 2. CLI and Pipeline Integration

- [x] 2.0 Add `--download-models` flag to CLI
  - Add boolean `--download-models` flag to argument parser in cli.py
  - Pass flag to DetectionPipeline during initialization
  - Document flag in help text

- [x] 2.0b Implement model download in pipeline
  - Add `download_models()` method to DetectionPipeline
  - Iterate through detector configs and collect all required models
  - Call CLIPDetector.download_model() for each CLIP model
  - Handle partial failures (skip failed models, log, continue)
  - Call pipeline.download_models() if --download-models flag is set before analysis

## 2. Integration and Registration

- [x] 2.1 Register CLIP detector in detector registry
  - Add `register_detector("clip", CLIPDetector)` in `video_censor_personal/__init__.py`
  - Verify detector is discoverable via `get_detector_registry().registered_types()`

- [x] 2.2 Test detection framework compatibility
  - Verify DetectionPipeline can instantiate CLIP detector from config
  - Verify pipeline can run CLIP detector via `analyze_frame()`
  - Verify cleanup() is called by pipeline.cleanup()

## 3. Testing

- [x] 3.1 Unit tests for CLIPDetector (`tests/test_clip_detector.py`)
  - Test successful initialization with valid config
  - Test config validation (missing prompts, invalid format, etc.)
  - Test detect() with real frame data (dummy numpy array OK)
  - Test multi-category detection with independent scores
  - Test error handling (inference failure, OOM recovery)
  - Test cleanup() releases model
  - Test device selection (auto-detect, override)
  - Test missing model raises error with `--download-models` suggestion
  - Test download_model() downloads and caches model
  - Test download_model() skips if model already exists
  - Test download_model() respects custom cache path
  - Test download_model() handles network errors gracefully

- [x] 3.2 Integration tests for pipeline compatibility
  - Test DetectionPipeline with CLIP detector config
  - Test CLIP detector coexists with other detectors (e.g., LLaVA)
  - Test end-to-end analysis: config → pipeline → analyze_frame() → results
  - Test pipeline.download_models() calls detector download methods
  - Test pipeline handles download failures (partial, complete)

- [x] 3.3 Configuration tests
  - Test example YAML config from proposal parses correctly
  - Test invalid configs raise appropriate errors with helpful messages
  - Test --download-models flag is parsed correctly
  - Test --download-models behavior with missing/existing models

- [x] 3.4 CLI tests
  - Test --download-models flag is available and documented
  - Test flag is passed through to pipeline
  - Test end-to-end: invoke CLI with --download-models and verify models are downloaded

## 4. Documentation and Examples

- [x] 4.1 Add CLIP detector section to QUICK_START.md
  - Model download instructions (manual and `--download-models` flag)
  - Example YAML config
  - Performance notes (speed vs. LLaVA)
  - Prompt engineering tips
  - Usage example: `python -m video_censor --download-models --config video-censor-clip.yaml`

- [x] 4.2 Add example config file
  - `video-censor-clip-detector.yaml.example`
  - Show multiple prompt examples per category

- [x] 4.3 Update README.md
  - Document CLIP as alternative to LLaVA
  - Link to quick start guide

## 5. Validation

- [x] 5.1 Run full test suite
  - pytest with coverage ≥80% for new code
  - All existing tests still pass

- [x] 5.2 Validate strict OpenSpec compliance
  - `openspec validate add-clip-detector --strict` passes with no errors
  - Spec format correct (scenarios with #### headers, etc.)
