# feat: Add video remediation feature with blank and cut modes

## Summary

Adds a new video remediation subsystem that allows blanking or cutting detected visual content from videos, with support for per-category and per-segment mode overrides.

## What Changed

### New Features
- **VideoRemediator engine** (`video_censor_personal/video_remediator.py`): Core remediation logic supporting:
  - **Blank mode**: Replaces detected segments with solid color frames (preserves audio)
  - **Cut mode**: Removes detected segments entirely from timeline
  - Three-tier mode resolution: segment-level → category-level → global default
  - Per-category mode overrides via `category_modes` config
  - Segment-level `allow` override to skip remediation
  - ffmpeg filter chain generation for blank mode
  - Segment extraction and concatenation for cut mode

- **Configuration support** (`video_censor_personal/config.py`):
  - New `remediation.video_editing` config section
  - Validation for mode, blank_color (hex), and category_modes
  - Helper functions: `is_video_remediation_enabled()`, `get_video_remediation_mode()`, etc.

- **CLI integration** (`video_censor_personal/cli.py`):
  - Requires `--output-video` when video remediation is enabled
  - Updated warning messages for unused output video flag

### Documentation
- Comprehensive section added to CONFIGURATION_GUIDE.md
- Quick start examples added to QUICK_START.md
- README.md updated with feature overview
- Example config: `video-censor-video-remediation.yaml.example`

### Tests
- `tests/test_video_remediator.py`: Unit tests (784 lines) covering all remediator methods
- `tests/test_video_remediator_integration.py`: Integration tests for ffmpeg workflows
- `tests/test_config_video_remediation.py`: Config validation tests

## Why

Enables users to automatically sanitize detected visual content by either:
1. Blanking frames (useful when you want to preserve timing/audio sync)
2. Cutting segments (useful when you want a shorter, cleaner output)

The three-tier mode resolution provides flexibility—users can set a global default but override for specific categories (e.g., cut violence, blank nudity) or individual detections.

## Files Changed

| File | Change |
|------|--------|
| `video_censor_personal/video_remediator.py` | ✨ New - Core remediation engine |
| `video_censor_personal/config.py` | ➕ Added remediation config validation & helpers |
| `video_censor_personal/cli.py` | 🔧 Updated CLI validation for video remediation |
| `tests/test_video_remediator.py` | ✨ New - Unit tests |
| `tests/test_video_remediator_integration.py` | ✨ New - Integration tests |
| `tests/test_config_video_remediation.py` | ✨ New - Config tests |
| `CONFIGURATION_GUIDE.md` | 📚 Added Section 8: Video Remediation |
| `QUICK_START.md` | 📚 Added video remediation examples |
| `README.md` | 📚 Updated feature overview |
| `video-censor-video-remediation.yaml.example` | ✨ New - Example config |
