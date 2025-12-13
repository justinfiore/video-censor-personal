# Change: Enhance Configuration Validation

## Why

The current configuration validation only checks structural requirements (presence of fields, correct types). To prevent invalid configurations from reaching runtime and causing obscure failures, we need semantic validation that enforces logical constraints: valid value ranges, enum constraints, and required state conditions.

## What Changes

- Add validation for detection sensitivity values (0.0-1.0)
- Require at least one detection category to be enabled
- Validate detection category structure (enabled, sensitivity, model fields)
- Restrict output format to "json" only
- Enforce frame sampling strategy enum ("uniform", "scene_based", "all")
- Add semantic validation for processing parameters (max_workers > 0, merge_threshold >= 0)

## Impact

- **Affected specs**: project-foundation (Configuration File Parsing)
- **Breaking changes**: Yes - configs with invalid values will now fail validation
- **Code changes**: video_censor_personal/config.py (enhanced validate_config function, new validation helpers)
- **Tests**: tests/test_config.py (new test cases for semantic validation)
