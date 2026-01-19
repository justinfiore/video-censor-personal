# Change: Add Segment Reviewed State

## Why
Users need a way to track which segments they've reviewed during the editing workflow. Currently there's no way to distinguish reviewed from unreviewed segments, making it difficult to resume work or ensure all segments have been evaluated.

## What Changes
- Add `reviewed: boolean` property to segment JSON (defaults to `false` if absent)
- Add "Reviewed" checkbox in segment details pane (next to Allowed checkbox)
- Auto-mark segment as `reviewed: true` when:
  - Segment is clicked/selected for >1 second
  - Video playback covers the entire segment timespan
- Add async write queue for JSON persistence (batch writes every 5 seconds max)
- Add sync status indicator in bottom-right UI gutter (orange "Pending Changes" / green "Synchronized")
- Add "Reviewed" / "Unreviewed" / "All Review Status" filter option
- Add "Mark All Reviewed" and "Mark All Unreviewed" bulk action buttons
- Migrate existing synchronous `allow` writes to use the new async queue

## Impact
- Affected specs: `segment-review`
- Affected code:
  - `video_censor_personal/ui/segment_manager.py` (Segment dataclass, write queue)
  - `video_censor_personal/ui/segment_details_pane.py` (Reviewed checkbox)
  - `video_censor_personal/ui/segment_list_pane.py` (filter dropdown)
  - `video_censor_personal/ui/preview_editor.py` (sync status indicator, playback tracking)
