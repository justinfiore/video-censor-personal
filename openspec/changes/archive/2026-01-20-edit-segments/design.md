# Design: Segment Editing

## Context
The preview editor UI allows users to review detected segments and mark them as allowed/not-allowed. However, detection is imperfect—segments may start too early, end too late, or span multiple distinct events. Users need to adjust segment boundaries and split segments to achieve accurate remediation.

## Goals
- Enable precise adjustment of segment start/end times via visual scrubbers
- Enable precise adjustment via text input (MM:SS:mmm)
- Allow splitting a segment into multiple parts via duplication
- Allow editing segment labels for remediation control
- Provide clear visual feedback for edit mode
- Maintain undo capability via Cancel button

## Non-Goals
- Merging multiple segments (future enhancement)
- Undo/redo stack beyond Cancel (future enhancement)
- Waveform visualization for audio segments (future enhancement)

## Decisions

### Edit Mode State Machine
The UI will have two modes: **View Mode** (default) and **Edit Mode**.

```
[View Mode] --("Edit Segment" click)--> [Edit Mode]
[Edit Mode] --("Cancel" click)--> [View Mode] (discard changes)
[Edit Mode] --("Apply" click)--> [View Mode] (persist changes)
```

**Rationale**: Explicit mode separation prevents accidental modifications and makes it clear when unsaved changes exist.

### Timeline Zoom Behavior
When entering edit mode:
1. Calculate visible range: `[segment.start_time - 30s, segment.end_time + 30s]`
2. Clamp to video bounds `[0, duration]`
3. Render timeline using this zoomed range instead of full video duration

**Rationale**: 30-second buffer provides context while keeping focus on the segment.

### Scrubber Controls
- Two draggable handles on the timeline: **Start Scrubber** (left) and **End Scrubber** (right)
- Scrubbers snap to 100ms increments for precision
- Dragging past current visible bounds adds 30s to that side and re-renders
- Minimum segment duration: 100ms (scrubbers cannot cross)

**Rationale**: 100ms granularity balances precision with usability.

### Time Input Fields
- Format: `MM:SS.mmm` (e.g., `01:23.456`)
- Validation: real-time, highlight invalid input in red
- Sync: bidirectional with scrubbers (update one, other reflects change)

### Playback Behavior in Edit Mode
- Play button starts from current playhead position
- Playback **stops** when reaching the edit mode's visible end time
- This allows reviewing exactly what will be included in the segment

### Segment Duplication
- "Duplicate Segment" creates a copy with same properties
- New segment inserted immediately after original in list
- New segment gets unique ID
- User can then edit each copy independently

### Label Editing
- Show current labels as editable chips/tags
- Allow adding new labels from a dropdown of known labels
- Allow removing labels by clicking X on chip

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Overlapping segments after editing | Allow overlaps—remediation handles priority |
| Accidental changes | Require explicit "Apply" to persist |
| Complex timeline interaction | Use distinct scrubber styling, tooltips |
| Performance with many segments | Only zoom affects rendering; existing pagination handles scale |

## Resolved Questions
- **Should "Duplicate" enter edit mode automatically?** Yes—enters edit mode on the duplicated segment for immediate adjustment.
- **Should there be a "Delete Segment" button?** Yes—available in the Segment Details pane with confirmation dialog.
