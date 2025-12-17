## Context

Video Censor currently supports audio remediation (silence/bleep). This change adds video remediation to censor visual content. The implementation must integrate with ffmpeg, handle multiple video codecs, and work alongside existing audio remediation.

**Stakeholders**: End users who want to censor visual content (nudity, violence, etc.)

**Constraints**:
- Must work with common codecs (H.264, H.265, VP9, AV1)
- Must preserve video quality where possible
- Should work in conjunction with audio remediation

## Goals / Non-Goals

**Goals:**
- Implement "blank" mode (replace video with black screen, keep audio playing)
- Implement "cut" mode (remove both audio and video for segment)
- Allow per-mode configuration via YAML
- Respect `"allow": true` segments (skip them)
- Support combining with audio remediation

**Non-Goals:**
- Real-time playback/preview of censored video (future UI feature)
- Custom overlay images or text (only blank/black screen)
- Partial opacity or blur effects (only fully opaque black)

## Decisions

### Decision 1: Support Both Modes (Mode C from project.md)

Implement both "blank" and "cut" modes, user-selectable via YAML config.

**Rationale**: Maximum flexibility for different use cases. "Blank" preserves timing for context-sensitive content; "cut" provides cleaner removal for shorter segments.

**Alternatives Considered**:
- Mode A (blank only): Simpler but limits flexibility
- Mode B (cut only): Causes timing issues, less useful for long-form content

### Decision 2: Three-Tier Mode Resolution

Implement a three-tier hierarchy for determining video remediation mode per segment.

**Rationale**: Different content types may warrant different default treatment (e.g., always cut nudity, but blank violence to preserve context). Users can further override on a per-segment basis after reviewing in the preview UI.

**Precedence** (first match wins):
1. **Segment-level override**: `segment.video_remediation` field in JSON (`"blank"` | `"cut"` | null)
2. **Category-based default**: YAML config per-category mode (e.g., Nudity → cut, Violence → blank)
3. **Global default**: YAML config `remediation.video_editing.mode`

**Note**: If `segment.allow = true`, no remediation is applied regardless of mode.

**JSON Schema (Segment)**:
```json
{
  "start_time": "00:10:30",
  "end_time": "00:10:35",
  "labels": ["Nudity", "Violence"],
  "video_remediation": "cut",  // "blank" | "cut" | null (use category/global default)
  ...
}
```

**YAML Schema (Category Defaults)**:
```yaml
remediation:
  video_editing:
    enabled: true
    mode: "blank"  # Global default
    category_modes:
      Nudity: "cut"
      Violence: "blank"
      Profanity: "cut"
```

**Category Mode Resolution**:
- If segment has multiple labels (e.g., ["Nudity", "Violence"]), use the most restrictive mode
- "cut" is considered more restrictive than "blank" (removes content entirely)
- If no category has a configured mode, fall back to global default

### Decision 3: Use ffmpeg Filter Chains for "Blank" Mode

Use ffmpeg's `drawbox` or `overlay` filters with color source to blank video segments.

**Rationale**: No re-encoding of non-blanked sections possible with filter_complex; preserves quality for untouched portions.

**Implementation**: Build ffmpeg command with `-filter_complex` using `between(t,start,end)` expressions.

### Decision 4: Use Segment Extraction + Concat for "Cut" Mode

Extract non-censored segments using `-ss` and `-to`, then concatenate with concat demuxer.

**Rationale**: Avoids complex filter chains; handles keyframe alignment via re-encoding at boundaries.

**Trade-off**: Requires re-encoding; slightly longer processing time.

### Decision 5: Re-encode by Default

Always re-encode output video to ensure consistency and avoid keyframe artifacts.

**Rationale**: Stream copy is faster but can cause artifacts at cut points and sync issues.

**Trade-off**: Longer processing time; consider future optimization for stream copy in blank-only mode.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Keyframe misalignment causes artifacts | Re-encode at boundaries; accept slight quality loss |
| Long processing time for large videos | Parallel segment processing; progress reporting |
| Codec compatibility issues | Test with H.264, H.265, VP9; document supported codecs |
| Cut mode causes viewer confusion | Document behavior clearly; recommend blank for long-form content |

## Migration Plan

1. Add `remediation.video_editing` config section (non-breaking; defaults to disabled)
2. Users opt-in by enabling in config
3. No changes to existing audio remediation behavior
4. Rollback: Remove config section; no persistent changes

## Open Questions

- [ ] Should "cut" mode produce a separate output video or modify the same one as audio remediation?
  - **Proposed**: Use same `--output-video` path; apply both audio and video remediation in single ffmpeg pass
- [ ] What default blank color? (Proposed: `#000000` black)
- [ ] Should we expose codec/quality settings in config? (Proposed: No, use sensible defaults initially)
