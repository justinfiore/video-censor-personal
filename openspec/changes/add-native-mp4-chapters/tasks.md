# Tasks: Native MP4 Chapter Writing

## 1. Implementation

### 1.1 Create native MP4 chapter writing function
- [ ] Implement ffmpeg version check before any chapter writing
  - [ ] Add `_check_ffmpeg_version()` helper function
  - [ ] Require ffmpeg >= 8.0; fail with error message if version is insufficient
  - [ ] Error message: "ffmpeg 8.0 or later is required for native MP4 chapter support. Install via: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
- [ ] Implement `write_skip_chapters_to_mp4_native()` function in `video_metadata_writer.py`
- [ ] Use ffmpeg with `-c:s mov_text` for native MP4 container atom chapters
- [ ] Handle millisecond timebase (1/1000) to match sample file structure
- [ ] Support extracting existing chapters from input and merging with skip chapters
- [ ] Log debug info about chapter generation and ffmpeg parameters
- [ ] Raise `VideoMetadataError` on subprocess failures with clear messages
- [ ] No FFMETADATA fallback; native MP4 chapters only

### 1.2 Generate MP4 chapter metadata
- [ ] Implement chapter list to ffmpeg subtitle format conversion
- [ ] Use HH:MM:SS.mmm timestamps matching `_seconds_to_timestamp()` format
- [ ] Create temporary subtitle file for ffmpeg input
- [ ] Clean up temporary file in finally block
- [ ] Support merging with existing chapters extracted from input video

### 1.3 Update write_skip_chapters_to_mp4() to use native method
- [ ] Replace FFMETADATA-based implementation with native MP4 method
- [ ] Call `_check_ffmpeg_version()` before any chapter writing
- [ ] Update function docstring to remove "DEPRECATED" warning
- [ ] Replace error-level warning with info-level log about native MP4 support
- [ ] Update logging to indicate native MP4 chapter support is enabled
- [ ] Remove all FFMETADATA code; native-only implementation

### 1.4 Update write_skip_chapters() dispatcher
- [ ] Update docstring to remove "broken/unreliable" language for MP4
- [ ] Update dispatcher comments to indicate MP4 now has native support
- [ ] Update error log message for MP4 format to indicate native support available
- [ ] Remove deprecation guidance that suggested MKV as only reliable option

## 2. Validation and Testing

### 2.1 Test-Driven Development: Native MP4 Chapter Validation Tests
- [x] Create `tests/fixtures_video.py` with dummy MP4/MKV file generators
- [x] Write test file: `tests/test_video_metadata_mp4_native.py` (17 tests, integration tests)
- [x] Implement critical tests that validate native atoms (CURRENTLY FAILING - expected before implementation)
  - [x] `test_mp4_uses_native_atoms_not_ffmetadata()` - FAILS: No native atoms yet
  - [x] `test_mp4_chapter_timebase_milliseconds()` - FAILS: No native atoms
  - [x] `test_mp4_chapter_start_end_integer_milliseconds()` - FAILS: No native atoms
  - [x] `test_mp4_chapter_title_from_native_atoms()` - FAILS: No native atoms in tags
  - [x] `test_mp4_generated_file_readable()` - PASSES: Basic file validity
  - Note: Test status is TDD - tests FAIL until native implementation is complete

### 2.2 Chapter Extraction and Merging Tests
- [x] `test_merge_skip_with_no_existing_chapters()` - FAILS: Expects native atoms not found
  - NOTE: Will PASS once implementation embeds chapters as native atoms
- [x] `test_skip_chapters_sorted_chronologically()` - FAILS: Expects native atoms sorted
  - NOTE: Will PASS once implementation sorts native atoms chronologically

### 2.3 Cross-player compatibility testing (Manual)
- [ ] Manual testing: Test generated MP4 in VLC media player
- [ ] Manual testing: Test generated MP4 in Plex (if available)
- [ ] Manual testing: Test generated MP4 in Windows Media Player or similar
- [ ] Manual testing: Verify chapters are visible and seekable in all players
- [ ] Document any player-specific quirks or limitations found

