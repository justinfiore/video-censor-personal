"""Video metadata writing for MP4 skip chapter markers.

Provides functionality to write detection segments as chapter markers to MP4 files,
merging with existing chapters if present.
"""

import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VideoMetadataError(Exception):
    """Exception raised for video metadata writing errors."""

    pass


def _format_chapter_name(labels: List[str], confidence: float) -> str:
    """Format a chapter name from detection labels and confidence.

    Args:
        labels: List of detection category labels.
        confidence: Average confidence score (0.0-1.0).

    Returns:
        Formatted chapter name string.
    """
    labels_str = ", ".join(labels)
    confidence_pct = int(round(confidence * 100))
    return f"skip: {labels_str} [{confidence_pct}%]"


def _extract_chapters_from_video(input_path: Path) -> Optional[str]:
    """Extract chapter metadata from video file using ffmpeg.

    Args:
        input_path: Path to input video file.

    Returns:
        FFMETADATA format string with chapters, or None if no chapters exist.

    Raises:
        VideoMetadataError: If ffmpeg extraction fails.
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(input_path),
                "-f",
                "ffmetadata",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        # ffmpeg writes metadata to stdout when format is ffmetadata
        # Check if output contains any chapter data
        if result.stdout and "[CHAPTER" in result.stdout:
            return result.stdout
        
        return None
    except subprocess.TimeoutExpired as e:
        raise VideoMetadataError(f"Chapter extraction timed out for {input_path}") from e
    except FileNotFoundError as e:
        raise VideoMetadataError(
            "ffmpeg not found. Please install ffmpeg to use skip chapters feature."
        ) from e
    except Exception as e:
        raise VideoMetadataError(f"Failed to extract chapters from {input_path}: {e}") from e


def _parse_timestamp_to_seconds(timestamp_str: str) -> float:
    """Parse timestamp from various formats to seconds.
    
    Handles:
    - Milliseconds: "5000" → 5.0
    - HH:MM:SS format: "00:00:05" → 5.0
    - HH:MM:SS.milliseconds: "00:00:05.500" → 5.5
    
    Args:
        timestamp_str: Timestamp string to parse.
    
    Returns:
        Time in seconds as float.
    
    Raises:
        ValueError: If timestamp format is not recognized.
    """
    timestamp_str = timestamp_str.strip()
    
    # Try milliseconds format first
    try:
        return int(timestamp_str) / 1000.0
    except ValueError:
        pass
    
    # Try HH:MM:SS or HH:MM:SS.milliseconds format
    if ":" in timestamp_str:
        parts = timestamp_str.split(":")
        if len(parts) == 3:
            try:
                hours = int(parts[0])
                minutes = int(parts[1])
                # Handle seconds with decimal point
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            except ValueError:
                pass
    
    raise ValueError(f"Could not parse timestamp: {timestamp_str}")


def _parse_ffmetadata_chapters(ffmetadata_str: str) -> List[Dict[str, Any]]:
    """Parse FFMETADATA format to extract existing chapters.

    Args:
        ffmetadata_str: Raw FFMETADATA format string from ffmpeg.

    Returns:
        List of chapter dictionaries with 'start', 'end', and 'title' keys.
    """
    chapters = []
    current_chapter: Optional[Dict[str, Any]] = None
    
    for line in ffmetadata_str.strip().split("\n"):
        line = line.strip()
        
        if not line or line.startswith(";"):
            # Skip empty lines and comments
            continue
        
        if line.startswith("[CHAPTER"):
            # New chapter section: [CHAPTER01]
            if current_chapter is not None and "start" in current_chapter:
                chapters.append(current_chapter)
            current_chapter = {}
        elif line.startswith("TIMEBASE="):
            # Extract timebase if needed (for now, we'll use milliseconds)
            if current_chapter is not None:
                current_chapter["timebase"] = line.split("=", 1)[1]
        elif line.startswith("START="):
            if current_chapter is not None:
                try:
                    timestamp_val = line.split("=", 1)[1]
                    current_chapter["start"] = _parse_timestamp_to_seconds(timestamp_val)
                except ValueError as e:
                    logger.warning(f"Failed to parse START timestamp: {e}")
        elif line.startswith("END="):
            if current_chapter is not None:
                try:
                    timestamp_val = line.split("=", 1)[1]
                    current_chapter["end"] = _parse_timestamp_to_seconds(timestamp_val)
                except ValueError as e:
                    logger.warning(f"Failed to parse END timestamp: {e}")
        elif line.startswith("title="):
            if current_chapter is not None:
                current_chapter["title"] = line.split("=", 1)[1]
    
    # Don't forget the last chapter
    if current_chapter is not None and "start" in current_chapter:
        chapters.append(current_chapter)
    
    return chapters


def _build_skip_chapters(
    merged_segments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build skip chapter list from merged detection segments.

    Args:
        merged_segments: List of merged segment dictionaries from output.merge_segments().
                        Each should have 'start_time', 'end_time', 'labels', and 'confidence'.

    Returns:
        List of skip chapter dictionaries with 'start', 'end', and 'title' keys.
    """
    skip_chapters = []
    
    for segment in merged_segments:
        chapter = {
            "start": segment["start_time"],
            "end": segment["end_time"],
            "title": _format_chapter_name(segment["labels"], segment["confidence"]),
        }
        skip_chapters.append(chapter)
    
    return skip_chapters


