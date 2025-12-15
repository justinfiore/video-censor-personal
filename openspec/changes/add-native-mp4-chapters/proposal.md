# Change: Implement Native MP4 Chapter Writing at Container Level

## Why
Current MP4 chapter implementation relies on ffmpeg FFMETADATA format, which is unreliable and marked as deprecated. Analysis of sample MP4 files (`Boston Blue - s01e01 - Pilot.mp4`, `Shifting Gears - s01e04 - Grief.mp4`) shows proper native MP4 chapters stored at the container level with proper timebase and atoms. These chapters work reliably in all media players (VLC, Plex, etc.). Native MP4 chapters should be as reliable as MKV chapters, enabling equal support for both formats.

## What Changes
- Replace FFMETADATA-based MP4 chapter writing with native MP4 container chapter embedding
- Analyze sample file structure to understand MP4 chapter atoms (time_base, start, end, tags)
- Implement ffmpeg-based or direct container-level chapter writing for MP4
- Remove "DEPRECATED" warnings for MP4 chapters once native method is proven reliable
- Support both MKV and native MP4 chapters equally without degradation warnings
- **BREAKING**: MP4 chapters will now work reliably; existing behavior changes from "may not work" to "works reliably"

## Impact
- Affected specs: `output-generation` (chapter writing requirements)
- Affected code:
  - `video_censor_personal/video_metadata_writer.py` - MP4 chapter implementation
  - Config examples and documentation
  - Test suite for MP4 chapter validation
