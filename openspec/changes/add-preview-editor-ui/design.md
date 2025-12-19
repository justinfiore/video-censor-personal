# Design: Video Preview / Editing UI

## Context

The Video Censor Personal project needs a desktop UI for reviewing and editing detection results. Users currently receive JSON output with flagged segments but lack visual feedback for verification. The existing codebase has:

- CustomTkinter-based application bootstrap (`video_censor_personal/ui/main.py`)
- Well-defined JSON segment structure with `allow` property support
- CLI-first philosophy ensuring UI is enhancement layer, not requirement
- Cross-platform requirements (macOS primary, Windows/Linux support)

## Goals

- Enable users to visually review detected segments with video and audio playback
- Provide intuitive controls for marking segments as allowed/not-allowed
- Ensure immediate JSON persistence without explicit save button
- Support seamless integration with existing detection pipeline
- Maintain CLI-first design (all UI features accessible from CLI)

## Non-Goals

- Full workflow UI (analysis + remediation from UI) — will be separate `ui-full-workflow` change
- Custom video codecs or format conversions — use standard playback libraries
- Advanced video editing (trimming, cutting, effects) — focus on review and marking only
- Streaming or network playback

## Decisions

### 1. UI Framework Selection: CustomTkinter + python-vlc

**Decision**: Use CustomTkinter (already in project) for UI framework combined with python-vlc for video playback. Prioritize CustomTkinter components throughout the UI.

