"""Segments JSON loading for remediation-only mode."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from video_censor_personal.frame import DetectionResult

logger = logging.getLogger(__name__)


class SegmentsLoadError(Exception):
    """Raised when segments JSON cannot be loaded or is invalid."""


def load_segments_from_json(
    path: str,
    video_path: Optional[str] = None,
    video_duration: Optional[float] = None,
) -> Dict[str, Any]:
    """Load segments from a JSON file produced by a previous analysis run.

    Validates the JSON structure and optionally checks metadata against
    the input video.

    Args:
        path: Path to the segments JSON file.
        video_path: Optional path to input video for filename validation.
        video_duration: Optional video duration for duration validation.

    Returns:
        Dictionary containing:
            - segments: List of segment dictionaries (with numeric timestamps)
            - metadata: Metadata from the JSON file

    Raises:
        SegmentsLoadError: If file cannot be read or has invalid structure.
    """
    json_path = Path(path)
    
    if not json_path.exists():
        raise SegmentsLoadError(f"Segments file not found: {path}")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SegmentsLoadError(f"Invalid JSON in segments file: {e}")
    except IOError as e:
        raise SegmentsLoadError(f"Cannot read segments file: {e}")
    
    if not isinstance(data, dict):
        raise SegmentsLoadError("Segments file must contain a JSON object")
    
    if "segments" not in data:
        raise SegmentsLoadError("Segments file must contain 'segments' array")
    
    if not isinstance(data["segments"], list):
        raise SegmentsLoadError("'segments' must be an array")
    
    if "metadata" not in data:
        raise SegmentsLoadError("Segments file must contain 'metadata' object")
    
    metadata = data["metadata"]
    segments = data["segments"]
    
    validated_segments = _validate_segments(segments)
    _validate_metadata(metadata, video_path, video_duration)
    
    return {
        "segments": validated_segments,
        "metadata": metadata,
    }


def _validate_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate and normalize segment data.

    Ensures each segment has required fields and extracts numeric timestamps.

    Args:
        segments: List of segment dictionaries from JSON.

    Returns:
        List of validated segment dictionaries with numeric timestamps.

    Raises:
        SegmentsLoadError: If required fields are missing.
    """
    validated = []
    
    for i, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise SegmentsLoadError(f"Segment {i} must be an object")
        
        # Prioritize time-string fields (easier to edit by humans)
        start_time = None
        end_time = None
        
        if "start_time" in segment:
            start_time = _parse_time_string(segment["start_time"], f"segment {i} start_time")
        elif "start_time_seconds" in segment:
            start_time = segment.get("start_time_seconds")
        else:
            raise SegmentsLoadError(f"Segment {i} missing start_time or start_time_seconds")
        
        if "end_time" in segment:
            end_time = _parse_time_string(segment["end_time"], f"segment {i} end_time")
        elif "end_time_seconds" in segment:
            end_time = segment.get("end_time_seconds")
        else:
            raise SegmentsLoadError(f"Segment {i} missing end_time or end_time_seconds")
        
        # Calculate duration from start_time and end_time (ignore any duration in input)
        start_float = float(start_time)
        end_float = float(end_time)
        calculated_duration = end_float - start_float
        
        validated_segment = {
            "start_time": start_float,
            "end_time": end_float,
            "duration_seconds": calculated_duration,
            "labels": segment.get("labels", []),
            "description": segment.get("description", ""),
            "confidence": segment.get("confidence", 0.0),
            "detections": segment.get("detections", []),
            "frame_data": segment.get("frame_data"),
            "allow": segment.get("allow", False),
        }
        
        validated.append(validated_segment)
    
    return validated


def _parse_time_string(time_str: str, field_name: str) -> float:
    """Parse HH:MM:SS time string to seconds.

    Args:
        time_str: Time string in HH:MM:SS format.
        field_name: Name of field for error messages.

    Returns:
        Time in seconds.

    Raises:
        SegmentsLoadError: If time string is invalid.
    """
    try:
        parts = time_str.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        elif len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + int(seconds)
        else:
            raise SegmentsLoadError(f"Invalid time format in {field_name}: {time_str}")
    except ValueError:
        raise SegmentsLoadError(f"Invalid time format in {field_name}: {time_str}")


def _validate_metadata(
    metadata: Dict[str, Any],
    video_path: Optional[str] = None,
    video_duration: Optional[float] = None,
) -> None:
    """Validate metadata against input video (warnings only).

    Args:
        metadata: Metadata dictionary from JSON.
        video_path: Optional path to input video for filename validation.
        video_duration: Optional video duration for duration validation.
    """
    if video_path:
        json_file = metadata.get("file", "")
        video_file = Path(video_path).name
        
        if json_file and json_file != video_file:
            logger.warning(
                f"Segments file was generated for '{json_file}' but input video is '{video_file}'. "
                "Proceeding anyway, but results may not match."
            )
    
    if video_duration is not None:
        json_duration = metadata.get("duration_seconds")
        
        if json_duration is not None:
            duration_diff = abs(float(json_duration) - video_duration)
            if duration_diff > 1.0:
                logger.warning(
                    f"Video duration mismatch: segments file says {json_duration:.2f}s, "
                    f"but video is {video_duration:.2f}s. Proceeding anyway."
                )


def segments_to_detections(segments: List[Dict[str, Any]]) -> List[DetectionResult]:
    """Convert segment dictionaries to DetectionResult objects.

    Creates one DetectionResult per label in each segment. Segments with
    'allow: true' are skipped (not converted to detections).

    Args:
        segments: List of segment dictionaries from load_segments_from_json.

    Returns:
        List of DetectionResult objects for remediation.
    """
    detections: List[DetectionResult] = []
    
    for segment in segments:
        if segment.get("allow", False):
            logger.debug(
                f"Skipping allowed segment at {segment['start_time']:.2f}s"
            )
            continue
        
        labels = segment.get("labels", [])
        if not labels:
            labels = ["Unknown"]
        
        for label in labels:
            detection = DetectionResult(
                start_time=segment["start_time"],
                end_time=segment["end_time"],
                label=label,
                confidence=segment.get("confidence", 1.0),
                reasoning=segment.get("description", f"Loaded from segments JSON"),
                description=segment.get("description"),
            )
            detections.append(detection)
    
    logger.info(f"Converted {len(detections)} detections from segments")
    return detections
