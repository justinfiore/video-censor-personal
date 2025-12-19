# Change: Add Video Preview / Editing UI

## Why

Users need a visual interface to review detected segments in video content before applying remediation. The current system outputs JSON detection results, but reviewing and modifying segment status requires manual file editing. A dedicated UI enables users to:

1. Watch video and audio content alongside detection results
2. Visually verify false positives and confirm true positives
3. Mark segments as allowed/not-allowed without JSON manipulation
4. Immediately see changes persisted to the detection file
5. Navigate between segments and understand detection reasoning

## What Changes

- Introduce **Video Player Component**: Synchronized video and audio playback with seeking, volume control, and timeline visualization
- Introduce **Segment List Component**: Scrollable list of detected segments with time ranges, labels, and allow/not-allow indicators
- Introduce **Segment Details Panel**: Display segment metadata (time, duration, labels, confidence, reasoning) with ability to toggle allow status
- Introduce **Three-Pane Layout**: Main video player (center), segment list (left), segment details (bottom)
- Introduce **Keyboard Shortcuts**: Space, arrow keys, A-key for quick navigation and allow toggling
- Introduce **Persistent Segment Updates**: Automatic JSON file persistence on allow/not-allow changes
- Introduce **Framework Selection and Integration**: Evaluate and integrate UI framework + video playback library combination

## Impact

- Affected specs:
  - **desktop-ui**: Expand from bootstrap to include preview-editor functionality
  - **New: video-player**: Requirements for video playback component
  - **New: segment-review**: Requirements for segment list, details, and interactions
  - **New: ui-framework**: Requirements for framework integration (CustomTkinter + python-vlc)

- Affected code:
  - `video_censor_personal/ui/main.py`: Expand DesktopApp with preview editor UI
  - `video_censor_personal/ui/`: Add new modules for video playback, segment management, layout
  - `requirements.txt`: Add python-vlc dependency (CustomTkinter already present)
  - Integration with existing output-generation segment data model

## Framework Decision

**Selected**: CustomTkinter + python-vlc

- **CustomTkinter**: Already integrated in project; modern, cross-platform styling; reduces dependency footprint
- **python-vlc**: Battle-tested video library (VLC's official Python bindings); reliable audio+video sync; supports MP4, MKV, AVI; sub-500ms seeking

## Notes

- This change focuses on **preview/review functionality only**. Full workflow integration (analysis + remediation from UI) will be handled in a separate `ui-full-workflow` change.
- Framework selection is locked in; implementation can proceed directly without prototyping phase.
- Video and audio playback must work reliably on macOS (primary dev platform) and Windows/Linux.
