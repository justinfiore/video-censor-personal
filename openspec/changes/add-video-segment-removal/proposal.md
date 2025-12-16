# Change: Add Video Segment Removal Remediation

## Why

Users need to censor visual content (not just audio) by blanking or cutting detected video segments. Currently, only audio remediation is supported—users have no way to hide objectionable visual content from the output video.

## What Changes

- Add new `video-remediation` capability for visual segment censoring
- Support two modes: **blank** (black screen) and **cut** (remove segment entirely)
- Integrate with existing `segment-allow-override` (only remediate segments NOT marked `"allow": true`)
- Require `--output-video` when video remediation is enabled
- Allow combining with audio remediation (e.g., bleep audio + blank video for same segment)

## Impact

- Affected specs: New `video-remediation` capability; modify `project-foundation` for --output-video validation
- Affected code: `video_censor_personal/` remediation pipeline, config parsing, ffmpeg integration
- User-facing: New YAML config section `remediation.video_editing`
