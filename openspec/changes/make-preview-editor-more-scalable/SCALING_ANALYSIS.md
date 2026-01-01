# Scaling Analysis: Preview Editor Performance

## Profiling Results

This document contains performance profiling results for the preview editor UI with different video sizes.

### Test Configurations

#### Small Video (15 segments, ~5 minutes)
- **Date**: [To be filled after testing]
- **Hardware**: [To be filled after testing]
- **OS**: [To be filled after testing]

**Timing Breakdown:**
- JSON parsing and segment manager load: [TBD]
- Video player initialization: [TBD]
- Segment list population: [TBD]
- Total initialization: [TBD]

#### Large Video (206 segments, ~1.5 hours)
- **Date**: [To be filled after testing]
- **Hardware**: [To be filled after testing]
- **OS**: [To be filled after testing]

**Timing Breakdown:**
- JSON parsing and segment manager load: [TBD]
- Video player initialization: [TBD]
- Segment list population: [TBD]
- Total initialization: [TBD]

### Bottleneck Analysis

**Primary Bottleneck**: [To be identified by profiling]

**Secondary Bottleneck**: [To be identified by profiling]

### Widget Creation Performance

- **Small video**: [TBD] items in [TBD]s
- **Large video**: [TBD] items in [TBD]s
- **Time per item (small)**: [TBD]ms
- **Time per item (large)**: [TBD]ms

### Recommendations

Based on profiling results, the following optimizations should be prioritized:

1. [TBD]
2. [TBD]
3. [TBD]

## How to Run Profiling

1. Load the preview editor with a video JSON file
2. The profiler will automatically log timing information to `logs/ui.log`
3. Look for lines starting with `[PROFILE]` to see detailed timing breakdown
4. Use `grep "[PROFILE]" logs/ui.log` to extract profiling data

## Log Levels

- **DEBUG**: Phase-level and operation-level timing (e.g., "JSON parsing", "Widget creation")
- **TRACE**: Frame-by-frame details (not yet implemented)

To enable TRACE logging, set environment variable: `export VIDEO_CENSOR_LOG_LEVEL=TRACE`
