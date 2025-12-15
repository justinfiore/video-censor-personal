# Change: Add detection segments to video file metadata as skip chapters

## Why

Media players like VLC, Plex, and others support skip chapter markers embedded in MP4 metadata. By writing detection segments into the video file's chapter metadata, users can jump between flagged content sections directly in their favorite media player without needing external tools or JSON analysis. This makes the detection results more accessible and actionable for non-technical users.

## What Changes

- Add configurable mode `video_metadata_skip` to control whether skip chapters are written to output video
- Support reading detection segments and writing them as chapter markers to MP4 files
- Enhance `--output-video` argument to also handle skip chapter output (not just audio remediation)
- Add user warning if `--input` and `--output-video` paths are identical (file overwrite protection)
- Update CLI validation to require `--output-video` when skip chapters mode enabled
- Extend config schema to include video metadata output options

## Impact

- **Affected specs**: `output-generation`, (new) `video-metadata-output`
- **Affected code**: 
  - `cli.py` (argument validation, overwrite warning)
  - `config.py` (config schema extension)
  - `output.py` (new MP4 metadata writing logic)
  - `video_censor_personal.py` (main pipeline flow)
  - `CONFIGURATION_GUIDE.md` (documentation)

- **Breaking changes**: None. Feature is opt-in via config flag.
- **New dependencies**: Potentially `ffmpeg-python` or `pymediainfo` if not already included (to be determined during implementation)
