"""Video metadata writing for MP4 skip chapter markers.

Provides functionality to write detection segments as chapter markers to MP4 files,
merging with existing chapters if present.
"""

import logging
import subprocess
import tempfile
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
        
        if line.startswith("[CHAPTER"):
            # New chapter section: [CHAPTER01]
            if current_chapter:
                chapters.append(current_chapter)
            current_chapter = {}
        elif line.startswith("TIMEBASE="):
            # Extract timebase if needed (for now, we'll use milliseconds)
            pass
        elif line.startswith("START="):
            if current_chapter is not None:
                # Convert to seconds
                start_ms = int(line.split("=", 1)[1])
                current_chapter["start"] = start_ms / 1000.0
        elif line.startswith("END="):
            if current_chapter is not None:
                # Convert to seconds
                end_ms = int(line.split("=", 1)[1])
                current_chapter["end"] = end_ms / 1000.0
        elif line.startswith("title="):
            if current_chapter is not None:
                current_chapter["title"] = line.split("=", 1)[1]
    
    # Don't forget the last chapter
    if current_chapter:
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


def _merge_chapters(
    existing_chapters: Optional[List[Dict[str, Any]]],
    skip_chapters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge existing chapters with skip chapters, sorted by start time.

    Args:
        existing_chapters: List of existing chapters from video, or None if none exist.
        skip_chapters: List of new skip chapters to add.

    Returns:
        Sorted list of merged chapters.
    """
    merged = []
    
    if existing_chapters:
        merged.extend(existing_chapters)
    
    merged.extend(skip_chapters)
    
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
        # FFMETADATA uses milliseconds
        start_ms = int(chapter["start"] * 1000)
        end_ms = int(chapter["end"] * 1000)
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
        
        # Use ffmpeg to copy video with new metadata
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(input_file),
                    "-i",
                    metadata_path,
                    "-map_metadata",
                    "1",
                    "-c",
                    "copy",
                    str(output_file),
                ],
                check=True,
                capture_output=True,
                timeout=300,
            )
            logger.info(f"Video with skip chapters written to {output_path}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"ffmpeg error: {error_msg}")
            raise VideoMetadataError(f"Failed to write video metadata: {error_msg}") from e
        except subprocess.TimeoutExpired as e:
            raise VideoMetadataError(
                f"Video metadata write operation timed out (file too large?)"
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
