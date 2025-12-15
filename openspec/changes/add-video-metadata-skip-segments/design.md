# Video Metadata Skip Segments Design

## Context

The system currently outputs detection results as JSON and optionally remediates audio. There's no way for users to navigate flagged content within their media player. Many media players (VLC, Plex, etc.) support chapter markers embedded in MP4 metadata, making them a natural vehicle for skip information. This design explores how to write detection segments as chapter markers to video files.

## Goals / Non-Goals

### Goals
- Enable users to jump between flagged segments in media players via native chapter markers
- Make detection results accessible without external tools
- Support MP4 as primary format (most compatible with chapter metadata)
- Maintain backward compatibility (opt-in feature)
- Provide user warnings when overwriting input files

### Non-Goals
- Support for non-MP4 formats (MKV, WebM) initially
- Auto-generation of chapter names beyond simple labels
- Streaming to file without full re-muxing (inherent limitation of MP4 format)
- Custom chapter styling or colors

## Decisions

### 1. Chapter Naming and Metadata Structure
**Decision**: Each detection segment becomes a chapter with name format:
```
skip: <category1>, <category2>, ... [<confidence_percent>%]
```

Example: `"skip: Nudity, Sexual Theme [92%]"`

**Rationale**: `skip:` prefix clearly identifies these as skip markers (distinct from original chapters); human-readable in player UI; includes confidence for context.

### 2. Output Mode Configuration
**Decision**: Add `video.metadata_output.skip_chapters.enabled: boolean` to config.

```yaml
output:
  format: "json"
  include_confidence: true
  pretty_print: true

# NEW SECTION
video:
  metadata_output:
    skip_chapters:
      enabled: false  # opt-in, default disabled
```

**Rationale**: Mirrors existing `audio.remediation` pattern; clear opt-in design.

### 3. Output Video Requirement
**Decision**: When `skip_chapters.enabled=true`, `--output-video` is mandatory (similar to audio remediation).

**Rationale**: Consistent with existing design; avoids overwriting input without explicit user intent.

### 4. Overwrite Warning
**Decision**: If `--input` and `--output-video` are identical paths, prompt user for confirmation:
```
WARNING: Output video file matches input file.
This will overwrite the original video.
Continue? (y/n)
```

**Rationale**: Prevents accidental data loss; standard practice for destructive operations.

**Alternative Considered**: Silently allow overwrite—rejected because users may not realize they're destroying original.

### 5. Chapter Merging Strategy
**Decision**: When writing skip chapters to output video:
1. Extract existing chapters from input video using ffmpeg
2. Parse existing chapter list
3. Append new skip chapters to existing chapters (preserving order by timestamp)
4. Write combined chapter list back to output video

If input has no chapters, write only skip chapters. If input has chapters but no detections, copy chapters as-is.

**Rationale**: Preserves original chapter structure (e.g., from video source or previous processing). Skip chapters coexist with user-created or source chapters. Allows for cumulative metadata enrichment.

### 6. Implementation Library
**Decision**: Use `ffmpeg` subprocess (via `subprocess` module) to:
1. Extract chapters from input: `ffmpeg -i input.mp4 -f ffmetadata -`
2. Merge with skip chapters
3. Write combined metadata: `ffmpeg -i input.mp4 -c copy -metadata-file combined_metadata.txt output.mp4`

**Rationale**: ffmpeg is already listed as external dependency; avoids heavy binary dependencies. Chapter metadata is text-based, doesn't require transcoding. ffmpeg's FFMETADATA format is standard and well-documented.

**Alternative Considered**: `pymediainfo` or `pychromecast`—rejected because they don't write metadata.

### 7. Fallback Behavior
**Decision**: If skip chapters write fails (corrupted file, permission denied), error is logged and JSON output still succeeds. User is notified but pipeline doesn't halt.

**Rationale**: Detection results (JSON) are primary output; video metadata is secondary enhancement. Failing gracefully prevents data loss.

### 8. Empty Detections Handling
**Decision**: If no detections found, existing chapters are preserved (file copied with original chapters intact, no new skip chapters added).

**Rationale**: Preserves original chapter structure when no new detections are present. Users always get benefit of original chapters even if analysis finds nothing.

## Risks / Trade-offs

- **Risk**: ffmpeg remuxing is I/O intensive; large video files may take minutes.
  - **Mitigation**: Log progress; document as expected behavior in CONFIGURATION_GUIDE.

- **Risk**: Some players may not handle malformed chapter metadata gracefully.
  - **Mitigation**: Validate chapter data structure before writing; test with VLC and other players.

- **Risk**: User accidentally overwrites input file.
  - **Mitigation**: Require explicit `--input` path != `--output-video` or prompt for confirmation.

- **Risk**: Detection confidence varies widely (0.1–0.99); percentage display may be misleading.
  - **Mitigation**: Document that chapter name reflects per-segment merged confidence (mean of constituent detections).

## Migration Plan

- New feature; no migration needed for existing configs
- Configs without `video.metadata_output` use defaults (disabled)
- Users opt-in by setting `enabled: true` in YAML
- Existing JSON output unaffected

## Open Questions

1. Should chapter duration extend slightly beyond segment end to accommodate media player UI behavior (e.g., 50ms padding)?
   - **Decision for now**: No padding; use exact segment boundaries. Add in future if UX testing shows need.

2. Should failed metadata writes abort the entire pipeline or log warning and continue?
   - **Decision for now**: Log warning and continue (graceful degradation).

3. What chapter numbering scheme? (Auto-increment, timestamp-based, label-based?)
   - **Decision for now**: FFmpeg auto-assigns ordinal chapters; use segment index as additional metadata.
