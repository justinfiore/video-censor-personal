# Change: Unify Remediation Configuration Hierarchy

## Why
The current configuration has audio remediation and video remediation at inconsistent hierarchy levels:
- Audio: `audio.remediation.*`
- Video: `remediation.video_editing.*`

This inconsistency makes the config harder to understand and maintain. Unifying both under a single `remediation` section improves clarity and maintainability.

## What Changes
- **BREAKING**: Move `audio.remediation.*` → `remediation.audio.*`
- Keep `remediation.video_editing.*` as `remediation.video.*` (rename subsection for consistency)
- Update config parser to read from new locations
- Update validation logic for new paths
- Maintain backward compatibility is **NOT** a goal (clean break)

## Impact
- Affected specs: `audio-remediation`, `video-remediation`, `project-foundation`
- Affected code:
  - `video_censor_personal/config.py` - validation and helper functions
  - `video_censor_personal/cli.py` - config access
  - `video_censor_personal/audio_remediation.py` - config reading
  - `video_censor_personal/video_remediation.py` - config reading (if exists)
- Affected tests:
  - `tests/test_config_audio.py`
  - `tests/test_config_video_remediation.py`
  - Any integration tests using config
- Affected documentation:
  - `CONFIGURATION_GUIDE.md`
  - All `.yaml.example` files
  - `AUDIO.md`
  - `VIDEO_AUDIO_REMEDIATION_WORKFLOW.md`
