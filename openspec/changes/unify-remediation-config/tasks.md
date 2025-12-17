# Implementation Tasks

## 1. Configuration Schema Updates
- [ ] 1.1 Update `_validate_remediation_section` to expect `remediation.audio` and `remediation.video`
- [ ] 1.2 Add validation for `remediation.audio.enabled`, `remediation.audio.mode`, etc.
- [ ] 1.3 Rename `remediation.video_editing` validation to `remediation.video`
- [ ] 1.4 Remove old `audio.remediation` validation path

## 2. Config Helper Functions
- [ ] 2.1 Update all config getter functions to use new paths
- [ ] 2.2 Update `is_video_remediation_enabled` to use `remediation.video.enabled`
- [ ] 2.3 Update `get_video_remediation_mode` to use `remediation.video.mode`
- [ ] 2.4 Update `get_video_remediation_blank_color` to use `remediation.video.blank_color`
- [ ] 2.5 Update `get_video_remediation_category_modes` to use `remediation.video.category_modes`

## 3. Code Updates
- [ ] 3.1 Update `cli.py` to read audio remediation from `remediation.audio.enabled`
- [ ] 3.2 Update `audio_remediation.py` to read from `remediation.audio.*`
- [ ] 3.3 Update any video remediation code to read from `remediation.video.*`

## 4. Test Updates
- [ ] 4.1 Update all tests in `test_config_audio.py` to use new paths
- [ ] 4.2 Update all tests in `test_config_video_remediation.py` to use new paths
- [ ] 4.3 Update integration tests that reference config structure
- [ ] 4.4 Verify all config validation tests pass

## 5. Example YAML Configuration Updates
- [ ] 5.1 Update `video-censor.yaml` (active config file)
- [ ] 5.2 Update `video-censor.yaml.example`
- [ ] 5.3 Update `video-censor-audio-detection.yaml.example`
- [ ] 5.4 Update `video-censor-audio-remediation-bleep.yaml.example`
- [ ] 5.5 Update `video-censor-audio-remediation-silence.yaml.example`
- [ ] 5.6 Update `video-censor-clip-detector.yaml.example`
- [ ] 5.7 Update `video-censor-skip-chapters.yaml.example`
- [ ] 5.8 Update `video-censor-video-only.yaml`
- [ ] 5.9 Update `video-censor-video-remediation.yaml.example`

## 6. Documentation Updates
- [ ] 6.1 Update `CONFIGURATION_GUIDE.md` audio remediation section
- [ ] 6.2 Update `CONFIGURATION_GUIDE.md` video remediation section
- [ ] 6.3 Update `AUDIO.md` with new config paths
- [ ] 6.4 Update `VIDEO_AUDIO_REMEDIATION_WORKFLOW.md` if applicable
- [ ] 6.5 Update any code comments referencing old paths

## 7. Validation
- [ ] 7.1 Run `pytest tests/test_config*.py -v` and verify all pass
- [ ] 7.2 Run full test suite
- [ ] 7.3 Manually test with each example config file
- [ ] 7.4 Verify error messages reference correct paths
- [ ] 7.5 Verify all YAML files are valid with new structure
