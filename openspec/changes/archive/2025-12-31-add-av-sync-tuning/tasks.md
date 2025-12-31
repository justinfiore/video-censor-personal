## 1. Implementation
- [x] 1.1 Add av_sync_offset_ms parameter to PyAVVideoPlayer.__init__()
- [x] 1.2 Store offset as _av_latency_offset (converted to seconds)
- [x] 1.3 Implement set_av_sync_offset(ms) method
- [x] 1.4 Apply offset in render thread drift calculation
- [x] 1.5 Add A/V sync UI controls (input field + Apply button)
- [x] 1.6 Update UI default values to 1500ms
- [x] 1.7 Update UI labels to clarify "positive = delay video"

## 2. Documentation
- [x] 2.1 Create QUICK_AV_SYNC_REFERENCE.md (quick symptom→fix mapping)
- [x] 2.2 Create AV_SYNC_LOGGING.md (detailed logging explanation)
- [x] 2.3 Create TEST_AV_SYNC.md (step-by-step testing procedure)
- [x] 2.4 Create AV_SYNC_TUNING.md (in-depth tuning guide with scenarios)
- [x] 2.5 Create AV_SYNC_TUNING_QUICK.md (condensed tuning guide)
- [x] 2.6 Create IMPLEMENTATION_COMPLETE.md (summary of changes)

## 3. Testing & Validation
- [x] 3.1 Test initialization with custom offset
- [x] 3.2 Test runtime offset adjustment via set_av_sync_offset()
- [x] 3.3 Test UI offset control (input + Apply button)
- [x] 3.4 Verify logs show correct drift calculation with offset
- [x] 3.5 Test with multiple videos (24fps, 30fps, 60fps)
- [x] 3.6 Verify default 1500ms works for typical setups
- [x] 3.7 Document offset range suitable for different systems

## 4. Cleanup & Archive
- [x] 4.1 Verify code compiles and runs
- [x] 4.2 Verify all documentation is accurate and complete
- [x] 4.3 Set default to 1500ms based on testing
- [x] 4.4 Commit changes with descriptive message
- [ ] 4.5 Archive this change to specs/video-playback/spec.md
- [ ] 4.6 Remove top-level AV_SYNC*.md and IMPLEMENTATION_COMPLETE.md files
- [ ] 4.7 Remove temporary test files (test_av_sync_fix.py, test_segment_seek.py) or move to tests/ if useful
