## 1. Core Device Detection Utility

- [x] 1.1 Create `video_censor_personal/device_utils.py` with `get_device(config_override: str | None) -> str` function
- [x] 1.2 Implement auto-detection: CUDA → MPS → CPU fallback order
- [x] 1.3 Add INFO-level logging for detected device (e.g., "Using device: cuda", "Using device: mps", "Using device: cpu (no GPU available)")
- [x] 1.4 Add unit tests for device detection

## 2. LLaVA Detector GPU Support

- [x] 2.1 Import and use `get_device()` in LLaVADetector.__init__, log device at INFO level
- [x] 2.2 Move model to device after loading: `model.to(device)`
- [x] 2.3 Move inputs to device in detect(): `inputs = {k: v.to(device) for k, v in inputs.items()}`
- [x] 2.4 Add `device` config option (optional override)
- [x] 2.5 Update cleanup() to handle device-aware model
- [x] 2.6 Test on MPS (Apple Silicon) and/or CUDA if available

## 3. Audio Classification Detector GPU Support

- [x] 3.1 Import and use `get_device()` in AudioClassificationDetector.__init__, log device at INFO level
- [x] 3.2 Move model to device after loading
- [x] 3.3 Move inference tensors to device
- [x] 3.4 Add `device` config option
- [x] 3.5 Test inference on available GPU

## 4. Speech Profanity Detector GPU Support

- [x] 4.1 Use `device` parameter in transformers pipeline() call, log device at INFO level
- [x] 4.2 Add `device` config option for override
- [x] 4.3 Test ASR pipeline on available GPU

## 5. Documentation

- [x] 5.1 Update QUICK_START.md with GPU requirements and troubleshooting
- [x] 5.2 Add device config examples to YAML example files
- [x] 5.3 Update README with GPU support notes

## 6. Validation

- [x] 6.1 Run full test suite
- [x] 6.2 Run end-to-end test on sample video with GPU
- [x] 6.3 Verify CPU fallback works when no GPU available
