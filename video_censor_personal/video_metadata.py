"""Video metadata management for remediated output.

Handles:
- Extracting original video metadata (title)
- Building remediation metadata tags (config, segments, timestamp, flags)
- Formatting metadata for ffmpeg command line
- Logging metadata changes
"""

import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def extract_existing_metadata(video_path: str) -> Dict[str, str]:
    """Extract all existing metadata tags from a video file.

    Reads all metadata tags from the input video so they can be preserved
    and merged with new remediation metadata in the output.

    Args:
        video_path: Path to the input video file.

    Returns:
        Dictionary of all existing metadata tags, or empty dict if none found.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            logger.debug(f"ffprobe failed extracting metadata for {video_path}")
            return {}

        import json
        data = json.loads(result.stdout)
        tags = data.get("format", {}).get("tags", {})

        if tags:
            logger.debug(f"Extracted {len(tags)} existing metadata tags from video")
        else:
            logger.debug(f"No existing metadata tags found in video")

        return tags

    except subprocess.TimeoutExpired:
        logger.warning("ffprobe timed out extracting metadata")
        return {}
    except FileNotFoundError:
        logger.warning("ffprobe not available, skipping existing metadata extraction")
        return {}
    except Exception as e:
        logger.warning(f"Error extracting existing metadata: {e}")
        return {}


def extract_original_title(video_path: str) -> Optional[str]:
    """Extract the title metadata from input video.
    
    Uses ffprobe to read the title tag from the video file.
    If no title exists, returns None.
    
    Args:
        video_path: Path to the input video file.
    
    Returns:
        Original video title, or None if not found.
    
    Raises:
        RuntimeError: If ffprobe is not available.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode != 0:
            logger.debug(f"ffprobe failed for {video_path}: {result.stderr}")
            return None
        
        import json
        data = json.loads(result.stdout)
        title = data.get("format", {}).get("tags", {}).get("title")
        
        if title:
            logger.debug(f"Extracted title from video: '{title}'")
        else:
            logger.debug(f"No title found in video metadata")
        
        return title
    
    except subprocess.TimeoutExpired:
        logger.warning("ffprobe timed out extracting title")
        return None
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe not available. Please install ffprobe. "
            "See: https://ffmpeg.org/download.html"
        )
    except Exception as e:
        logger.warning(f"Error extracting title: {e}")
        return None


def create_censored_title(original_title: Optional[str], input_path: str) -> str:
    """Create the censored title by appending " (Censored)".
    
    Rules:
    - If original_title exists and doesn't already end with "(Censored)", append it
    - If original_title exists and already ends with "(Censored)", keep as-is
    - If no original_title, use input filename (without extension) + " (Censored)"
    
    Args:
        original_title: Original video title from metadata, or None.
        input_path: Path to input video file (fallback for filename).
    
    Returns:
        New censored title string.
    """
    if original_title:
        # Don't double-append if already censored
        if original_title.endswith(" (Censored)"):
            new_title = original_title
            logger.debug(f"Title already has (Censored) suffix, keeping as-is: '{new_title}'")
        else:
            new_title = f"{original_title} (Censored)"
            logger.debug(f"Appending (Censored) suffix: '{original_title}' → '{new_title}'")
    else:
        # Use input filename as fallback
        input_filename = Path(input_path).stem  # filename without extension
        new_title = f"{input_filename} (Censored)"
        logger.debug(f"No title in metadata, using filename: '{new_title}'")
    
    return new_title


def build_remediation_metadata(
    config_file: str,
    segment_file: str,
    processed_timestamp: datetime,
    audio_remediation_enabled: bool,
    video_remediation_enabled: bool,
) -> Dict[str, str]:
    """Build remediation metadata tags for MP4 container.
    
    Creates a dictionary of metadata key-value pairs to embed in the output video.
    
    Rules for values:
    - Filenames: Use only basename (not full path)
    - Timestamp: ISO8601 format with timezone
    - Flags: "true" or "false" strings (lowercase)
    
    Args:
        config_file: Path to the config YAML file used for remediation.
        segment_file: Path to the segment JSON file used for remediation.
        processed_timestamp: datetime when remediation started.
        audio_remediation_enabled: Whether audio remediation was enabled.
        video_remediation_enabled: Whether video remediation was enabled.
    
    Returns:
        Dictionary of metadata tags ready for ffmpeg.
    """
    metadata = {}
    
    # Extract basenames (not full paths)
    config_basename = Path(config_file).name
    segment_basename = Path(segment_file).name
    
    # Format timestamp as ISO8601 with timezone
    timestamp_iso = processed_timestamp.isoformat()
    
    # Format boolean flags as lowercase strings
    audio_flag = "true" if audio_remediation_enabled else "false"
    video_flag = "true" if video_remediation_enabled else "false"
    
    # Build metadata dictionary using underscore-separated keys for compatibility
    metadata["video_censor_personal_config_file"] = config_basename
    metadata["video_censor_personal_segment_file"] = segment_basename
    metadata["video_censor_personal_processed_date"] = timestamp_iso
    metadata["video_censor_personal_audio_remediation_enabled"] = audio_flag
    metadata["video_censor_personal_video_remediation_enabled"] = video_flag
    
    return metadata


def format_metadata_for_ffmpeg(metadata: Dict[str, str]) -> list:
    """Format metadata dictionary for ffmpeg command line.
    
    Converts dictionary to list of ffmpeg -metadata arguments.
    Each entry becomes: ["-metadata", "key=value"]
    
    Args:
        metadata: Dictionary of metadata key-value pairs.
    
    Returns:
        List of ffmpeg command arguments (interleaved -metadata and key=value pairs).
    """
    ffmpeg_args = []
    for key, value in metadata.items():
        ffmpeg_args.extend(["-metadata", f"{key}={value}"])
    return ffmpeg_args


def log_metadata(metadata: Dict[str, str], title: Optional[str] = None) -> None:
    """Log all metadata tags and values at DEBUG level.
    
    Args:
        metadata: Dictionary of remediation metadata tags.
        title: Optional new title being set.
    """
    if title:
        logger.debug(f"Setting video metadata: title = '{title}'")
    
    for key, value in metadata.items():
        logger.debug(f"Setting video metadata: {key} = '{value}'")
