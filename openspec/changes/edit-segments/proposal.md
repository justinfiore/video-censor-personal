# Change: Add Segment Editing Capabilities

## Why
Users need fine-grained control over segment boundaries and labels to accurately tune remediation. Currently, segments can only be marked as allowed/not-allowed, but cannot be modified. This limits the ability to handle segments that are too long, have incorrect boundaries, or need split into multiple parts.

## What Changes
- Add "Edit Segment" mode with dedicated UI for adjusting start/end times
- Add time-range scrubbers to drag segment boundaries visually
- Add text inputs for precise time entry (MM:SS:mmm format)
- Zoom the timeline to segment ± 30 seconds when editing
- Add "Duplicate Segment" functionality to create copies for splitting
- Add ability to edit segment labels
- Stop playback at segment end time when in edit mode
- Expand visible time range when scrubbers are dragged to boundaries

## Impact
- Affected specs: `segment-review` (or new `segment-editing` capability)
- Affected code:
  - `video_censor_personal/ui/segment_details_pane.py` - Add Edit/Duplicate buttons
  - `video_censor_personal/ui/video_player_pane.py` - Add scrubber controls, timeline zoom
  - `video_censor_personal/ui/segment_manager.py` - Add segment mutation/duplication methods
  - `video_censor_personal/ui/preview_editor.py` - Coordinate edit mode state
