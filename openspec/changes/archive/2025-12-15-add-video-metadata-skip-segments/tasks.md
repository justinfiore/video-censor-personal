# Implementation Tasks: add-video-metadata-skip-segments

## 1. Configuration and Validation

- [ ] 1.1 Extend `config.py` to add `video.metadata_output.skip_chapters` schema
  - Add `enabled: boolean` (default: false)
  - Add optional `name_format` for future chapter naming customization
  - Validate config loads and defaults are applied

- [ ] 1.2 Update CLI validation in `cli.py`
  - When `skip_chapters.enabled=true` and `--output-video` missing, error with guidance
  - When `--output-video` provided but `skip_chapters.enabled=false`, warn user
  - Check if `--input` path equals `--output-video` path; prompt for overwrite confirmation

- [ ] 1.3 Add unit tests for config parsing and CLI validation
  - Test missing `--output-video` with skip chapters enabled
  - Test overwrite warning logic
  - Test config schema validation

## 2. Chapter Writing Implementation

- [ ] 2.1 Create `video_metadata_writer.py` module
  - Implement `write_skip_chapters_to_mp4(input_path, output_path, segments, merged_results)` function
  - Use ffmpeg subprocess to copy video with chapter metadata
  - Handle edge cases: no detections, empty segment list, file I/O errors
  - Log operation progress and errors

- [ ] 2.2 Implement chapter extraction and merging
  - Extract existing chapters from input video using ffmpeg
  - Parse ffmpeg FFMETADATA format
  - Merge existing chapters with skip chapters
  - Sort combined chapter list by start timestamp
  - Handle cases: no existing chapters, no new detections, both present

- [ ] 2.3 Implement chapter metadata formatting
  - Build chapter list from merged segments
  - Format chapter names with "skip:" prefix: `"skip: Category1, Category2, ... [XX%]"`
  - Calculate chapter timestamps from segment start/end times
  - Create ffmpeg FFMETADATA format output

- [ ] 2.4 Add error handling and logging
  - Catch ffmpeg process errors, log clearly
  - Validate output file is readable after write
  - Log warnings for failed metadata writes but continue pipeline

- [ ] 2.5 Unit tests for chapter writing and merging
  - Mock ffmpeg subprocess for extraction and writing
  - Test chapter name formatting with "skip:" prefix and various detection counts
  - Test chapter merging (existing + skip chapters)
  - Test chapter sorting by timestamp
  - Test confidence percentage calculation
  - Test empty detection handling with existing chapters
  - Test cases: no chapters, only skip chapters, merged chapters

## 3. Pipeline Integration

- [ ] 3.1 Update `video_censor_personal.py` main function
  - After JSON output generated, check if `skip_chapters.enabled=true`
  - If enabled, call chapter writer with merged segments and results
  - Handle overwrite prompt before calling chapter writer

- [ ] 3.2 Update `pipeline.py` (if needed) to track merged segments for output
  - Ensure merged segment data is available to output module
  - Pass confidence and labels correctly to chapter writer

- [ ] 3.3 Integration tests
  - End-to-end test with mock video input
  - Verify both JSON and MP4 outputs generated
  - Verify chapter metadata readable by ffmpeg (metadata inspection)

## 4. Documentation

- [ ] 4.1 Update `CONFIGURATION_GUIDE.md`
  - Add `video.metadata_output` section with example
  - Explain skip chapters feature and player compatibility
  - Document `--output-video` requirement when enabled
  - Include example YAML

- [ ] 4.2 Update main `README.md`
  - Add skip chapters feature to feature list
  - Link to CONFIGURATION_GUIDE for setup details

- [ ] 4.3 Create or update `METADATA_OUTPUT.md` (optional)
  - Detailed guide on chapter naming, chapter behavior in different players
  - Tips for VLC, Plex, other popular players

## 5. Testing and Validation

- [ ] 5.1 Manual testing with real MP4 file
  - Generate detections, write chapters, open in VLC
  - Verify chapter markers are visible and seekable
  - Test with various media players if possible

- [ ] 5.2 Edge case testing
  - Empty detection results (no chapters written)
  - Very long segment list (100+ segments)
  - Special characters in category names
  - Large video files (ensure reasonable performance)

- [ ] 5.3 Code coverage
  - Target 80%+ coverage for new modules
  - Update coverage thresholds if changed

## 6. Release Preparation

- [ ] 6.1 Update CHANGELOG/release notes
  - Document new feature, config option, CLI behavior
  - Note external dependency (ffmpeg) requirement

- [ ] 6.2 Example configuration
  - Create `video-censor-skip-chapters.yaml.example`
  - Show full config with skip chapters enabled

- [ ] 6.3 Final validation
  - Run full test suite
  - Check code style (PEP 8, type hints)
  - Verify no breaking changes to existing APIs
