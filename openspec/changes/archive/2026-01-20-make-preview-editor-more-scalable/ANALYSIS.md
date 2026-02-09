# Scaling Analysis: Preview Editor Hang with Large Videos

## Problem Statement

The preview editor UI hangs during initial load with large videos (1.5 hours, 206 segments, ~1GB) while working fine with small videos (5 minutes, 15 segments).

**Test Case**: `./launch-ui.sh output-video/NetForce1-1-clean.json`
- Video: 84 minutes (5053.74s), ~1GB
- Segments: 206
- Result: UI unresponsive, appears frozen

## Evidence from Logs

### Timeline of Events

```
15:15:04 - App bundle launch initiated
15:15:05 - ... (app startup)
15:15:15 - Audio extraction begins (PyAV reading audio frames)
15:15:15 - Audio frame logging shows incremental decoding (frames #227300 through #233850)
15:15:18 - Audio extraction complete (236894 frames decoded)
15:15:18 - Audio concatenated into single array (shape=(242579456, 2), dtype=int16)
15:15:18 - Audio loaded into player (5053.74s duration)
15:15:18 - Audio player initialization complete
         - (NO FURTHER LOGGING - UI becomes unresponsive here)
```

**Observation**: Audio loads successfully in ~3 seconds (15:15:15 to 15:15:18). The hang occurs AFTER audio initialization, likely during segment list rendering.

### Log Volume

The log file is **540KB** and contains dense audio frame logging (~2000+ repetitive log lines like "Audio frame #227300: shape=(2, 1024)..."). This suggests:
- **Logging overhead**: 540KB log file with 2000+ frame-level logs indicates significant logging I/O overhead
- **Opportunity**: Moving frame-level logs to TRACE level could reduce logging overhead by 80-90%
- **Audio processing**: Audio completes successfully in ~3s, but logging overhead during extraction adds to total time
- **Real bottleneck**: Likely segment list rendering AFTER audio loads, but logging overhead may also contribute

See [LOGGING_OPTIMIZATION.md](LOGGING_OPTIMIZATION.md) for detailed analysis of logging reduction strategy.

## Root Cause Analysis

### Likely Bottlenecks (in order of probability)

1. **Segment List Widget Creation** (HIGH PROBABILITY)
   - **Scale**: Creating 206 `SegmentListItem` widgets upfront
   - **Impact**: CustomTkinter widget creation involves layout calculation, geometry management, and event binding
   - **Evidence**: 206 segments vs. 15 segments = 13.7x more widgets
   - **Fix**: Virtualize with visible-items-only rendering (~15-30 visible at once)

2. **JSON Parsing and Data Structure Creation** (MEDIUM PROBABILITY)
   - **Scale**: Parsing 206 segments from JSON, creating segment objects
   - **Impact**: Fast in isolation (<100ms), but observable with logging overhead
   - **Evidence**: JSON file is only 6,158 lines (small), so parsing alone is unlikely
   - **Fix**: Profile to confirm; move to background thread if significant

3. **Audio Caching and Frame Indexing** (LOW PROBABILITY)
   - **Scale**: Audio is 242 million samples (2.8GB in memory)
   - **Impact**: Audio load completes successfully per logs; indexing could still block UI
   - **Evidence**: Logs show audio loads in ~3s; unclear if blocking afterward
   - **Fix**: Move frame indexing to background thread; consolidate audio caching

4. **Initial Layout and Rendering Pass** (MEDIUM PROBABILITY)
   - **Scale**: 206 items in a scrollable list triggers full geometry pass
   - **Impact**: Tkinter's geometry manager must calculate positions for all items
   - **Evidence**: Classic Tkinter bottleneck with large item counts
   - **Fix**: Virtualization eliminates this by rendering only visible items

## Performance Targets

Based on user expectations and industry standards:

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Initial UI Display** | < 3 seconds | User sees the window open and can start interacting |
| **Full Segment List Load** | < 10 seconds | User can scroll and select segments without perceived lag |
| **Small Video (15 segments)** | < 500ms | Maintain existing fast performance for small files |
| **Segment Selection Response** | < 100ms | Clicking a segment should select and play immediately |
| **Scroll Smoothness** | 30+ fps | Scrolling large list feels smooth (at least 30 FPS) |

## Proposed Solutions (in priority order)

### 1. Virtualize Segment List (HIGHEST ROI)
- **Effort**: Medium (refactor `SegmentListPaneImpl`)
- **Impact**: 75-85% reduction in widgets, dramatically faster initial rendering
- **Risk**: Low (localized change, minimal threading complexity)
- **Expected Result**: 206-segment load: 500ms-1s (vs. current hang)

### 2. Optimize Audio Loading
- **Effort**: Low (consolidate cache locations, profile audio ops)
- **Impact**: 10-20% improvement if audio processing is blocking
- **Risk**: Very Low (localized to audio player code)
- **Expected Result**: Ensures audio doesn't block UI during segment list rendering

### 3. Background Thread for Segment List (if virtualization insufficient)
- **Effort**: Medium-High (threading, synchronization, progress UI)
- **Impact**: 50% improvement if segment list population is still bottleneck
- **Risk**: Medium (threading introduces complexity, potential race conditions)
- **Expected Result**: UI responsive during background population; user sees progress

## Implementation Plan

1. **Profiling Phase**: Add detailed timing logs to identify exact bottleneck
2. **Virtualization Phase**: Implement scrollable canvas with visible-items-only rendering
3. **Optional Threading Phase**: Move segment list to background if virtualization insufficient
4. **Testing Phase**: Create integration tests with 50, 100, 206+ segment datasets
5. **Validation Phase**: Test with actual 1.5-hour video and verify no regressions

## Validation Criteria

- ✓ UI displays initial window within 3 seconds
- ✓ Segment list fully populated within 10 seconds
- ✓ All user interactions work (selection, playback, marking segments)
- ✓ No memory leaks or unbounded growth
- ✓ Small videos (15 segments) still load in < 500ms
- ✓ Integration tests pass with 200+ segment datasets
