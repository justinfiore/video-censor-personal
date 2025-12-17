## 1. Configuration & Validation

- [x] 1.1 Add `remediation.video_editing` schema to YAML config parser
- [x] 1.2 Add validation for global default mode (mode, blank_color)
- [x] 1.3 Add `category_modes` config parsing and validation
- [x] 1.4 Update `--output-video` validation to require when video remediation enabled
- [x] 1.5 Write unit tests for config parsing and validation

## 2. Video Blank Mode Implementation

- [x] 2.1 Implement ffmpeg filter chain builder for blank mode
- [x] 2.2 Handle time range expressions with `between(t,start,end)`
- [x] 2.3 Support configurable blank color (hex to ffmpeg color)
- [x] 2.4 Write unit tests for filter chain generation
- [x] 2.5 Write integration test for blank mode end-to-end

## 3. Video Cut Mode Implementation

- [x] 3.1 Implement segment extraction logic (non-censored segments)
- [x] 3.2 Generate ffmpeg concat demuxer file
- [x] 3.3 Handle keyframe alignment via re-encoding at boundaries
- [x] 3.4 Write unit tests for segment extraction logic
- [x] 3.5 Write integration test for cut mode end-to-end

## 4. Three-Tier Mode Resolution

- [x] 4.1 Parse `video_remediation` field from segment JSON
- [x] 4.2 Implement category-based mode lookup from config
- [x] 4.3 Implement multi-label "most restrictive" mode resolution
- [x] 4.4 Implement three-tier resolution (segment → category → global)
- [x] 4.5 Handle invalid segment mode values (log warning, use fallback)
- [x] 4.6 Write unit tests for mode resolution logic

## 5. Allow Override Integration

- [x] 5.1 Filter segments by `"allow": true` before remediation
- [x] 5.2 Ensure allow takes precedence over segment mode
- [x] 5.3 Write unit tests for allow override filtering

## 6. Combined Audio + Video Remediation

- [x] 6.1 Merge audio and video remediation into single ffmpeg command
- [x] 6.2 Handle different categories for audio vs video
- [x] 6.3 Write integration test for combined remediation

## 7. Error Handling & Edge Cases

- [x] 7.1 Add ffmpeg error handling with stderr capture
- [x] 7.2 Add invalid timecode validation and skip logic
- [x] 7.3 Add disk space check before processing
- [x] 7.4 Write tests for error handling scenarios

## 8. Documentation

- [x] 8.1 Update README with video remediation section
- [x] 8.2 Add YAML config example file (video-censor-video-remediation.yaml.example)
- [x] 8.3 Update CONFIGURATION_GUIDE.md with video remediation section
  - [x] Add Video Remediation Configuration subsection under Video Section
  - [x] Document `remediation.video_editing` config options (enabled, mode, category_modes, blank_color)
  - [x] Document three-tier mode resolution (global → category → segment)
  - [x] Add examples for blank and cut modes
- [x] 8.4 Update QUICK_START.md with video remediation workflow
  - [x] Add "Video Remediation" section after Audio Remediation
  - [x] Document per-segment mode override in JSON editing workflow
  - [x] Add example CLI commands for video remediation
- [x] 8.5 Document `video_remediation` field in JSON output schema
- [x] 8.6 Document supported codecs and limitations

## 9. Pipeline Integration

- [x] 9.1 Import VideoRemediator into AnalysisPipeline
- [x] 9.2 Call video remediation after detection but before audio remediation
- [x] 9.3 Pass detections/segments and config to VideoRemediator
- [x] 9.4 Handle video remediation output path generation
- [x] 9.5 Chain video-remediated output to audio remediation input
- [x] 9.6 Add TRACE logging for video remediation execution
- [x] 9.7 Write integration test for full end-to-end pipeline (video + audio)
- [x] 9.8 Verify logs show video editing operations when enabled

## 10. Comprehensive Permutation Testing

- [x] 10.1 Create test_remediation_permutations.py with all combinations
- [x] 10.2 Test audio only (bleep and silence modes)
- [x] 10.3 Test video only (blank and cut modes)
- [x] 10.4 Test audio + video combinations:
  - [x] Audio bleep + video blank
  - [x] Audio bleep + video cut
  - [x] Audio silence + video blank
  - [x] Audio silence + video cut
- [x] 10.5 Test mixed video modes (category-based blank/cut)
- [x] 10.6 Test edge cases:
  - [x] No detections
  - [x] No output-video path specified
  - [x] Allowed segments (skip remediation)
- [x] 10.7 Test audio/video sync verification
- [x] 10.8 Test logging for all permutations
- [x] 10.9 Fix audio cutting logic to match video cuts exactly
- [x] 10.10 Update tasks to reflect audio remediation before video remediation order
