# Design: Output Generation System

## Context

Detection engines will produce results identifying problematic content with timecodes, labels, and confidence scores. The system must serialize these into JSON that users can understand, filter, and integrate with downstream systems. This requires a data model, merge logic, summary calculation, and flexible formatting.

## Goals / Non-Goals

- **Goals**:
  - Define a standard `DetectionResult` data class for all detection engines to use
  - Merge overlapping or nearby detections based on configurable threshold
  - Calculate summary statistics automatically (segment count, total duration, per-label counts)
  - Honor config settings (include_confidence, include_frames, pretty_print)
  - Support dual time formatting (HH:MM:SS and raw seconds)
  - Write output to file with configurable path
  - Maintain deterministic output (sorted by time, consistent structure)

- **Non-Goals**:
  - Custom output formats beyond JSON (defer CSV/XML to future)
  - Real-time streaming output (batch processing only)
  - Include frame images by default (only when explicitly requested in config)

## Decisions

### Data Model: DetectionResult

```python
@dataclass
class DetectionResult:
    start_time: float        # seconds
    end_time: float          # seconds
    label: str               # Detection category (e.g., "Profanity")
    confidence: float        # 0.0-1.0
    reasoning: str           # Human-readable explanation
    description: Optional[str] = None  # Optional segment description
    frame_data: Optional[bytes] = None # Optional base64-encoded frame
```

Rationale:
- Single detection per result (not a bundle of labels per segment)
- Time in seconds (canonical); formatting happens at output stage
- Reasoning and description support user understanding
- Frame data included conditionally for space efficiency

### Segment Merging Strategy

1. **Input**: List of DetectionResult sorted by start_time
2. **Process**:
   - Group results that overlap or fall within merge_threshold seconds
   - For each group, create a merged segment with:
     - start_time: earliest start
     - end_time: latest end
     - labels: unique labels in group
     - detections: all original detections in group
     - description: concatenate descriptions or generate from labels
     - confidence: mean of group confidences
3. **Rationale**: Prevents output spam from frame-by-frame detections; user-configurable threshold allows flexibility

### Summary Statistics

Calculate after merging:
```python
summary = {
  "total_segments_detected": len(merged_segments),
  "total_flagged_duration": sum of all segment durations,
  "detection_counts": {label: count for each label across all segments}
}
```

Rationale: Gives users quick insight into flagged content volume and distribution

### Config-Driven Output

Honor these config fields:
- `output.include_confidence`: boolean (default: true) - include confidence scores in detections
- `output.include_frames`: boolean (default: false) - include base64 frame data
- `output.pretty_print`: boolean (default: true) - human-readable JSON formatting

Rationale: Users may want minimal output for bandwidth/storage; frame data is expensive

### Time Formatting

Support two formats:
- `HH:MM:SS` - human-readable (for UI, reports)
- `seconds` - machine-readable (for downstream processing)

Implement a format function:
```python
def format_time(seconds: float, fmt: str = "hms") -> str:
    """Format seconds as HH:MM:SS or raw seconds."""
    if fmt == "hms":
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:  # "seconds"
        return str(int(seconds))
```

Rationale: HMS for readability, seconds for machine consumption

## Risks / Trade-offs

- **Risk**: Segment merging may mask fine-grained detection boundaries
  - **Mitigation**: Config threshold lets users control merge aggressiveness; raw detections available if needed

- **Risk**: Including frame data significantly increases output size
  - **Mitigation**: Make include_frames default to false; users opt-in only if needed

- **Risk**: Summary calculation requires full data before writing (not streaming)
  - **Mitigation**: Acceptable for now; future enhancement could stream and update summary

## Migration Plan

1. Implement DetectionResult data class first (no breaking changes)
2. Build output generator in separate module (isolation)
3. Add config-driven formatting (respect user preferences)
4. Integration with CLI happens when detection engine is complete

### Frame Data Structure with Metadata

When `include_frames=true`, frame data includes both pixel data and metadata:

```python
"frame_data": {
  "image": "iVBORw0KGgoAAAANSUhEUgAA...",  # base64-encoded pixels
  "frame_index": 1234,                       # frame number in video
  "timecode_hms": "00:30:45",                # HH:MM:SS format
  "timecode_seconds": 1845.0                 # raw seconds
}
```

Rationale: Downstream tools can display frames with proper labeling without correlating back to segment metadata.

## Decisions Finalized

- **Frame data location**: Per-segment at merge time, using the first detection's frame_data (if available) to represent the initial flagged frame. This reduces output size while maintaining key reference information.