def _normalize_chapter_timestamps(chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize all chapter timestamps to numeric seconds.
    
    Ensures all chapters have numeric 'start' and 'end' values (not strings).
    Skips chapters that can't be normalized.
    
    Args:
        chapters: List of chapter dictionaries.
    
    Returns:
        List of chapters with normalized numeric timestamps.
    """
    normalized = []
    
    for chapter in chapters:
        # Skip chapters without start/end
        if "start" not in chapter or "end" not in chapter:
            logger.warning(f"Skipping chapter with missing timestamp: {chapter.get('title', 'unknown')}")
            continue
        
        start = chapter["start"]
        end = chapter["end"]
        
        # Convert to float if string
        if isinstance(start, str):
            try:
                start = _parse_timestamp_to_seconds(start)
            except ValueError as e:
                logger.warning(f"Skipping chapter with unparseable start time: {e}")
                continue
        
        if isinstance(end, str):
            try:
                end = _parse_timestamp_to_seconds(end)
            except ValueError as e:
                logger.warning(f"Skipping chapter with unparseable end time: {e}")
                continue
        
        # Create normalized chapter
        normalized_chapter = {
            "start": float(start),
            "end": float(end),
            "title": chapter.get("title", "Chapter"),
        }
        normalized.append(normalized_chapter)
    
    return normalized


def _merge_chapters(
    existing_chapters: Optional[List[Dict[str, Any]]],
    skip_chapters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge existing chapters with skip chapters, sorted by start time.

    Args:
        existing_chapters: List of existing chapters from video, or None if none exist.
        skip_chapters: List of new skip chapters to add.

    Returns:
        Sorted list of merged chapters with normalized numeric timestamps.
    """
    merged = []
    
    if existing_chapters:
        # Normalize existing chapters to ensure numeric timestamps
        normalized_existing = _normalize_chapter_timestamps(existing_chapters)
        merged.extend(normalized_existing)
    
    # Skip chapters should already be numeric, but normalize to be safe
    normalized_skip = _normalize_chapter_timestamps(skip_chapters)
    merged.extend(normalized_skip)
    
    # Sort by start time
    merged.sort(key=lambda ch: ch.get("start", 0))
    
    return merged


def _generate_ffmetadata(
    chapters: List[Dict[str, Any]],
) -> str:
    """Generate FFMETADATA format string from chapter list.

    Args:
        chapters: List of chapter dictionaries with 'start', 'end', and 'title'.

    Returns:
        FFMETADATA format string.
    """
    lines = [";FFMETADATA1"]
    
    for idx, chapter in enumerate(chapters, 1):
        # Ensure timestamps are numeric
        start = chapter["start"]
        end = chapter["end"]
        
        # Convert to float if needed
        if isinstance(start, str):
            try:
                start = _parse_timestamp_to_seconds(start)
            except ValueError:
                logger.warning(f"Skipping chapter {idx} with invalid start timestamp: {start}")
                continue
        
        if isinstance(end, str):
            try:
                end = _parse_timestamp_to_seconds(end)
            except ValueError:
                logger.warning(f"Skipping chapter {idx} with invalid end timestamp: {end}")
                continue
        
        # FFMETADATA uses milliseconds
        start_ms = int(float(start) * 1000)
        end_ms = int(float(end) * 1000)
        title = chapter.get("title", f"Chapter {idx}")
        
        lines.append(f"[CHAPTER{idx:02d}]")
        lines.append(f"TIMEBASE=1/1000")
        lines.append(f"START={start_ms}")
        lines.append(f"END={end_ms}")
        lines.append(f"title={title}")
    
    return "\n".join(lines)


def write_skip_chapters_to_mp4(
    input_path: str,
    output_path: str,
    merged_segments: List[Dict[str, Any]],
) -> None:
    """Write detection segments as skip chapter markers to MP4 file.

    Extracts any existing chapters from the input video, merges them with
    new skip chapters derived from detection segments, and writes the
    combined metadata to the output MP4 file using ffmpeg re-muxing.

    Args:
        input_path: Path to input video file.
        output_path: Path to output video file with chapter metadata.
        merged_segments: List of merged detection segments from output.merge_segments().
                        Each should have 'start_time', 'end_time', 'labels', and 'confidence'.

    Raises:
        VideoMetadataError: If chapter writing fails.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise VideoMetadataError(f"Input video file not found: {input_path}")
    
    # If no detections, copy input to output with existing chapters preserved
    if not merged_segments:
        logger.info(
            f"No detection segments found. Copying video with existing chapters to {output_path}"
        )
        try:
            subprocess.run(
                ["ffmpeg", "-i", str(input_file), "-c", "copy", str(output_file)],
                check=True,
                capture_output=True,
                timeout=300,
            )
            logger.info(f"Video copied successfully to {output_path}")
        except subprocess.CalledProcessError as e:
            raise VideoMetadataError(
                f"Failed to copy video file: {e.stderr.decode() if e.stderr else str(e)}"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise VideoMetadataError(f"Video copy operation timed out") from e
        return
    
    # Build skip chapters from segments
    skip_chapters = _build_skip_chapters(merged_segments)
    logger.debug(f"Built {len(skip_chapters)} skip chapters from {len(merged_segments)} segments")
    
    # Extract existing chapters
    existing_ffmetadata = _extract_chapters_from_video(input_file)
    existing_chapters = (
        _parse_ffmetadata_chapters(existing_ffmetadata)
        if existing_ffmetadata
        else None
    )
    
    if existing_chapters:
        logger.debug(f"Found {len(existing_chapters)} existing chapters in input video")
    
    # Merge chapters
    merged_chapters = _merge_chapters(existing_chapters, skip_chapters)
    logger.debug(f"Merged to {len(merged_chapters)} total chapters")
    
    # Generate FFMETADATA
    ffmetadata_content = _generate_ffmetadata(merged_chapters)
    
    # Write metadata to temp file and use it with ffmpeg
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as metadata_file:
            metadata_file.write(ffmetadata_content)
            metadata_path = metadata_file.name
        
        logger.debug(f"Written metadata to temporary file: {metadata_path}")
        logger.debug(f"Input file size: {input_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Use ffmpeg to copy video with new metadata
        logger.debug("Starting ffmpeg metadata write (codec copy mode)...")
        start_time = time.time()
        try:
            logger.info(f"ffmpeg command: ffmpeg -i {input_file} -i {metadata_path} -map_metadata 1 -c copy {output_file}")
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",  # Suppress ffmpeg banner
                    "-loglevel", "error",  # Only show errors, suppress all other output
                    "-i",
                    str(input_file),
                    "-i",
                    metadata_path,
                    "-map_metadata",
                    "1",
                    "-c",
                    "copy",
                    "-y",  # Auto-confirm overwrite
                    str(output_file),
                ],
                check=True,
                capture_output=True,
                timeout=600,  # Increased from 300 to 600 seconds (10 minutes) for very large files
            )
            elapsed = time.time() - start_time
            logger.info(f"Video with skip chapters written to {output_path} (took {elapsed:.1f}s)")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"ffmpeg error: {error_msg}")
            raise VideoMetadataError(f"Failed to write video metadata: {error_msg}") from e
        except subprocess.TimeoutExpired as e:
            raise VideoMetadataError(
                f"Video metadata write operation timed out after 600 seconds (file may be too large or disk I/O is very slow)"
            ) from e
    finally:
        # Clean up temp metadata file
        try:
            Path(metadata_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary metadata file: {e}")
    
    # Verify output file is readable
    if not output_file.exists():
        raise VideoMetadataError(f"Output video file was not created: {output_path}")
    
    if output_file.stat().st_size == 0:
        raise VideoMetadataError(
            f"Output video file is empty (may indicate ffmpeg error): {output_path}"
        )
    
    logger.info(
        f"Successfully wrote {len(skip_chapters)} skip chapters to {output_path}"
    )
    logger.info(
        "Note: Chapter markers are written using FFMETADATA format. "
        "Full chapter support may vary by media player and container format. "
        "For best compatibility with chapter navigation, consider using MKV format."
    )
