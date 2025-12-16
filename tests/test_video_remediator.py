"""Tests for video remediation functionality."""

import pytest

from video_censor_personal.video_remediator import VideoRemediator


class TestVideoRemediatorInit:
    """Test VideoRemediator initialization and validation."""
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        remediator = VideoRemediator({})
        
        assert remediator.enabled is False
        assert remediator.mode == "blank"
        assert remediator.blank_color == "#000000"
        assert remediator.category_modes == {}
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        config = {
            "enabled": True,
            "mode": "cut",
            "blank_color": "#FF0000",
            "category_modes": {"Nudity": "cut", "Violence": "blank"}
        }
        remediator = VideoRemediator(config)
        
        assert remediator.enabled is True
        assert remediator.mode == "cut"
        assert remediator.blank_color == "#FF0000"
        assert remediator.category_modes == {"Nudity": "cut", "Violence": "blank"}
    
    def test_init_invalid_mode(self):
        """Test initialization with invalid mode."""
        config = {"mode": "invalid"}
        
        with pytest.raises(ValueError, match="Invalid remediation mode"):
            VideoRemediator(config)
    
    def test_init_invalid_category_mode(self):
        """Test initialization with invalid category mode."""
        config = {"category_modes": {"Nudity": "invalid"}}
        
        with pytest.raises(ValueError, match="Invalid mode for category"):
            VideoRemediator(config)
    
    def test_init_invalid_color_no_hash(self):
        """Test initialization with invalid color (missing #)."""
        config = {"blank_color": "000000"}
        
        with pytest.raises(ValueError, match="Invalid hex color"):
            VideoRemediator(config)
    
    def test_init_invalid_color_wrong_length(self):
        """Test initialization with invalid color (wrong length)."""
        config = {"blank_color": "#00"}
        
        with pytest.raises(ValueError, match="Invalid hex color"):
            VideoRemediator(config)
    
    def test_init_invalid_color_non_hex(self):
        """Test initialization with invalid color (non-hex characters)."""
        config = {"blank_color": "#GGGGGG"}
        
        with pytest.raises(ValueError, match="Invalid hex color"):
            VideoRemediator(config)
    
    def test_init_valid_short_color(self):
        """Test initialization with valid short hex color."""
        config = {"blank_color": "#F00"}
        remediator = VideoRemediator(config)
        
        assert remediator.blank_color == "#F00"


class TestHexColorConversion:
    """Test hex color conversion to ffmpeg format."""
    
    def test_hex_to_ffmpeg_color_long_form(self):
        """Test conversion of long-form hex color."""
        remediator = VideoRemediator({})
        
        result = remediator._hex_to_ffmpeg_color("#000000")
        assert result == "0x000000"
        
        result = remediator._hex_to_ffmpeg_color("#FF0000")
        assert result == "0xFF0000"
        
        result = remediator._hex_to_ffmpeg_color("#ABCDEF")
        assert result == "0xABCDEF"
    
    def test_hex_to_ffmpeg_color_short_form(self):
        """Test conversion of short-form hex color."""
        remediator = VideoRemediator({})
        
        result = remediator._hex_to_ffmpeg_color("#000")
        assert result == "0x000000"
        
        result = remediator._hex_to_ffmpeg_color("#F00")
        assert result == "0xFF0000"
        
        result = remediator._hex_to_ffmpeg_color("#ABC")
        assert result == "0xAABBCC"


class TestTimecodeParser:
    """Test timecode parsing."""
    
    def test_parse_timecode_seconds_only(self):
        """Test parsing of seconds-only timecode."""
        remediator = VideoRemediator({})
        
        assert remediator._parse_timecode("10.5") == 10.5
        assert remediator._parse_timecode("0") == 0.0
        assert remediator._parse_timecode("123.456") == 123.456
    
    def test_parse_timecode_mm_ss(self):
        """Test parsing of MM:SS timecode."""
        remediator = VideoRemediator({})
        
        assert remediator._parse_timecode("01:30") == 90.0
        assert remediator._parse_timecode("00:10.5") == 10.5
        assert remediator._parse_timecode("10:00") == 600.0
    
    def test_parse_timecode_hh_mm_ss(self):
        """Test parsing of HH:MM:SS timecode."""
        remediator = VideoRemediator({})
        
        assert remediator._parse_timecode("01:00:00") == 3600.0
        assert remediator._parse_timecode("00:01:30") == 90.0
        assert remediator._parse_timecode("01:30:45.5") == 5445.5
        assert remediator._parse_timecode("00:00:10") == 10.0
    
    def test_parse_timecode_invalid(self):
        """Test parsing of invalid timecode."""
        remediator = VideoRemediator({})
        
        with pytest.raises(ValueError, match="Invalid timecode format"):
            remediator._parse_timecode("invalid")
        
        with pytest.raises(ValueError, match="Invalid timecode format"):
            remediator._parse_timecode(":")


