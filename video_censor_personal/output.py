"""Output generation and formatting for detection results."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from video_censor_personal.frame import DetectionResult

logger = logging.getLogger(__name__)


def format_time(seconds: float, fmt: str = "hms") -> str:
    """Format time in seconds to HH:MM:SS.mmm or seconds.

    Args:
        seconds: Time in seconds.
        fmt: Format type ("hms" for HH:MM:SS.mmm with milliseconds, "seconds" for raw seconds).

    Returns:
        Formatted time string.
    """
    if fmt == "seconds":
        return str(int(seconds))

    # HH:MM:SS.mmm format with milliseconds
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    # Use round() to handle floating point precision issues
    milliseconds = round((seconds % 1) * 1000)
    # Handle edge case where rounding gives 1000ms
    if milliseconds >= 1000:
        milliseconds = 0
        secs += 1
        if secs >= 60:
            secs = 0
            minutes += 1
            if minutes >= 60:
                minutes = 0
                hours += 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def merge_segments(
    detections: List[DetectionResult], threshold: float = 2.0
) -> List[Dict[str, Any]]:
    """Merge overlapping or nearby detection results into segments.

    Groups detections that overlap or fall within threshold seconds of each
    other into single merged segments.

    Args:
        detections: List of DetectionResult objects.
        threshold: Time in seconds within which to merge detections.

    Returns:
        List of merged segment dictionaries with aggregated properties.
    """
    if not detections:
        return []

    # Sort by start time
    sorted_detections = sorted(detections, key=lambda d: d.start_time)

    merged = []
    current_group = [sorted_detections[0]]

    for detection in sorted_detections[1:]:
        # Check if detection overlaps or is within threshold of last in group
        last_end = current_group[-1].end_time
        if detection.start_time <= last_end + threshold:
            current_group.append(detection)
        else:
            # Finalize current group and start new one
            merged.append(_build_merged_segment(current_group))
            current_group = [detection]

    # Don't forget the last group
    merged.append(_build_merged_segment(current_group))

    return merged


def _build_merged_segment(detections: List[DetectionResult]) -> Dict[str, Any]:
    """Build a merged segment from a group of detections.

    Args:
        detections: List of DetectionResult objects to merge.

    Returns:
        Dictionary with merged segment properties.
    """
    start_time = min(d.start_time for d in detections)
    end_time = max(d.end_time for d in detections)
    duration = end_time - start_time

    # Collect unique labels
    labels = sorted(set(d.label for d in detections))

    # Average confidence
    avg_confidence = sum(d.confidence for d in detections) / len(detections)

    # Build detections array
    detections_array = [
        {
            "label": d.label,
            "confidence": d.confidence,
            "reasoning": d.reasoning,
        }
        for d in detections
    ]

    # Use first description or generate one
    description = next(
        (d.description for d in detections if d.description), None
    )
    if not description:
        description = f"Detected {', '.join(labels)}"

    # Use frame data from first detection if available
    frame_data = next((d.frame_data for d in detections if d.frame_data), None)

    return {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration,
        "labels": labels,
        "description": description,
        "confidence": avg_confidence,
        "detections": detections_array,
        "frame_data": frame_data,
        "allow": False,  # Default to not allowed (will be remediated)
    }


def calculate_summary(merged_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics from merged segments.

    Args:
        merged_segments: List of merged segment dictionaries.

    Returns:
        Dictionary with summary statistics.
    """
    if not merged_segments:
        return {
            "total_segments_detected": 0,
            "total_flagged_duration": 0,
            "detection_counts": {},
        }

    total_duration = sum(seg["duration_seconds"] for seg in merged_segments)

    detection_counts: Dict[str, int] = {}
    for segment in merged_segments:
        for label in segment["labels"]:
            detection_counts[label] = detection_counts.get(label, 0) + 1

    return {
        "total_segments_detected": len(merged_segments),
        "total_flagged_duration": total_duration,
        "detection_counts": detection_counts,
    }


def generate_json_output(
    merged_segments: List[Dict[str, Any]],
    video_path: str,
    video_duration: float,
    config_path: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate complete JSON output structure.

    Args:
        merged_segments: List of merged segment dictionaries.
        video_path: Path to video file.
        video_duration: Duration of video in seconds.
        config_path: Path to configuration file.
        config: Configuration dictionary.

    Returns:
        Complete output dictionary ready for JSON serialization.
    """
    # Build segments with formatted times
    segments_output = []
    for segment in merged_segments:
        segment_dict = {
            "start_time": format_time(segment["start_time"], "hms"),
            "start_time_seconds": segment["start_time"],
            "end_time": format_time(segment["end_time"], "hms"),
            "end_time_seconds": segment["end_time"],
            "duration_seconds": segment["duration_seconds"],
            "labels": segment["labels"],
            "description": segment["description"],
        }

        # Add confidence if configured
        if config.get("output", {}).get("include_confidence", True):
            segment_dict["confidence"] = segment["confidence"]

        # Add allow flag (always included)
        segment_dict["allow"] = segment.get("allow", False)

        # Build detections array
        detections_array = []
        for detection in segment["detections"]:
            det_dict = {
                "label": detection["label"],
                "reasoning": detection["reasoning"],
            }
            if config.get("output", {}).get("include_confidence", True):
                det_dict["confidence"] = detection["confidence"]
            detections_array.append(det_dict)

        segment_dict["detections"] = detections_array

        # Add frame data if configured and available
        if (
            config.get("output", {}).get("include_frames", False)
            and segment["frame_data"]
        ):
            segment_dict["frame_data"] = segment["frame_data"]

        segments_output.append(segment_dict)

    # Build metadata
    metadata = {
        "file": Path(video_path).name,
        "duration": format_time(video_duration, "hms"),
        "duration_seconds": video_duration,
        "processed_at": datetime.now().isoformat() + "Z",
        "config": Path(config_path).name if config_path else None,
    }

    # Build summary
    summary = calculate_summary(merged_segments)

    return {
        "metadata": metadata,
        "segments": segments_output,
        "summary": summary,
    }


def write_output(
    output_dict: Dict[str, Any],
    output_path: str,
    config: Dict[str, Any],
) -> None:
    """Write JSON output to file.

    Args:
        output_dict: Output dictionary to serialize.
        output_path: Path where JSON should be written.
        config: Configuration dictionary (for pretty_print option).

    Raises:
        IOError: If file cannot be written.
    """
    output_path_obj = Path(output_path)

    # Create directory if needed
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path_obj, "w") as f:
            pretty_print = config.get("output", {}).get("pretty_print", True)
            if pretty_print:
                json.dump(output_dict, f, indent=2)
            else:
                json.dump(output_dict, f)
        logger.info(f"Output written to {output_path}")
    except IOError as e:
        raise IOError(f"Failed to write output to {output_path}: {e}")
