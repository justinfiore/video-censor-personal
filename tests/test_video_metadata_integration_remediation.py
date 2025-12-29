"""Integration tests for video metadata remediation writing to MP4.

Tests end-to-end metadata writing using VideoMuxer with actual ffmpeg calls.
Verifies that:
- Metadata tags are written to MP4 container
- Title is updated correctly
- Metadata can be read back with ffprobe
- All remediation flags are preserved
"""

import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Check if ffmpeg and ffprobe are available
FFMPEG_AVAILABLE = subprocess.run(
    ["ffmpeg", "-version"],
    capture_output=True,
).returncode == 0

FFPROBE_AVAILABLE = subprocess.run(
    ["ffprobe", "-version"],
    capture_output=True,
).returncode == 0


def create_test_video(output_path: str, duration: float = 1.0) -> None:
    """Create a minimal test video using ffmpeg.
    
    Args:
        output_path: Path where test video will be saved.
        duration: Duration in seconds (default: 1.0).
    """
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"testsrc=size=320x240:duration={duration}",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=" + str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-y",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create test video: {result.stderr.decode()}")


def read_video_metadata(video_path: str) -> dict:
    """Read metadata from video file using ffprobe.
    
    Args:
        video_path: Path to video file.
    
    Returns:
        Dictionary of format tags/metadata.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    
    data = json.loads(result.stdout)
    return data.get("format", {}).get("tags", {})


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg not available")
@pytest.mark.skipif(not FFPROBE_AVAILABLE, reason="ffprobe not available")
class TestVideoMetadataIntegration:
    """Integration tests for metadata writing to MP4."""

    def test_mux_with_title_metadata(self):
        """Test that title metadata is written to output video."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test video
            input_video = str(tmpdir / "input.mp4")
            create_test_video(input_video, duration=1.0)
            
            # Create fake audio
            audio_file = str(tmpdir / "audio.wav")
            subprocess.run([
                "ffmpeg",
                "-f", "lavfi",
                "-i", "sine=frequency=1000:duration=1",
                "-y",
                audio_file,
            ], capture_output=True, check=True, timeout=30)
            
            # Mux with metadata
            from video_censor_personal.video_muxer import VideoMuxer
            
            metadata = {
                "video_censor_personal_config_file": "config.yaml",
                "video_censor_personal_segment_file": "segments.json",
            }
            
            output_video = str(tmpdir / "output.mp4")
            muxer = VideoMuxer(
                input_video,
                audio_file,
                metadata=metadata,
                title="Family Video (Censored)",
            )
            muxer.mux_video(output_video)
            
            # Verify metadata was written
            assert Path(output_video).exists()
            tags = read_video_metadata(output_video)
            
            assert tags.get("title") == "Family Video (Censored)"
            assert tags.get("video_censor_personal_config_file") == "config.yaml"
            assert tags.get("video_censor_personal_segment_file") == "segments.json"

    def test_mux_with_all_remediation_metadata(self):
        """Test that all remediation metadata flags are written correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test video
            input_video = str(tmpdir / "input.mp4")
            create_test_video(input_video, duration=1.0)
            
            # Create fake audio
            audio_file = str(tmpdir / "audio.wav")
            subprocess.run([
                "ffmpeg",
                "-f", "lavfi",
                "-i", "sine=frequency=1000:duration=1",
                "-y",
                audio_file,
            ], capture_output=True, check=True, timeout=30)
            
            # Mux with all metadata
            from video_censor_personal.video_muxer import VideoMuxer
            
            metadata = {
                "video_censor_personal_config_file": "config.yaml",
                "video_censor_personal_segment_file": "segments.json",
                "video_censor_personal_processed_date": "2025-12-29T14:30:45.123-08:00",
                "video_censor_personal_audio_remediation_enabled": "true",
                "video_censor_personal_video_remediation_enabled": "false",
            }
            
            output_video = str(tmpdir / "output.mp4")
            muxer = VideoMuxer(
                input_video,
                audio_file,
                metadata=metadata,
                title="Test Video (Censored)",
            )
            muxer.mux_video(output_video)
            
            # Verify all metadata was written
            tags = read_video_metadata(output_video)
            
            assert tags.get("title") == "Test Video (Censored)"
            assert tags.get("video_censor_personal_config_file") == "config.yaml"
            assert tags.get("video_censor_personal_segment_file") == "segments.json"
            assert tags.get("video_censor_personal_processed_date") == "2025-12-29T14:30:45.123-08:00"
            assert tags.get("video_censor_personal_audio_remediation_enabled") == "true"
            assert tags.get("video_censor_personal_video_remediation_enabled") == "false"

    def test_mux_without_metadata_still_works(self):
        """Test that muxing works when metadata is not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test video
            input_video = str(tmpdir / "input.mp4")
            create_test_video(input_video, duration=1.0)
            
            # Create fake audio
            audio_file = str(tmpdir / "audio.wav")
            subprocess.run([
                "ffmpeg",
                "-f", "lavfi",
                "-i", "sine=frequency=1000:duration=1",
                "-y",
                audio_file,
            ], capture_output=True, check=True, timeout=30)
            
            # Mux without metadata
            from video_censor_personal.video_muxer import VideoMuxer
            
            output_video = str(tmpdir / "output.mp4")
            muxer = VideoMuxer(input_video, audio_file)
            muxer.mux_video(output_video)
            
            # Verify output exists and is valid
            assert Path(output_video).exists()
            assert Path(output_video).stat().st_size > 0

    def test_title_with_special_characters(self):
        """Test that special characters in title are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test video
            input_video = str(tmpdir / "input.mp4")
            create_test_video(input_video, duration=1.0)
            
            # Create fake audio
            audio_file = str(tmpdir / "audio.wav")
            subprocess.run([
                "ffmpeg",
                "-f", "lavfi",
                "-i", "sine=frequency=1000:duration=1",
                "-y",
                audio_file,
            ], capture_output=True, check=True, timeout=30)
            
            # Mux with special character title
            from video_censor_personal.video_muxer import VideoMuxer
            
            special_title = 'La Película: Noche & Día (Censored)'
            output_video = str(tmpdir / "output.mp4")
            muxer = VideoMuxer(
                input_video,
                audio_file,
                title=special_title,
            )
            muxer.mux_video(output_video)
            
            # Verify special characters preserved
            tags = read_video_metadata(output_video)
            assert tags.get("title") == special_title

    def test_metadata_survives_codec_copy(self):
        """Test that metadata is preserved when video codec is copied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test video
            input_video = str(tmpdir / "input.mp4")
            create_test_video(input_video, duration=1.0)
            
            # Create fake audio
            audio_file = str(tmpdir / "audio.wav")
            subprocess.run([
                "ffmpeg",
                "-f", "lavfi",
                "-i", "sine=frequency=1000:duration=1",
                "-y",
                audio_file,
            ], capture_output=True, check=True, timeout=30)
            
            # Mux with metadata (uses -c:v copy internally)
            from video_censor_personal.video_muxer import VideoMuxer
            
            metadata = {
                "test_key": "test_value",
            }
            
            output_video = str(tmpdir / "output.mp4")
            muxer = VideoMuxer(
                input_video,
                audio_file,
                metadata=metadata,
            )
            muxer.mux_video(output_video)
            
            # Verify metadata survived codec copy
            tags = read_video_metadata(output_video)
            assert tags.get("test_key") == "test_value"
