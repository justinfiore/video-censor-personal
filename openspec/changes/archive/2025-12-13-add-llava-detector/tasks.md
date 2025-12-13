# Implementation Tasks

## 1. Project Setup

- [ ] 1.1 Create `video_censor_personal/detectors/` directory structure
- [ ] 1.2 Create `video_censor_personal/detectors/__init__.py` with detector registry
- [ ] 1.3 Create `prompts/` directory for prompt templates
- [ ] 1.4 Uncomment transformers/torch/torchvision/pillow in requirements.txt
- [ ] 1.5 Create `prompts/llava-detector.txt` with default prompt template

## 2. LLaVA Detector Implementation

- [ ] 2.1 Create `video_censor_personal/detectors/llava_detector.py` with LLaVADetector class
- [ ] 2.2 Implement `__init__()` with model loading and validation
- [ ] 2.3 Implement `_load_prompt()` to read external prompt files
- [ ] 2.4 Implement `_load_model()` with error handling and user guidance
- [ ] 2.5 Implement `detect()` method for frame analysis
- [ ] 2.6 Implement BGR to RGB and PIL Image conversion
- [ ] 2.7 Implement LLaVA inference with max_new_tokens and temperature config
- [ ] 2.8 Implement JSON response parsing with error recovery
- [ ] 2.9 Implement confidence score extraction and validation (clamp to [0.0, 1.0])
- [ ] 2.10 Implement category mapping (JSON keys → DetectionResult labels)
- [ ] 2.11 Implement `cleanup()` for model unloading
- [ ] 2.12 Register LLaVADetector in detector registry globally

## 3. Error Handling & User Guidance

- [ ] 3.1 Add validation for model existence before inference
- [ ] 3.2 Create helpful error message for missing models (with download instructions)
- [ ] 3.3 Create helpful error message for missing dependencies (transformers/torch)
- [ ] 3.4 Create helpful error message for missing prompt files
- [ ] 3.5 Handle RuntimeError (OOM) during inference gracefully
- [ ] 3.6 Handle JSON parse failures with logging and fallback
- [ ] 3.7 Handle invalid frame data (None, wrong shape)

## 4. Configuration Support

- [ ] 4.1 Add LLaVA detector example to `video-censor.yaml.example`
- [ ] 4.2 Document config parameters: model_name, model_path, prompt_file
- [ ] 4.3 Support both 7B and 13B model variants via model_name config
- [ ] 4.4 Allow custom model_path for non-default HuggingFace cache locations
- [ ] 4.5 Verify prompt_file path exists during detector initialization

## 5. Testing - Unit Tests (Mocked Model)

- [ ] 5.1 Create `tests/test_llava_detector.py`
- [ ] 5.2 Mock LLaVA model and processor with unittest.mock
- [ ] 5.3 Test detector initialization with valid config
- [ ] 5.4 Test detector initialization with missing model (error message)
- [ ] 5.5 Test detector initialization with missing dependencies
- [ ] 5.6 Test detector initialization with missing prompt file
- [ ] 5.7 Test detect() with valid frame data
- [ ] 5.8 Test detect() with BGR to RGB conversion
- [ ] 5.9 Test detect() with LLaVA returning valid JSON with multi-category results
- [ ] 5.10 Test detect() with malformed JSON response (graceful fallback)
- [ ] 5.11 Test detect() with missing JSON fields (default confidence)
- [ ] 5.12 Test detect() with None frame_data (error)
- [ ] 5.13 Test detect() with RuntimeError (OOM) during inference
- [ ] 5.14 Test confidence score clamping to [0.0, 1.0]
- [ ] 5.15 Test category mapping (JSON keys to DetectionResult labels)
- [ ] 5.16 Test cleanup() method
- [ ] 5.17 Test detector inherits from Detector base class
- [ ] 5.18 Test detector registers in global registry

## 6. Testing - Integration Tests (Stub Responses)

- [ ] 6.1 Test detector with mocked LLaVA returning realistic JSON response
- [ ] 6.2 Test detector integration with DetectionPipeline
- [ ] 6.3 Test pipeline orchestrates detector lifecycle (init → detect → cleanup)
- [ ] 6.4 Test pipeline aggregates LLaVA results with other detectors
- [ ] 6.5 Test end-to-end: frame → detector → multi-category DetectionResults

## 7. Testing - Configuration Validation

- [ ] 7.1 Test detector config parsing from YAML
- [ ] 7.2 Test default model_name (7B if not specified)
- [ ] 7.3 Test custom model_name (13B variant)
- [ ] 7.4 Test custom model_path
- [ ] 7.5 Test prompt_file path resolution

## 8. Documentation

- [ ] 8.1 Update `QUICK_START.md` with LLaVA detector setup instructions
- [ ] 8.2 Update `QUICK_START.md` with model download section (7B and 13B)
- [ ] 8.3 Update `README.md` to reference LLaVA detector in features
- [ ] 8.4 Add docstrings to LLaVADetector class and methods
- [ ] 8.5 Add example prompt in `prompts/llava-detector.txt` with clear instructions
- [ ] 8.6 Document config parameters in `video-censor.yaml.example`

## 9. Verification

- [ ] 9.1 Run pytest on test_llava_detector.py and ensure all tests pass
- [ ] 9.2 Verify 100% line coverage of llava_detector.py
- [ ] 9.3 Run full test suite (171+ tests) and ensure no regressions
- [ ] 9.4 Verify detector registers globally and can be instantiated via registry
- [ ] 9.5 Test error messages are clear and actionable
- [ ] 9.6 Verify prompt file loading works with external files
- [ ] 9.7 Test detector can process multiple frames with same instance
