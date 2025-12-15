# Change: Fix Chapter Writing with Proper MKV Support

## Why
Current chapter writing implementation uses ffmpeg's FFMETADATA format with MP4, which doesn't write chapters reliably. MKV (Matroska) format has native, robust chapter support that works consistently across all media players. Switching to MKV for chapter output enables reliable navigation to flagged content.

## What Changes
- Switch primary chapter writing implementation to use MKV format instead of MP4
- Implement MKV-specific chapter embedding using `mkvmerge` tool
- Update documentation and config examples to recommend MKV for chapter output
- Maintain backward compatibility by supporting both MP4 (with warning) and MKV (recommended)
- **BREAKING**: Chapter writing is now MKV-optimized; MP4 support degrades gracefully with clear warnings

## Impact
- Affected specs: `output-generation` (chapter writing requirements)
- Affected code:
  - `video_censor_personal/video_metadata_writer.py` - Main chapter writing module
  - `video_censor_personal.py` - Command-line handling and examples
  - `openspec/specs/output-generation/spec.md` - Chapter requirements
