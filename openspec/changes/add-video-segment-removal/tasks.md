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

- [ ] 3.1 Implement segment extraction logic (non-censored segments)
- [ ] 3.2 Generate ffmpeg concat demuxer file
- [ ] 3.3 Handle keyframe alignment via re-encoding at boundaries
- [ ] 3.4 Write unit tests for segment extraction logic
- [ ] 3.5 Write integration test for cut mode end-to-end

## 4. Three-Tier Mode Resolution

- [ ] 4.1 Parse `video_remediation` field from segment JSON
- [ ] 4.2 Implement category-based mode lookup from config
- [ ] 4.3 Implement multi-label "most restrictive" mode resolution
- [ ] 4.4 Implement three-tier resolution (segment → category → global)
- [ ] 4.5 Handle invalid segment mode values (log warning, use fallback)
- [ ] 4.6 Write unit tests for mode resolution logic

## 5. Allow Override Integration

- [ ] 5.1 Filter segments by `"allow": true` before remediation
- [ ] 5.2 Ensure allow takes precedence over segment mode
- [ ] 5.3 Write unit tests for allow override filtering

## 6. Combined Audio + Video Remediation

- [ ] 6.1 Merge audio and video remediation into single ffmpeg command
- [ ] 6.2 Handle different categories for audio vs video
- [ ] 6.3 Write integration test for combined remediation

## 7. Error Handling & Edge Cases

- [ ] 7.1 Add ffmpeg error handling with stderr capture
- [ ] 7.2 Add invalid timecode validation and skip logic
- [ ] 7.3 Add disk space check before processing
- [ ] 7.4 Write tests for error handling scenarios

## 8. Documentation

- [ ] 8.1 Update README with video remediation section
- [ ] 8.2 Add YAML config example file (video-censor-video-remediation.yaml.example)
- [ ] 8.3 Update CONFIGURATION_GUIDE.md with video remediation section
  - [ ] Add Video Remediation Configuration subsection under Video Section
  - [ ] Document `remediation.video_editing` config options (enabled, mode, category_modes, blank_color)
  - [ ] Document three-tier mode resolution (global → category → segment)
  - [ ] Add examples for blank and cut modes
- [ ] 8.4 Update QUICK_START.md with video remediation workflow
  - [ ] Add "Video Remediation" section after Audio Remediation
  - [ ] Document per-segment mode override in JSON editing workflow
  - [ ] Add example CLI commands for video remediation
- [ ] 8.5 Document `video_remediation` field in JSON output schema
- [ ] 8.6 Document supported codecs and limitations
