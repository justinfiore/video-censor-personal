# Change: Add Video Extraction Capability

## Why

The video analysis pipeline requires a mechanism to extract audio and video frames from input files. This extraction step is fundamental to feeding the correct data formats to the LLM for content detection (video frames for visual analysis, audio for profanity detection). Without this capability, the system cannot process raw video files.

## What Changes

- **ADDED**: New `video-extraction` capability to extract frames and audio from video files using ffmpeg
- **ADDED**: Frame sampling strategy (uniform, scene-based, or all frames) configurable via YAML
- **ADDED**: Audio extraction and caching for reuse across detection modules
- **ADDED**: Frame metadata (timecode, duration) for temporal tracking
- **ADDED**: Integration with config system to respect processing settings (frame sample rate, max workers)

## Impact

- **Affected specs**: 
  - `project-foundation` (no changes to existing CLI/config—video-extraction is new capability)
  - `video-extraction` (new specification)
- **Affected code**: 
  - New module: `video_censor_personal/video_extraction.py`
  - New module: `video_censor_personal/frame.py` (Frame data class)
  - Modified: `video_censor_personal/config.py` (already supports processing config)
  - Modified: `video_censor_personal/cli.py` (will call extraction in main pipeline—to be handled by orchestration change)
