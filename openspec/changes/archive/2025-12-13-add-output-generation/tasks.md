# Implementation Tasks

## 1. Data Model Implementation

- [x] 1.1 Add DetectionResult dataclass to frame.py (start_time, end_time, label, confidence, reasoning, description, frame_data)
- [x] 1.2 Add time formatting utility functions (format_time with "hms" and "seconds" modes)
- [x] 1.3 Implement DetectionResult validation (confidence 0.0-1.0, end_time >= start_time)

## 2. Segment Merging Implementation

- [x] 2.1 Create output.py module
- [x] 2.2 Implement segment_merge() function to group overlapping/nearby detections
- [x] 2.3 Calculate merged segment properties (start, end, labels, confidence mean, description)
- [x] 2.4 Sort merged segments by start_time for deterministic output

## 3. Summary Statistics

- [x] 3.1 Implement calculate_summary() function
- [x] 3.2 Calculate total_segments_detected
- [x] 3.3 Calculate total_flagged_duration (sum of all segment durations)
- [x] 3.4 Calculate detection_counts per label

## 4. JSON Output Generation

- [x] 4.1 Implement generate_json_output() function respecting config settings
- [x] 4.2 Include/exclude confidence based on config.output.include_confidence
- [x] 4.3 Include/exclude frame data based on config.output.include_frames
- [x] 4.4 Format time fields using dual time format (HH:MM:SS for display, also include seconds)
- [x] 4.5 Build metadata section (file, duration, processed_at, config path)
- [x] 4.6 Build segments section with all detection details
- [x] 4.7 Build summary section with statistics

## 5. File Output

- [x] 5.1 Implement write_output() function to persist JSON to file
- [x] 5.2 Create output directory if needed
- [x] 5.3 Handle file write errors with descriptive messages
- [x] 5.4 Support pretty_print config option

## 6. Testing

- [x] 6.1 Write tests for DetectionResult creation and validation
- [x] 6.2 Write tests for time formatting (HH:MM:SS edge cases, seconds format)
- [x] 6.3 Write tests for segment merging (overlapping, nearby, distant detections)
- [x] 6.4 Write tests for merged segment property calculation
- [x] 6.5 Write tests for summary statistics (empty, single segment, multiple segments)
- [x] 6.6 Write tests for config-driven output (with/without confidence, frames, pretty_print)
- [x] 6.7 Write tests for JSON structure validation (all required fields present)
- [x] 6.8 Write tests for file writing (success, directory creation, error handling)
- [x] 6.9 Write integration tests (end-to-end: create results → merge → output → write)
- [x] 6.10 Run full test suite and ensure 100% pass rate

## 7. Verification

- [x] 7.1 Verify output matches spec JSON schema for sample data
- [x] 7.2 Verify merge_threshold from config is respected
- [x] 7.3 Verify summary statistics are accurate
- [x] 7.4 Verify config options control output content
- [x] 7.5 Run pytest with coverage to ensure new code is covered
