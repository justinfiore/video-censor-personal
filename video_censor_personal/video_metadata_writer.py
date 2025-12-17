"""Video metadata writing for skip chapter markers.

Provides functionality to write detection segments as chapter markers to video files.
Supports MKV format (native chapter support via mkvmerge) and MP4 format (native chapter
atoms via ffmpeg mov_text codec).
"""

import logging
import re
import subprocess
import tempfile
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def _seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format for chapter timestamps.
    
    Args:
        seconds: Time in seconds as float.
    
    Returns:
        Timestamp string in HH:MM:SS.mmm format.
    """
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    milliseconds = int((seconds - total_seconds) * 1000)
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def _generate_chapter_xml(chapters: List[Dict[str, Any]]) -> str:
    """Generate OGG Theora XML format for MKV chapters.
    
    Generates XML in the format expected by mkvmerge for embedding chapters
    in Matroska files.
    
    Args:
        chapters: List of chapter dictionaries with 'start', 'end', and 'title'.
    
    Returns:
        XML string for mkvmerge chapters input.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Chapters>',
        '  <EditionEntry>',
    ]
    
    for chapter in chapters:
        start = chapter["start"]
        end = chapter["end"]
        title = chapter.get("title", "Chapter")
        
        # Ensure numeric values
        if isinstance(start, str):
            try:
                start = _parse_timestamp_to_seconds(start)
            except ValueError:
                logger.warning(f"Skipping chapter with invalid start: {start}")
                continue
        if isinstance(end, str):
            try:
                end = _parse_timestamp_to_seconds(end)
            except ValueError:
                logger.warning(f"Skipping chapter with invalid end: {end}")
                continue
        
        start_ts = _seconds_to_timestamp(float(start))
        end_ts = _seconds_to_timestamp(float(end))
        
        # Escape XML special characters in title
        title_escaped = (
            title.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
        
        lines.append("    <ChapterAtom>")
        lines.append(f"      <ChapterTimeStart>{start_ts}</ChapterTimeStart>")
        lines.append(f"      <ChapterTimeEnd>{end_ts}</ChapterTimeEnd>")
        lines.append("      <ChapterDisplay>")
        lines.append(f"        <ChapterString>{title_escaped}</ChapterString>")
        lines.append("      </ChapterDisplay>")
        lines.append("    </ChapterAtom>")
    
    lines.extend([
        '  </EditionEntry>',
        '</Chapters>',
    ])
    
    return "\n".join(lines)


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
    - Nanoseconds (ffmpeg FFMETADATA): "60000000000" → 60.0
    - Milliseconds: "5000" → 5.0
    - Seconds: "5" → 5.0 (small integers)
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
    
    # Try HH:MM:SS or HH:MM:SS.milliseconds format first (has colons)
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
    
    # Try numeric formats - detect based on magnitude
    try:
        value = float(timestamp_str)
        
        # Nanoseconds: very large numbers (> 1e9 means > 1000 seconds, typical video is nanoseconds)
        # ffmpeg FFMETADATA uses nanoseconds when TIMEBASE=1/1000000000
        if value > 1e9:  # > 1 billion = likely nanoseconds
            return value / 1e9
        # Milliseconds: reasonable range (< 1e9 and > 1000 means likely milliseconds for typical videos)
        elif value > 1000:
            return value / 1000.0
        # Otherwise assume seconds
        else:
            return value
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
                        Each should have 'start_time', 'end_time', 'labels', 'confidence', and optional 'allow' flag.

    Returns:
        List of skip chapter dictionaries with 'start', 'end', and 'title' keys.
        Excludes segments marked with 'allow': True.
    """
    skip_chapters = []
    
    for segment in merged_segments:
        # Skip segments marked as allowed
        if segment.get("allow", False):
            logger.debug(
                f"Skipping chapter for segment at {segment['start_time']:.2f}s "
                f"(marked as allowed)"
            )
            continue
        
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


def _check_ffmpeg_version() -> Tuple[int, int, int]:
    """Check ffmpeg version and ensure it meets minimum requirement (2.0+).

    Returns:
        Tuple of (major, minor, patch) version numbers.

    Raises:
        VideoMetadataError: If ffmpeg < 2.0 or ffmpeg not found.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        
        # Parse version from output: "ffmpeg version N-12345-...-g1234567c ..."
        # or "ffmpeg version 2.0 ..."
        match = re.search(r"version (\d+)\.(\d+)(?:\.(\d+))?", result.stdout)
        if not match:
            raise VideoMetadataError("Could not parse ffmpeg version from output")
        
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3)) if match.group(3) else 0
        
        if major < 2:
            raise VideoMetadataError(
                f"ffmpeg {major}.{minor}.{patch} is installed, but ffmpeg >= 2.0 is required for MKV to MP4 conversion. "
                "Please install a newer version:\n"
                "  macOS: brew install ffmpeg\n"
                "  Linux: sudo apt install ffmpeg\n"
                "  Windows: Download from https://ffmpeg.org/download.html"
            )
        
        logger.debug(f"ffmpeg version check: {major}.{minor}.{patch} (OK)")
        return (major, minor, patch)
    
    except subprocess.TimeoutExpired as e:
        raise VideoMetadataError("ffmpeg version check timed out") from e
    except FileNotFoundError as e:
        raise VideoMetadataError(
            "ffmpeg not found. Please install ffmpeg to use MP4 chapter writing.\n"
            "  macOS: brew install ffmpeg\n"
            "  Linux: sudo apt install ffmpeg\n"
            "  Windows: Download from https://ffmpeg.org/download.html"
        ) from e
    except Exception as e:
        raise VideoMetadataError(f"Failed to check ffmpeg version: {e}") from e