**Rationale**: 
- CustomTkinter already integrated in project (`video_censor_personal/ui/main.py`), reducing dependencies and leveraging existing patterns
- python-vlc is battle-tested (VLC's official Python bindings), providing robust video+audio playback with seeking
- Tkinter's Tk widgets can host VLC's native video output via windowed rendering
- Reduces framework complexity vs PyQt6/PySide6; aligns with project's preference for simplicity
- Leverages existing investment in CustomTkinter codebase

**Justification**:
- Video+audio playback: python-vlc supports all common formats (MP4, MKV, AVI) with synchronized audio
- Seeking performance: VLC's seeking is sub-500ms, meets responsiveness requirements
- Cross-platform: VLC works on macOS (primary), Windows, Linux without additional configuration
- Code maintainability: Smaller, focused framework stack compared to PyQt6
- Community support: Both CustomTkinter and python-vlc have active communities and documentation

**CustomTkinter Component Strategy**:
- Use **CTkFrame** for all container/pane layouts (segment list, video player, details panel)
- Use **CTkScrollableFrame** for scrollable segment list
- Use **CTkButton** for all interactive buttons (play/pause, skip, allow toggle)
- Use **CTkLabel** for all text displays (timecode, segment info, descriptions)
- Use **CTkSlider** for volume and timeline progress
- Use **CTkCheckBox** for allow/not-allow toggle (alternative to button)
- Use **CTkToplevel** for file dialogs and error/info messages
- Use **CTkCanvas** only for timeline visualization with segment markers (if CustomTkinter provides; fallback to Tkinter Canvas if needed)
- Avoid mixing standard Tkinter widgets; use CustomTkinter equivalents for consistent modern styling

### 2. Data Model: Segment Representation in UI

**Decision**: Load segments directly from JSON output; apply in-memory modifications; persist to JSON on changes.

**Rationale**: 
- Avoids coupling UI to internal detection pipeline
- Users can generate JSON from CLI, load in UI without re-running analysis
- Easy undo (reload from file) if user makes unintended changes
- Clear separation: analysis phase (CLI) → review phase (UI)

**Implications**:
- JSON must be the authoritative source; UI reads and writes same format
- No internal database or state—UI is stateless except for in-memory segment list
- Allow/not-allow toggle is the only mutable field; all other segment data is read-only in UI

### 3. Layout Architecture: Three-Pane Grid (CustomTkinter)

**Decision**: Use CustomTkinter's grid layout system with three distinct regions:
- **Left Pane (20-25% width)**: Segment list (CTkScrollableFrame) 
- **Center Pane (50-60% width)**: Video player with controls (CTkFrame)
- **Bottom Pane (20-25% height)**: Segment details panel (CTkFrame)

**Rationale**:
- Segment list always visible for quick navigation
- Video player dominant visual area for main content
- Details panel shows context without cluttering video area
- Standard web/desktop UI pattern (familiar to users)

**Implementation Approach**:
- Use CustomTkinter CTkFrame containers for each pane
- Use grid geometry manager with row/column weights for proper spacing
- Use CTkScrollableFrame for segment list (built-in scrolling with CustomTkinter styling)
- Resizable panes if CustomTkinter supports (optional enhancement)
- Vertical scroll only for segment list; horizontal scrolling not needed
- Maintain consistent CustomTkinter visual theme across all components

### 4. Video Player Widget Integration

**Decision**: Abstract video playback into a reusable `VideoPlayer` component with clear interface.

**Rationale**:
- Isolates video library complexity from UI layout logic
- Easier to swap implementations if framework choice changes
- Testable in isolation (mock playback for unit tests)

**Interface (pseudo-code)**:
```python
class VideoPlayer:
    def load(self, video_path: str) -> None: ...
    def play(self) -> None: ...
    def pause(self) -> None: ...
    def seek(self, seconds: float) -> None: ...
    def set_volume(self, level: float) -> None: ...  # 0.0-1.0
    def get_current_time(self) -> float: ...  # seconds
    def on_time_changed(callback: Callable) -> None: ...  # for timeline updates
    def set_playback_rate(self, rate: float) -> None: ...  # optional
    def cleanup(self) -> None: ...
```

### 5. Segment List Selection and Highlighting

**Decision**: Single-selection model (one segment selected at a time); highlight follows video playback.

**Rationale**:
- Simpler state management (no multi-select complexity)
- Clear association between UI elements and current segment
- Allows simultaneous updates: user clicks segment → details update AND video seeks
- Current segment auto-highlights as video plays

**Interaction Flow**:
1. User clicks segment in list → segment highlights, details update, video seeks to start time
2. User presses spacebar → video plays from current position
3. As video plays → current segment in list auto-highlights based on playback timestamp
4. User clicks "Allow" button → segment.allow toggled, JSON persisted, list indicator updates

### 6. Immediate Persistence Strategy

**Decision**: Write JSON to disk immediately on any allow/not-allow change (no explicit save).

**Rationale**:
- Users expect changes to persist (web app behavior)
- Eliminates "save" button complexity
- Reduces risk of lost work
- JSON file size is small; disk I/O not a bottleneck

**Error Handling**:
- If write fails, show warning dialog (e.g., "Failed to save segment changes")
- Keep in-memory changes so user can retry or continue reviewing
- Log errors to application log file for debugging

### 7. Keyboard Shortcuts Mapping

**Decision**: Use standard media player + productivity shortcuts.

| Key | Action | Rationale |
|-----|--------|-----------|
| `Space` | Play/Pause | Standard across all media players |
| `←` | Seek back 5 seconds | Arrow keys for temporal navigation |
| `→` | Seek forward 5 seconds | Arrow keys for temporal navigation |
| `↑` | Previous segment | Vertical arrows for list navigation |
| `↓` | Next segment | Vertical arrows for list navigation |
| `A` | Toggle allow | Mnemonic: A for "Allow" |
| `Enter` | Jump to selected segment | Standard activation key |

**Implementation**: Register global application shortcuts; handle in main event loop (framework-dependent).

### 8. JSON File Watching (Optional Enhancement)

**Decision**: Do NOT implement file watching in initial version; it introduces race conditions.

**Rationale**:
- UI is the primary editor; external modifications are rare
- Watching adds complexity (file system events, race conditions)
- Better to leave for future enhancement if users request external workflow

### 9. Current Time Display Format

**Decision**: Display as HH:MM:SS.mmm (human-readable with milliseconds for precision).

**Rationale**:
- HH:MM:SS familiar to users (video players)
- Milliseconds useful for precise timing of short segments
- Example: "00:48:25.500"

### 10. Confidence Score Display

**Decision**: Show as percentage (e.g., "92%") in addition to decimal (e.g., "0.92").

**Rationale**:
- Percentage more intuitive for non-technical users
- Still preserve raw confidence in detailed view if needed

## Risks / Trade-offs

### Risk 1: VLC Integration with Tkinter Windowed Rendering
- **Risk**: Embedding VLC video output in Tkinter window requires special windowed mode; may have platform-specific quirks.
- **Mitigation**: Use python-vlc's windowed rendering (xwindow on Linux, hwnd on Windows, nsview on macOS); test early in implementation; refer to VLC documentation for platform-specific embedding.

### Risk 2: Complexity of Three-Pane Layout
- **Risk**: Layout might be cramped on small screens; resizing/responsiveness adds complexity.
- **Mitigation**: Start with fixed layout; add resizable panes only if user feedback indicates need. Focus on macOS (1366×768 min resolution assumed).

### Risk 3: JSON Persistence Race Conditions
- **Risk**: User performs rapid allow/not-allow toggles; writes overlap or corrupt JSON.
- **Mitigation**: Serialize writes with a queue; ensure atomic writes (write to temp file, rename).

### Risk 4: Performance with Large Segment Lists
- **Risk**: Videos with hundreds of detections could make segment list UI sluggish.
- **Mitigation**: Implement virtual scrolling (render only visible items) if prototyping shows issue; initial target: <100 segments per video.

## Migration Plan

### Phase 1: Core Implementation (This Change - Framework Already Selected)
1. Integrate chosen framework into project
2. Build VideoPlayer abstraction
3. Implement three-pane layout
4. Add segment list with click handling
5. Add segment details panel with allow toggle
6. Add keyboard shortcuts
7. Add JSON persistence on changes
8. Manual testing on macOS

### Phase 2: Cross-Platform Testing (Follow-up PR)
- Test on Windows and Linux; fix platform-specific issues
- Validate video codec support
- Gather user feedback

## Resolved Decisions

1. **Segment list styling for allowed segments**: Checkmark + subtle background color (green for allowed, default for not-allowed).

2. **Playback speed adjustment (0.5x, 2x)**: Yes, supported in initial version.

3. **Segment details panel collapsing/expanding**: Resizable but not collapsible (users can adjust height as needed).

4. **Multi-label segment display**: Show all labels with text wrapping (Option B).

5. **Batch operations**: Yes, support marking all segments with a specific label as allowed/not-allowed.

6. **VLC windowed mode configuration**: Validate correct window ID passing approach for Tkinter canvas/frame during implementation phase; document platform-specific code paths (xwindow on Linux, hwnd on Windows, nsview on macOS).