### 2.4 Edge Case Tests (All Passing - format routing, etc.)
- [x] Test with video containing no detections (chapter passthrough)
- [x] Test with very large chapter counts (50+ chapters)
- [x] Test with special characters in chapter names
- [x] Test MP4 chapters at video boundaries (start/end)
- [x] Test MP4 format routing in write_skip_chapters dispatcher (PASSES)
- [x] Test unknown format graceful handling
- [x] Test confidence percentage formatting in chapter names

## 3. Integration and Updates

### 3.1 Update configuration examples
- [ ] Update `video-censor.yaml.example` to show MP4 as supported option
- [ ] Update `CONFIGURATION_GUIDE.md` to remove MP4 deprecation warning
- [ ] Add example: `output.video.metadata_output.skip_chapters.enabled: true` with `.mp4` output
- [ ] Document that both `.mkv` and `.mp4` formats are equally supported

### 3.2 Update documentation
- [ ] Update `README.md` to indicate MP4 chapter support is now native and reliable
- [ ] Remove "MKV recommended" language; update to "both MKV and MP4 supported"
- [ ] Update any inline docstrings referencing MP4 unreliability
- [ ] Document that native MP4 chapters work in all standard media players

### 3.3 Update inline code comments
- [ ] Remove "FFMETADATA unreliable" comments in `video_metadata_writer.py`
- [ ] Add comments explaining native MP4 atom structure and timebase
- [ ] Document fallback logic (native → FFMETADATA graceful degradation)
- [ ] Add reference to sample files and verification method

## 4. Spec Update

### 4.1 Update output-generation spec
- [ ] MODIFY "Video Metadata Skip Chapters Output" requirement
  - [ ] Update MP4 scenario to indicate native support (remove "degraded" language)
  - [ ] Update to indicate chapters work reliably in all players
  - [ ] Remove warning about MP4 limitations
- [ ] MODIFY "Chapter Format Detection and Routing" requirement
  - [ ] Update MP4 scenario to indicate native MP4 implementation
  - [ ] Remove reference to FFMETADATA as primary method
  - [ ] Add reference to native atom structure and validation

## 5. Cleanup and Deprecation

### 5.1 Remove FFMETADATA from MP4 path
- [ ] Remove `write_skip_chapters_to_mp4()` call to FFMETADATA generation
- [ ] Keep `_generate_ffmetadata()` function for MKV-only or future use (if needed)
- [ ] Add code comment explaining why FFMETADATA is not used for MP4
- [ ] Document decision: "Native MP4 chapters only; no FFMETADATA fallback for MP4"

### 5.2 Update deprecation warnings
- [ ] Remove "MP4 fundamentally broken" warning from code
- [ ] Remove "CHANGE OUTPUT to .mkv" guidance for MP4 format
- [ ] Update logging to indicate MP4 is fully supported format with native atoms

## 6. Quality Assurance

### 6.1 Code review
- [ ] Verify error handling matches MKV implementation patterns
- [ ] Verify logging levels are consistent (info for success, debug for detail, error for failures)
- [ ] Verify subprocess timeout values are reasonable
- [ ] Verify temporary file cleanup is robust

### 6.2 Final validation
- [ ] Run `openspec validate add-native-mp4-chapters --strict`
- [ ] Verify all scenarios in spec deltas pass
- [ ] Run full test suite to ensure no regressions
- [ ] Test with both sample MP4 files to verify against real-world structure

### 6.3 Documentation review
- [ ] Verify QUICK_START.md mentions MP4 as supported option
- [ ] Verify CONFIGURATION_GUIDE.md reflects native MP4 support
- [ ] Verify README reflects equal support for MKV and MP4
- [ ] Verify no lingering references to MP4 unreliability
