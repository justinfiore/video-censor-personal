"""Integration tests for video remediation."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.fixtures_video import create_dummy_mp4
from video_censor_personal.video_remediator import VideoRemediator


@pytest.fixture
def sample_video():
    """Create a sample video for testing."""
    video_path = create_dummy_mp4(duration_seconds=30, width=1920, height=1080, fps=1)
    yield video_path
    # Cleanup
    video_path.unlink(missing_ok=True)


class TestBlankModeIntegration:
    """Integration tests for blank mode video remediation."""
    
    def test_blank_mode_single_segment(self, sample_video):
        """Test blank mode with single segment end-to-end."""
        remediator = VideoRemediator({
            "enabled": True,
            "mode": "blank",
            "blank_color": "#000000"
        })
        
        segments = [
            {"start_time": "5", "end_time": "10"}
        ]
        
        # Build filter chain
        filter_chain = remediator.build_blank_filter_chain(segments, 1920, 1080)
        
        # Create output file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            output_path = tmp.name
        
        try:
            # Apply filter chain with ffmpeg
            cmd = [
                "ffmpeg",
                "-i", str(sample_video),
                "-filter_complex", filter_chain,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-y",
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0, f"ffmpeg failed: {result.stderr}"
            
            # Verify output file exists and has content
            output = Path(output_path)
            assert output.exists()
            assert output.stat().st_size > 0
            
            # Verify output has same duration as input
            duration_cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                output_path
            ]
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            assert 28.0 <= duration <= 32.0  # Allow some variance
            
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_blank_mode_multiple_segments(self, sample_video):
        """Test blank mode with multiple segments."""
        remediator = VideoRemediator({
            "enabled": True,
            "mode": "blank",
            "blank_color": "#FF0000"
        })
        
        segments = [
            {"start_time": "5", "end_time": "8"},
            {"start_time": "15", "end_time": "20"}
        ]
        
        filter_chain = remediator.build_blank_filter_chain(segments, 1920, 1080)
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            output_path = tmp.name
        
        try:
            cmd = [
                "ffmpeg",
                "-i", str(sample_video),
                "-filter_complex", filter_chain,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-y",
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0, f"ffmpeg failed: {result.stderr}"
            assert Path(output_path).exists()
            
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_blank_mode_custom_color(self, sample_video):
        """Test blank mode with custom color."""
        remediator = VideoRemediator({
            "enabled": True,
            "mode": "blank",
            "blank_color": "#00FF00"  # Green
        })
        
        segments = [
            {"start_time": "10", "end_time": "15"}
        ]
        
        filter_chain = remediator.build_blank_filter_chain(segments, 1920, 1080)
        assert "color=0x00FF00" in filter_chain
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            output_path = tmp.name
        
        try:
            cmd = [
                "ffmpeg",
                "-i", str(sample_video),
                "-filter_complex", filter_chain,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-y",
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0, f"ffmpeg failed: {result.stderr}"
            assert Path(output_path).exists()
            
        finally:
            Path(output_path).unlink(missing_ok=True)