class TestBlankFilterChain:
    """Test ffmpeg filter chain generation for blank mode."""
    
    def test_build_blank_filter_chain_empty(self):
        """Test filter chain with no segments."""
        remediator = VideoRemediator({"mode": "blank"})
        
        result = remediator.build_blank_filter_chain([], 1920, 1080)
        assert result == ""
    
    def test_build_blank_filter_chain_single_segment(self):
        """Test filter chain with single segment."""
        remediator = VideoRemediator({"mode": "blank", "blank_color": "#000000"})
        
        segments = [
            {"start_time": "00:00:10", "end_time": "00:00:15"}
        ]
        result = remediator.build_blank_filter_chain(segments, 1920, 1080)
        
        assert "drawbox=x=0:y=0:w=1920:h=1080" in result
        assert "color=0x000000" in result
        assert "t=fill" in result
        assert "enable='between(t,10.0,15.0)'" in result
    
    def test_build_blank_filter_chain_multiple_segments(self):
        """Test filter chain with multiple segments."""
        remediator = VideoRemediator({"mode": "blank", "blank_color": "#000000"})
        
        segments = [
            {"start_time": "00:00:10", "end_time": "00:00:15"},
            {"start_time": "00:00:30", "end_time": "00:00:35"}
        ]
        result = remediator.build_blank_filter_chain(segments, 1920, 1080)
        
        # Should have two drawbox filters chained together
        assert result.count("drawbox") == 2
        assert "enable='between(t,10.0,15.0)'" in result
        assert "enable='between(t,30.0,35.0)'" in result
        assert "," in result  # Filters should be separated by comma
    
    def test_build_blank_filter_chain_custom_color(self):
        """Test filter chain with custom color."""
        remediator = VideoRemediator({"mode": "blank", "blank_color": "#FF0000"})
        
        segments = [
            {"start_time": "10.5", "end_time": "15.5"}
        ]
        result = remediator.build_blank_filter_chain(segments, 1280, 720)
        
        assert "drawbox=x=0:y=0:w=1280:h=720" in result
        assert "color=0xFF0000" in result
        assert "enable='between(t,10.5,15.5)'" in result
    
    def test_build_blank_filter_chain_short_color(self):
        """Test filter chain with short-form hex color."""
        remediator = VideoRemediator({"mode": "blank", "blank_color": "#F00"})
        
        segments = [
            {"start_time": "0", "end_time": "5"}
        ]
        result = remediator.build_blank_filter_chain(segments, 1920, 1080)
        
        # Short form #F00 should expand to 0xFF0000
        assert "color=0xFF0000" in result
    
    def test_build_blank_filter_chain_different_resolutions(self):
        """Test filter chain with different video resolutions."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segments = [{"start_time": "0", "end_time": "5"}]
        
        # 1080p
        result = remediator.build_blank_filter_chain(segments, 1920, 1080)
        assert "w=1920:h=1080" in result
        
        # 720p
        result = remediator.build_blank_filter_chain(segments, 1280, 720)
        assert "w=1280:h=720" in result
        
        # 4K
        result = remediator.build_blank_filter_chain(segments, 3840, 2160)
        assert "w=3840:h=2160" in result
    
    def test_build_blank_filter_chain_decimal_timestamps(self):
        """Test filter chain with decimal timestamps."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segments = [
            {"start_time": "10.123", "end_time": "15.456"}
        ]
        result = remediator.build_blank_filter_chain(segments, 1920, 1080)
        
        assert "enable='between(t,10.123,15.456)'" in result
