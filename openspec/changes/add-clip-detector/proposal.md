# Change: Add OpenAI CLIP Model as Video Detector

## Why

The project currently supports LLaVA for vision-based detection, which is powerful but resource-intensive. CLIP (Contrastive Language-Image Pretraining) offers a lightweight, efficient alternative for detecting content categories through prompt-based image classification. CLIP enables users to configure custom detection categories via text prompts without requiring large vision-language models, reducing memory footprint and inference latency.

## What Changes

- Add new `clip-detector` capability implementing CLIP-based content detection
- Support configurable prompts per category as shown in the example YAML
- Add `--download-models` CLI flag for convenient one-time model download
- Register CLIP detector in the detector registry for use in detection pipelines
- Support multiple model sizes (`openai/clip-vit-base-patch32`, `openai/clip-vit-large-patch14`, etc.)
- Integrate with existing detection framework (Detector interface, DetectionPipeline)

## Impact

- **Affected specs**: 
  - New: `clip-detector`
  - Modified: `detection-framework` (no changes to interface, only adds new implementation option)
- **Affected code**:
  - New: `video_censor_personal/detectors/clip_detector.py`
  - Modified: `video_censor_personal/__init__.py` (register CLIP detector)
  - Configuration: YAML configs can now specify `type: "clip"`