def write_skip_chapters_to_mkv(
    input_path: str,
    output_path: str,
    merged_segments: List[Dict[str, Any]],
) -> None:
    """Write detection segments as skip chapter markers to MKV file.

    Uses mkvmerge to embed chapters natively in Matroska format for reliable
    chapter support visible in all media players. Extracts existing chapters
    from input and merges with new skip chapters.

    Args:
        input_path: Path to input video file.
        output_path: Path to output MKV file with chapter metadata.
        merged_segments: List of merged detection segments.
                        Each should have 'start_time', 'end_time', 'labels', and 'confidence'.

    Raises:
        VideoMetadataError: If mkvmerge not found or chapter writing fails.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise VideoMetadataError(f"Input video file not found: {input_path}")
    
    # Check if mkvmerge is available
    try:
        subprocess.run(
            ["mkvmerge", "--version"],
            capture_output=True,
            timeout=5,
            check=True,
        )
    except FileNotFoundError as e:
        raise VideoMetadataError(
            "mkvmerge not found. Please install mkvtoolnix to use chapter writing with MKV format. "
            "On macOS: brew install mkvtoolnix | On Linux: sudo apt-get install mkvtoolnix | On Windows: download from mkvtoolnix.download"
        ) from e
    except subprocess.CalledProcessError as e:
        raise VideoMetadataError(f"mkvmerge check failed: {e}") from e
    
    # If no detections, just copy input to output
    if not merged_segments:
        logger.info(f"No detection segments found. Copying video to {output_path}")
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
        return
    
    # Build skip chapters
    skip_chapters = _build_skip_chapters(merged_segments)
    logger.debug(f"Built {len(skip_chapters)} skip chapters from {len(merged_segments)} segments")
    
    # Extract existing chapters from input
    existing_ffmetadata = _extract_chapters_from_video(input_file)
    existing_chapters = (
        _parse_ffmetadata_chapters(existing_ffmetadata) if existing_ffmetadata else None
    )
    
    if existing_chapters:
        logger.debug(f"Found {len(existing_chapters)} existing chapters in input video")
    
    # Merge chapters
    merged_chapters = _merge_chapters(existing_chapters, skip_chapters)
    logger.debug(f"Merged to {len(merged_chapters)} total chapters")
    
    # Generate chapter XML
    chapter_xml = _generate_chapter_xml(merged_chapters)
    
    # Write chapters to temp file
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False
        ) as chapter_file:
            chapter_file.write(chapter_xml)
            chapter_path = chapter_file.name
        
        logger.debug(f"Written chapters to temporary file: {chapter_path}")
        logger.debug(f"Input file size: {input_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Use mkvmerge to embed chapters
        logger.debug("Starting mkvmerge chapter embedding...")
        start_time = time.time()
        try:
            cmd = [
                "mkvmerge",
                "-o",
                str(output_file),
                "--chapters",
                chapter_path,
                str(input_file),
            ]
            logger.info(f"mkvmerge command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=600,
            )
            elapsed = time.time() - start_time
            logger.info(
                f"Video with skip chapters written to {output_path} (took {elapsed:.1f}s)"
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"mkvmerge error: {error_msg}")
            raise VideoMetadataError(f"Failed to write chapters with mkvmerge: {error_msg}") from e
        except subprocess.TimeoutExpired as e:
            raise VideoMetadataError(
                f"mkvmerge timed out after 600 seconds (file may be too large)"
            ) from e
    finally:
        # Clean up temp chapter file
        try:
            Path(chapter_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary chapter file: {e}")
    
    # Verify output file
    if not output_file.exists():
        raise VideoMetadataError(f"Output video file was not created: {output_path}")
    
    if output_file.stat().st_size == 0:
        raise VideoMetadataError(
            f"Output video file is empty (may indicate mkvmerge error): {output_path}"
        )
    
    logger.info(f"Successfully wrote {len(skip_chapters)} skip chapters to {output_path}")


def write_skip_chapters_to_mp4_native(
    input_path: str,
    output_path: str,
    merged_segments: List[Dict[str, Any]],
) -> None:
    """Write detection segments as skip chapter markers to MP4 file using native atoms.

    Creates native MP4 chapter atoms by:
    1. Creating an intermediate MKV with chapters using mkvmerge
    2. Converting the MKV to MP4 via ffmpeg, which preserves chapters as native atoms
    
    This ensures chapters are visible as native MP4 atoms in all media players.

    Args:
        input_path: Path to input video file.
        output_path: Path to output MP4 file with chapter metadata.
        merged_segments: List of merged detection segments.
                        Each should have 'start_time', 'end_time', 'labels', and 'confidence'.

    Raises:
        VideoMetadataError: If chapter writing fails.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    # Check ffmpeg version before proceeding
    _check_ffmpeg_version()
    
    if not input_file.exists():
        raise VideoMetadataError(f"Input video file not found: {input_path}")
    
    # Check if mkvmerge is available
    try:
        subprocess.run(
            ["mkvmerge", "--version"],
            capture_output=True,
            timeout=5,
            check=True,
        )
    except FileNotFoundError as e:
        raise VideoMetadataError(
            "mkvmerge not found. MP4 chapter support requires mkvtoolnix for creating intermediate MKV. "
            "Please install mkvtoolnix:\n"
            "  macOS: brew install mkvtoolnix\n"
            "  Linux: sudo apt-get install mkvtoolnix\n"
            "  Windows: download from mkvtoolnix.download"
        ) from e
    
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
    
    # MP4 chapter handling: When converting MKV→MP4, ffmpeg has a quirk where it forces
    # the first chapter to start at 0.0 if there are no pre-existing chapters.
    # Solution: Only add padding chapters when merging with existing chapters.
    # For pure skip chapters with no existing chapters, we accept the ffmpeg behavior of starting at 0.
    chapters_for_mp4 = merged_chapters
    if existing_chapters and merged_chapters and merged_chapters[0].get("start", 0) > 0:
        # Add padding chapter only when merging with existing chapters to preserve all timing
        padding_chapter = {
            "start": 0,
            "end": merged_chapters[0]["start"],
            "title": "Start",
        }
        chapters_for_mp4 = [padding_chapter] + merged_chapters
        logger.debug(f"Added padding chapter (0.0-{merged_chapters[0]['start']}s) for ffmpeg MKV→MP4 timing preservation")
    
    # Generate chapter XML for mkvmerge
    chapter_xml = _generate_chapter_xml(chapters_for_mp4)
    
    # Temporary files for intermediate processing
    chapter_file_path = None
    mkv_temp_path = None
    
    try:
        # Write chapter XML to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False
        ) as chapter_file:
            chapter_file.write(chapter_xml)
            chapter_file_path = chapter_file.name
        
        logger.debug(f"Written chapter XML to temporary file: {chapter_file_path}")
        
        # Create temporary MKV with chapters
        mkv_temp_path = str(Path(tempfile.gettempdir()) / f"video_temp_{time.time():.0f}.mkv")
        
        logger.debug("Creating intermediate MKV with chapters using mkvmerge...")
        try:
            cmd_mkvmerge = [
                "mkvmerge",
                "-o", mkv_temp_path,
                "--chapters", chapter_file_path,
                str(input_file),
            ]
            logger.debug(f"mkvmerge command: {' '.join(cmd_mkvmerge)}")
            result = subprocess.run(
                cmd_mkvmerge,
                check=True,
                capture_output=True,
                timeout=600,
            )
            logger.debug(f"Intermediate MKV created: {mkv_temp_path}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"mkvmerge error: {error_msg}")
            raise VideoMetadataError(f"Failed to create intermediate MKV with chapters: {error_msg}") from e
        except subprocess.TimeoutExpired as e:
            raise VideoMetadataError(
                f"mkvmerge timed out after 600 seconds (file may be too large)"
            ) from e
        
        # Convert MKV to MP4 with ffmpeg, preserving chapters as native atoms
        logger.debug("Converting intermediate MKV to MP4 with native chapter atoms...")
        start_time = time.time()
        try:
            cmd_ffmpeg = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-i", mkv_temp_path,
                "-c", "copy",  # Copy all codecs unchanged
                "-y",           # Auto-confirm overwrite
                str(output_file),
            ]
            logger.debug(f"ffmpeg command: {' '.join(cmd_ffmpeg)}")
            result = subprocess.run(
                cmd_ffmpeg,
                check=True,
                capture_output=True,
                timeout=600,
            )
            elapsed = time.time() - start_time
            logger.info(
                f"Video with native MP4 chapter atoms written to {output_path} (took {elapsed:.1f}s)"
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"ffmpeg error: {error_msg}")
            raise VideoMetadataError(f"Failed to convert to MP4 with native chapters: {error_msg}") from e
        except subprocess.TimeoutExpired as e:
            raise VideoMetadataError(
                f"ffmpeg conversion timed out after 600 seconds (file may be too large)"
            ) from e
    
    finally:
        # Clean up temporary files
        if chapter_file_path:
            try:
                Path(chapter_file_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary chapter file: {e}")
        
        if mkv_temp_path:
            try:
                Path(mkv_temp_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary MKV file: {e}")
    
    # Verify output file
    if not output_file.exists():
        raise VideoMetadataError(f"Output video file was not created: {output_path}")
    
    if output_file.stat().st_size == 0:
        raise VideoMetadataError(
            f"Output video file is empty (may indicate ffmpeg error): {output_path}"
        )
    
    logger.info(f"Successfully wrote {len(skip_chapters)} skip chapters as native MP4 atoms to {output_path}")


def write_skip_chapters_to_mp4(
    input_path: str,
    output_path: str,
    merged_segments: List[Dict[str, Any]],
) -> None:
    """Write detection segments as skip chapter markers to MP4 file.

    Uses native MP4 container-level chapter atoms for reliable cross-platform support.
    Requires ffmpeg >= 8.0 for stable mov_text codec support.

    Args:
        input_path: Path to input video file.
        output_path: Path to output MP4 file with chapter metadata.
        merged_segments: List of merged detection segments.
                        Each should have 'start_time', 'end_time', 'labels', and 'confidence'.

    Raises:
        VideoMetadataError: If chapter writing fails.
    """
    logger.info("MP4 format detected - using native MP4 atoms for reliable chapter support")
    write_skip_chapters_to_mp4_native(input_path, output_path, merged_segments)


def write_skip_chapters(
    input_path: str,
    output_path: str,
    merged_segments: List[Dict[str, Any]],
) -> None:
    """Write detection segments as chapter markers to video file.

    Automatically detects output format from file extension and routes to
    appropriate implementation:
    - .mkv: Uses mkvmerge for native Matroska chapter support
    - .mp4: Uses ffmpeg with mov_text codec for native MP4 atom support
    - Other: Falls back to MP4 native implementation with warning

    Both MKV and MP4 formats provide reliable cross-platform chapter support in all
    standard media players (VLC, Plex, Windows Media Player, Kodi, etc.).

    Args:
        input_path: Path to input video file.
        output_path: Path to output video file with chapter metadata.
        merged_segments: List of merged detection segments.
                        Each should have 'start_time', 'end_time', 'labels', and 'confidence'.

    Raises:
        VideoMetadataError: If chapter writing fails.
    """
    output_ext = Path(output_path).suffix.lower()
    
    if output_ext == ".mkv":
        logger.info("✓ MKV format detected - using mkvmerge for Matroska chapter support")
        write_skip_chapters_to_mkv(input_path, output_path, merged_segments)
    elif output_ext == ".mp4":
        write_skip_chapters_to_mp4(input_path, output_path, merged_segments)
    else:
        logger.warning(
            f"Unknown video format '{output_ext}'. Using native MP4 implementation. "
            f"For best compatibility, use .mkv or .mp4 extension."
        )
        write_skip_chapters_to_mp4(input_path, output_path, merged_segments)
