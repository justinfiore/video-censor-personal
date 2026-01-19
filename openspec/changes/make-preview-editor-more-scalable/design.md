# Design: Preview Editor Scalability

## Context

The preview editor uses CustomTkinter for UI rendering and currently renders all segments upfront via `SegmentListPaneImpl`, creating a widget for each segment. With 15 segments (5-minute video), this completes quickly. With 206 segments (1.5-hour video), widget creation and initial layout calculations block the main thread for an extended period, causing the UI to hang and appear frozen.

The logs indicate:
1. Audio extracts and loads successfully (5053.74s = 84 minutes)
2. The hang occurs after audio loads (presumably during UI rendering)
3. Initial load must complete before any user interaction is possible

## Goals

- **Goals**:
  - UI remains responsive during initial load of 200+ segment videos (target: <3 second initial display, <2 second full segment list load)
  - Maintain feature parity for all use cases (small and large videos)
  - Enable profiling and monitoring of UI performance
  - Prevent regressions with integration tests

- **Non-Goals**:
  - Redesign the UI layout or appearance
  - Change the JSON data model or file format
  - Optimize video frame decoding or analysis

## Decisions

### 1. Virtualization for Segment List

**Decision**: Implement a virtualized/scrollable segment list that renders only visible items + buffer (e.g., 10 above/below viewport).

**Rationale**: 
- Reducing widget creation from 206 to ~30 visible+buffered items cuts rendering overhead by ~85%
- CustomTkinter's Canvas widget supports scrolling natively; can wrap existing `SegmentListItem` renderer
- Low implementation risk; isolated to `segment_list_pane.py`

**Alternatives Considered**:
- Full rewrite with a grid/table widget: Higher risk, longer implementation
- Lazy loading on scroll: Similar outcome but more complex event handling

### 2. Deferred Non-Critical Operations

**Decision**: Defer audio caching and frame indexing to background threads; load audio only once during player initialization.

**Rationale**:
- Audio is extracted once and reused; no need to cache multiple times
- Frame indexing for thumbnails (if implemented later) can load in the background
- Unblocks main thread to handle segment list rendering sooner

**Alternatives Considered**:
- Preload all data synchronously: Current behavior; causes hang
- Stream segments as they load: More complex; minimal UX benefit

### 3. Background Threading for Blocking Operations

**Decision**: Move JSON loading and segment list population to a background thread with progress signaling.

**Rationale**:
- JSON parsing of 206 segments is fast (<100ms), but widget creation is slow
- Background thread can batch widget creation and signal main thread via queue
- Keeps UI responsive and allows for progress indicators

**Alternatives Considered**:
- Incremental rendering (render N items, schedule next batch): Similar approach, requires more careful synchronization

### 4. Performance Profiling & Logging

**Decision**: Add detailed timing logs to identify bottlenecks (audio load, JSON parse, widget creation, layout) and create a performance monitoring utility. Additionally, optimize logging by moving frame-by-frame logs to TRACE level.

**Rationale**:
- Cannot fix what we cannot measure; need phase-transition logs at DEBUG level
- Dense frame-level logs (2000+ audio frame logs in current implementation) cause logging overhead and obscure real issues
- TRACE logs should be available on-demand for deep troubleshooting without impacting normal operation
- Low overhead with log level stratification; can be controlled via environment variable

**Alternatives Considered**:
- Manual profiling with `cProfile`: One-time use, harder to integrate into dev workflow
- Remove logging entirely: Loses diagnostic detail when problems arise
- Keep all logs at DEBUG: Current 540KB log file; adds overhead and noise

### 5. Integration Tests for Large Videos

**Decision**: Create an integration test suite with synthetic 200+ segment datasets and timing assertions.

**Rationale**:
- Prevents regressions when other UI code is modified
- Provides confidence that scaling improvements work as intended
- Tests can be run locally and in CI

**Alternatives Considered**:
- Manual testing only: Doesn't scale; easy to break with future changes

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Virtualization introduces complexity in list management (selection, scrolling) | Start with simple visible-items-only approach; add buffer gradually; extensive testing |
| Background threading introduces race conditions or UI freezes during load | Use queue-based synchronization; keep critical sections small; test with various video sizes |
| Performance improvements plateau (virtualization alone insufficient) | Profiling will show next bottleneck; stay flexible on implementation strategy |
| Tests with synthetic data don't match real-world scenarios | Use real video files when available; create multiple test sizes (50, 100, 206+ segments) |

## Migration Plan

**Phase 1: Profiling & Instrumentation**
- Add detailed timing logs at key points (JSON load, widget creation, layout, render)
- Identify exact bottleneck(s) before optimizing

**Phase 2: Virtualization**
- Refactor `SegmentListPaneImpl` to use scrollable canvas with virtual items
- Implement dynamic widget creation/destruction on scroll events
- Test with small and large videos

**Phase 3: Background Threading** (if needed after Phase 2)
- Move segment list population to background thread
- Add progress callback for UI updates
- Test thread safety and edge cases (file changes during load, cancellation)

**Phase 4: Integration Tests**
- Create test fixtures with 50, 100, 200+ segments
- Add timing assertions: initial UI display < 3s, full load < 10s
- Test on macOS (primary dev platform) and Windows/Linux if feasible

**Phase 5: Documentation & Cleanup**
- Document performance tuning decisions in code comments
- Remove temporary profiling code if not needed long-term
- Update TESTING_GUIDE.md with large-video test procedures

## Open Questions

1. **What is the acceptable initial load time?** (Proposed: <3s to display UI, <10s to fully populate segment list)
2. **Should thumbnails or frame previews be supported?** (Currently not implemented; deferred non-critical op)
3. **Are there other UI components besides the segment list that block on large videos?** (To be determined by profiling)
4. **What is the maximum segment count we need to support?** (Currently aiming for 200+; may scale to 1000+ with virtualization)
