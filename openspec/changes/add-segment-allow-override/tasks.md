# Implementation Tasks: Add Segment Allow Override

## 1. Output Schema Update
- [ ] 1.1 Update segment JSON schema to include optional `allow` property (boolean)
- [ ] 1.2 Add schema validation tests for `allow` property
- [ ] 1.3 Update JSON output generation to support `allow` field serialization
- [ ] 1.4 Ensure backward compatibility (missing `allow` property defaults to false)

## 2. Audio Remediation Integration
- [ ] 2.1 Update audio remediation pipeline to check `allow` flag before processing
- [ ] 2.2 Skip bleep/silence operations for segments with `"allow": true`
- [ ] 2.3 Add unit tests for allow-flagged segment handling
- [ ] 2.4 Update audio remediation documentation with allow behavior

## 3. Chapter Generation Integration
- [ ] 3.1 Update chapter/skip-point generation to respect `allow` flag
- [ ] 3.2 Exclude allowed segments from chapter markers
- [ ] 3.3 Add unit tests for chapter generation with allowed segments

## 4. CLI/Config Integration
- [ ] 4.1 Verify CLI output correctly includes `allow` property in generated JSON
- [ ] 4.2 Ensure configuration changes don't conflict with allow behavior
- [ ] 4.3 Implement `--allow-all-segments` CLI flag in argument parser
- [ ] 4.4 Thread the flag through to analysis phase (no effect during remediation phase)
- [ ] 4.5 Populate `"allow": true` on all detected segments when flag is used
- [ ] 4.6 Verify flag is ignored when using `--input-segments` (remediation phase)
- [ ] 4.7 Add end-to-end test covering analysis → allow override → remediation

## 5. Documentation
- [ ] 5.1 Update output format documentation with `allow` property description
- [ ] 5.2 Add use case examples to QUICK_START.md or CONFIGURATION_GUIDE.md
- [ ] 5.3 Document backward compatibility behavior

## 6. Testing & Validation
- [ ] 6.1 Unit test: `--allow-all-segments` flag correctly sets all segments to `allow: true`
- [ ] 6.2 Unit test: `--allow-all-segments` has no effect during remediation phase (with `--input-segments`)
- [ ] 6.3 Integration test: Analysis with `--allow-all-segments` → all segments marked allowed
- [ ] 6.4 Integration test: Remediation with allowed segments → no audio changes
- [ ] 6.5 Integration test: false positive workflow (detect → override → remediate)
- [ ] 6.6 Run full test suite to ensure no regressions
- [ ] 6.7 Verify test coverage remains at or above 80%

## 7. CLI Flag Documentation
- [ ] 7.1 Add `--allow-all-segments` flag to CLI help text and README
- [ ] 7.2 Document the flag in QUICK_START.md with use case example
- [ ] 7.3 Add note that flag only applies during analysis phase
- [ ] 7.4 Include example CLI command: `python -m video_censor --input video.mp4 --output segments.json --config config.yaml --allow-all-segments`
- [ ] 7.5 Update project.md with CLI flag documentation
