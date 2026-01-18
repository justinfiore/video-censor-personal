# Performance Tuning Guide

This document describes performance optimizations in the Video Censor Personal application and how to troubleshoot performance issues.

## Segment List Pagination

The segment list uses pagination to handle large numbers of segments efficiently.

### How It Works

- Segments are stored in memory but only the current page of widgets is rendered
- Default page size: 20 segments per page
- Navigation automatically updates the visible widgets

### Performance Impact

| Segment Count | Without Pagination | With Pagination (20/page) | Improvement |
|---------------|-------------------|---------------------------|-------------|
| 15 segments   | 15 widgets        | 15 widgets                | N/A         |
| 50 segments   | 50 widgets        | 20 widgets                | 60%         |
| 100 segments  | 100 widgets       | 20 widgets                | 80%         |
| 206 segments  | 206 widgets       | 20 widgets                | 90%         |

### Configuration

The page size can be adjusted programmatically:

```python
segment_list_pane.set_page_size(30)  # Set to 30 items per page
```

## Logging Levels

The application uses hierarchical logging levels to balance verbosity and performance.

### Available Levels

| Level    | Value | Use Case |
|----------|-------|----------|
| INFO     | 20    | General operation status |
| DEBUG    | 10    | Phase transitions, operation timing |
| TRACE    | 5     | Per-item details, frame-by-frame logs |

### Configuration

Set the log level via environment variable:

```bash
# Standard operation
export VIDEO_CENSOR_LOG_LEVEL=INFO

# Development/debugging
export VIDEO_CENSOR_LOG_LEVEL=DEBUG

# Deep troubleshooting
export VIDEO_CENSOR_LOG_LEVEL=TRACE
```

### Log File Size by Level

Expected log sizes for a 206-segment video operation:

| Level | Approximate Size |
|-------|-----------------|
| INFO  | 5-10 KB         |
| DEBUG | 50-100 KB       |
| TRACE | 500+ KB         |

## Audio Loading

Audio is extracted and loaded in a background thread to keep the UI responsive.

### Thread Architecture

1. Main thread: UI rendering, user interaction
2. Audio thread: Extracts audio frames, loads into player

### Optimization Notes

- Audio extraction happens once during video load
- Frames are cached in memory for the duration of playback
- No re-extraction when seeking within the video

## Troubleshooting Slow Performance

### Symptom: UI hangs during segment list load

**Cause**: Too many segments being rendered at once

**Solution**: Pagination is now enabled by default. If you see this issue, ensure you're using the latest version.

### Symptom: Slow audio loading

**Cause**: Large video files require more time for audio extraction

**Solution**: Audio loads in background; wait for completion indicator. Consider using smaller video clips for testing.

### Symptom: Excessive log file size

**Cause**: Log level set too verbose

**Solution**: Set `VIDEO_CENSOR_LOG_LEVEL=INFO` for production use.

## Profiling

### Running the Profiling Script

```bash
python run_scaling_profiling.py
```

This generates synthetic test data with various segment counts and reports timing metrics.

### Key Metrics to Monitor

1. **JSON parsing time**: Should be <100ms for 200 segments
2. **Widget creation time**: Should be <500ms per page (20 segments)
3. **Page navigation time**: Should be <200ms per page switch
4. **Audio extraction time**: Varies by video length (~1s per minute of video)
