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

## Next Steps: Phase 2+ Optimization

After collecting profiling data:

1. **Identify bottleneck**: Which operation takes the longest?
   - Widget creation? → Implement virtualization (Phase 2)
   - Audio extraction? → Already on background thread, profile further
   - JSON parsing? → Already fast, unlikely to be bottleneck
   - Layout? → Investigate if Canvas/scroll handling is blocking

2. **Measure scalability**: How does timing scale with segment count?
   - Linear scaling → Widget creation time per item
   - Exponential scaling → Layout recalculation or memory issue

3. **Implement optimization**: Based on bottleneck
   - Virtualize segment list if widget creation is bottleneck
   - Move operations to background thread if main-thread blocking
   - Optimize layout if layout time dominates

4. **Measure improvement**: Rerun profiling after optimization
   - Should see reduction in bottleneck operation
   - Measure overall UI responsiveness

## Reference Files

- **Phase 1 Summary**: `PHASE1_IMPLEMENTATION_SUMMARY.md`
- **Profiling Utility**: `video_censor_personal/ui/performance_profiler.py`
- **Test Script**: `run_scaling_profiling.py`
- **Log Files**: `logs/ui.log` (generated at runtime)
