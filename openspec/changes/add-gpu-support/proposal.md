# Change: Add GPU Support for Detector Inference

## Why
Model inference on CPU is extremely slow (minutes per frame for LLaVA 7B). GPU acceleration (CUDA, MPS/Metal) is essential for practical use. Currently no detectors manage device placement—models default to CPU.

## What Changes
- Add automatic GPU detection (CUDA → MPS → CPU fallback)
- Move models and tensors to detected device during initialization
- Move inference inputs to device before model.generate()
- Add `device` configuration option for manual override
- Apply to all torch-based detectors: LLaVA, AudioClassification, SpeechProfanity

## Impact
- Affected specs: `llava-detector`, `audio-detection`
- Affected code:
  - `video_censor_personal/detectors/llava_detector.py`
  - `video_censor_personal/audio_classification_detector.py`
  - `video_censor_personal/speech_profanity_detector.py`
