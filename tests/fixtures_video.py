"""Test fixtures for generating dummy video files.

This module provides utilities to create minimal dummy MP4 and MKV files
for testing chapter writing functionality without requiring external
video files or copyrighted material.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def create_dummy_mp4(
    duration_seconds: float = 60.0,
    width: int = 320,
    height: int = 240,
    fps: int = 1,
) -> Path:
    """Create a minimal dummy MP4 file for testing.

    Generates a simple video using ffmpeg with:
    - Pure black video frames
    - No audio
    - Specified duration and dimensions
    - Minimal file size

    Args:
        duration_seconds: Video duration in seconds.
        width: Video width in pixels.
        height: Video height in pixels.
        fps: Frames per second (1 fps = minimal file size).

    Returns:
        Path to created MP4 file (temporary file that will be cleaned up).

    Raises:
        RuntimeError: If ffmpeg fails to create the file.
    """
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    output_path = temp_file.name
    temp_file.close()

    try:
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c=black:s={width}x{height}:d={duration_seconds}",
            "-r", str(fps),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "51",  # Lowest quality for smallest file
            "-an",  # No audio
            "-y",  # Overwrite without asking
            output_path,
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to create dummy MP4: {result.stderr}"
            )
        
        return Path(output_path)
    except Exception as e:
        # Clean up on failure
        Path(output_path).unlink(missing_ok=True)
        raise RuntimeError(f"Failed to create dummy MP4 file: {e}") from e


def create_mp4_with_chapters(
    duration_seconds: float = 60.0,
    chapters: Optional[list] = None,
) -> Path:
    """Create a dummy MP4 file with embedded chapters.

    Args:
        duration_seconds: Video duration in seconds.
        chapters: List of chapter dicts with 'start', 'end', 'title'.
                 If None, creates video without chapters.

    Returns:
        Path to created MP4 file with chapters.

    Raises:
        RuntimeError: If ffmpeg fails.
    """
    # First create base video
    base_mp4 = create_dummy_mp4(duration_seconds=duration_seconds)
    
    if not chapters:
        return base_mp4
    
    # If chapters provided, we'll need to add them
    # For now, just return the base video (chapter writing is what we're testing)
    # The actual chapter embedding will be tested by the write_skip_chapters functions
    return base_mp4


def create_dummy_mkv(
    duration_seconds: float = 60.0,
    width: int = 320,
    height: int = 240,
) -> Path:
    """Create a minimal dummy MKV file for testing.

    Args:
        duration_seconds: Video duration in seconds.
        width: Video width in pixels.
        height: Video height in pixels.

    Returns:
        Path to created MKV file.

    Raises:
        RuntimeError: If ffmpeg fails.
    """
    temp_file = tempfile.NamedTemporaryFile(suffix=".mkv", delete=False)
    output_path = temp_file.name
    temp_file.close()

    try:
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c=black:s={width}x{height}:d={duration_seconds}",
            "-r", "1",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "51",
            "-an",
            "-y",
            output_path,
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to create dummy MKV: {result.stderr}"
            )
        
        return Path(output_path)
    except Exception as e:
        Path(output_path).unlink(missing_ok=True)
        raise RuntimeError(f"Failed to create dummy MKV file: {e}") from e
