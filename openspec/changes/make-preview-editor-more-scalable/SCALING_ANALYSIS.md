# Scaling Analysis: Preview Editor Performance

## Phase 1: Instrumentation Complete ✓

Detailed profiling and logging has been added to track UI performance. See `PHASE1_IMPLEMENTATION_SUMMARY.md` for complete implementation details.

## How to Collect Profiling Data

### Step 1: Run Preview Editor with Video
```bash
# Standard DEBUG logging (default)
python3 video_censor_personal.py preview-editor video.json

# OR with TRACE logging for detailed frame-by-frame logs
export VIDEO_CENSOR_LOG_LEVEL=TRACE
python3 video_censor_personal.py preview-editor video.json
```

### Step 2: Extract Profiling Results
```bash
# View all profiling logs
grep "\[PROFILE\]" logs/ui.log

# View specific operation
grep "\[PROFILE\] Segment list" logs/ui.log

# View audio profiling
grep "\[PROFILE\] Audio" logs/ui.log

# Get summary at end of load
tail -20 logs/ui.log | grep "\[PROFILE\]"
```

## Log Levels

- **INFO**: General application flow (file loaded, operations started)
- **DEBUG** (Default): Phase-level and operation-level timing measurements
  - Example: `[PROFILE] Segment list: 206 widgets created in 0.50s`
  - File size: ~100-200KB for 206-segment video
  
- **TRACE**: Frame-by-frame and widget-by-widget details
  - Enabled with: `export VIDEO_CENSOR_LOG_LEVEL=TRACE`
  - Example: `[PROFILE] Segment list: created widget 1/206 (id: seg_0000) in 0.002s`
  - File size: 1-5MB for 206-segment video

## Profiling Instrumentation Points

### Preview Editor Startup
- **Phase**: "App Initialization"
  - Window setup, layout creation, keyboard shortcuts
  
### JSON File Loading
- **Phase**: "JSON File Loading"
  - **Operation**: "JSON parsing and segment manager load"
  - **Operation**: "Video player initialization"
  - **Operation**: "Segment list population"
    - Sub-measurements: parsing, widget creation, layout

### Segment List Rendering
- `load_segments()`: Parse JSON into segment objects, filter options
- `_render_segments()`:
  - Destroy old widgets (timing tracked)
  - Create new widgets (per-widget timing at TRACE level)
  - Layout and selection restoration
  - Total time breakdown by phase

### Audio Loading (Background Thread)
- Audio extraction: Decode audio frames (TRACE logs every 100 frames)
- Audio concatenation: Combine frame arrays
- Audio player loading: Load into playback engine
- Total audio initialization time

## Profiling Test Data

Use `run_scaling_profiling.py` to generate synthetic test data:
```bash
python3 run_scaling_profiling.py
```

This creates test JSON files with:
- 15 segments (small video baseline)
- 50 segments (medium)
- 100 segments (large)
- 206 segments (extra large)

Results show timing for JSON parsing and segment operations.

## Phase 2: Paging Implementation Complete ✓

### Summary

Implemented pagination for segment list to limit widget creation from N total segments to 20 segments per page (DEFAULT_PAGE_SIZE = 20).

### Key Changes

1. **Pagination Controls**: Added Previous/Next buttons with page indicator ("Page X of Y")
2. **Efficient Rendering**: Only renders widgets for current page, destroying previous page widgets
3. **Auto-Navigation**: During playback, auto-navigates to page containing active segment
4. **Filter Integration**: Filters reset to page 1 and recalculate total pages
5. **Selection Tracking**: Selection preserved across page changes
6. **Keyboard Shortcuts**: Page Up/Page Down keys for quick navigation

### Expected Performance Improvement

| Segment Count | Old Widget Count | New Widget Count | Reduction |
|---------------|------------------|------------------|-----------|
| 15            | 15               | 15               | 0%        |
| 50            | 50               | 20               | 60%       |
| 100           | 100              | 20               | 80%       |
| 206           | 206              | 20               | 90%       |

**Theoretical improvement for 206-segment video**: ~90% reduction in initial widget creation

### Implementation Details

- `page_size`: 20 segments per page (configurable via `set_page_size()`)
- `current_page`: 0-indexed page number
- `_render_current_page()`: Destroys old widgets, creates new page widgets
- `go_to_page(n)`: Navigate to specific page
- `highlight_segment_at_time()`: Auto-navigates to correct page during playback

### Testing

All 1010 tests pass after paging implementation. Unit tests for segment list pane updated to include pagination attributes.

## Next Steps: Phase 3+ Optimization

If paging alone doesn't meet performance targets:

1. **Background Threading (Section 3)**: Move JSON parsing and widget creation to background thread
2. **Audio Loading Optimization (Section 4)**: Consolidate audio extraction
3. **Integration Tests (Section 5)**: Add timing assertions for large videos

## Reference Files

- **Phase 1 Summary**: `PHASE1_IMPLEMENTATION_SUMMARY.md`
- **Profiling Utility**: `video_censor_personal/ui/performance_profiler.py`
- **Test Script**: `run_scaling_profiling.py`
- **Log Files**: `logs/ui.log` (generated at runtime)
