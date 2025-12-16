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


class TestSegmentExtraction:
    """Test segment extraction logic for cut mode."""
    
    def test_extract_non_censored_segments_no_censored(self):
        """Test extraction when no segments are censored."""
        remediator = VideoRemediator({"mode": "cut"})
        
        result = remediator.extract_non_censored_segments([], 100.0)
        
        assert len(result) == 1
        assert result[0] == {"start": 0.0, "end": 100.0}
    
    def test_extract_non_censored_segments_beginning(self):
        """Test extraction when censored segment is at beginning."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segments = [{"start_time": "0", "end_time": "10"}]
        result = remediator.extract_non_censored_segments(segments, 100.0)
        
        assert len(result) == 1
        assert result[0] == {"start": 10.0, "end": 100.0}
    
    def test_extract_non_censored_segments_middle(self):
        """Test extraction when censored segment is in middle."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segments = [{"start_time": "30", "end_time": "40"}]
        result = remediator.extract_non_censored_segments(segments, 100.0)
        
        assert len(result) == 2
        assert result[0] == {"start": 0.0, "end": 30.0}
        assert result[1] == {"start": 40.0, "end": 100.0}
    
    def test_extract_non_censored_segments_end(self):
        """Test extraction when censored segment is at end."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segments = [{"start_time": "90", "end_time": "100"}]
        result = remediator.extract_non_censored_segments(segments, 100.0)
        
        assert len(result) == 1
        assert result[0] == {"start": 0.0, "end": 90.0}
    
    def test_extract_non_censored_segments_multiple(self):
        """Test extraction with multiple censored segments."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segments = [
            {"start_time": "10", "end_time": "20"},
            {"start_time": "40", "end_time": "50"},
            {"start_time": "80", "end_time": "90"}
        ]
        result = remediator.extract_non_censored_segments(segments, 100.0)
        
        assert len(result) == 4
        assert result[0] == {"start": 0.0, "end": 10.0}
        assert result[1] == {"start": 20.0, "end": 40.0}
        assert result[2] == {"start": 50.0, "end": 80.0}
        assert result[3] == {"start": 90.0, "end": 100.0}
    
    def test_extract_non_censored_segments_unsorted(self):
        """Test extraction with unsorted censored segments."""
        remediator = VideoRemediator({"mode": "cut"})
        
        # Provide segments out of order
        segments = [
            {"start_time": "40", "end_time": "50"},
            {"start_time": "10", "end_time": "20"},
            {"start_time": "80", "end_time": "90"}
        ]
        result = remediator.extract_non_censored_segments(segments, 100.0)
        
        # Should still produce correct sorted result
        assert len(result) == 4
        assert result[0] == {"start": 0.0, "end": 10.0}
        assert result[1] == {"start": 20.0, "end": 40.0}
        assert result[2] == {"start": 50.0, "end": 80.0}
        assert result[3] == {"start": 90.0, "end": 100.0}
    
    def test_extract_non_censored_segments_entire_video(self):
        """Test extraction when entire video is censored."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segments = [{"start_time": "0", "end_time": "100"}]
        result = remediator.extract_non_censored_segments(segments, 100.0)
        
        assert len(result) == 0
    
    def test_extract_non_censored_segments_overlapping(self):
        """Test extraction with overlapping censored segments."""
        remediator = VideoRemediator({"mode": "cut"})
        
        # Overlapping segments should be handled
        segments = [
            {"start_time": "10", "end_time": "30"},
            {"start_time": "20", "end_time": "40"}
        ]
        result = remediator.extract_non_censored_segments(segments, 100.0)
        
        assert len(result) == 2
        assert result[0] == {"start": 0.0, "end": 10.0}
        assert result[1] == {"start": 40.0, "end": 100.0}
    
    def test_extract_non_censored_segments_timecodes(self):
        """Test extraction with HH:MM:SS timecodes."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segments = [
            {"start_time": "00:00:10", "end_time": "00:00:20"},
            {"start_time": "00:01:00", "end_time": "00:01:30"}
        ]
        result = remediator.extract_non_censored_segments(segments, 200.0)
        
        assert len(result) == 3
        assert result[0] == {"start": 0.0, "end": 10.0}
        assert result[1] == {"start": 20.0, "end": 60.0}
        assert result[2] == {"start": 90.0, "end": 200.0}


class TestConcatFileGeneration:
    """Test concat file generation for cut mode."""
    
    def test_generate_concat_file(self, tmp_path):
        """Test concat file generation."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segments = [
            {"start": 0.0, "end": 10.0},
            {"start": 20.0, "end": 30.0}
        ]
        
        concat_file = tmp_path / "concat.txt"
        remediator.generate_concat_file(segments, str(concat_file))
        
        assert concat_file.exists()
        content = concat_file.read_text()
        
        assert "file 'segment_0.0_10.0.mp4'" in content
        assert "file 'segment_20.0_30.0.mp4'" in content
    
    def test_generate_concat_file_empty(self, tmp_path):
        """Test concat file generation with no segments."""
        remediator = VideoRemediator({"mode": "cut"})
        
        concat_file = tmp_path / "concat.txt"
        remediator.generate_concat_file([], str(concat_file))
        
        assert concat_file.exists()
        content = concat_file.read_text()
        assert content == ""


class TestModeResolution:
    """Test three-tier mode resolution logic."""
    
    def test_resolve_segment_mode_global_default(self):
        """Test mode resolution using global default."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segment = {"start_time": "10", "end_time": "20"}
        mode = remediator.resolve_segment_mode(segment)
        
        assert mode == "blank"
    
    def test_resolve_segment_mode_segment_override(self):
        """Test mode resolution with segment-level override."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "video_remediation": "cut"
        }
        mode = remediator.resolve_segment_mode(segment)
        
        assert mode == "cut"
    
    def test_resolve_segment_mode_category_default(self):
        """Test mode resolution with category default."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {
                "Nudity": "cut",
                "Violence": "blank"
            }
        })
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": ["Nudity"]
        }
        mode = remediator.resolve_segment_mode(segment)
        
        assert mode == "cut"
    
    def test_resolve_segment_mode_precedence_segment_over_category(self):
        """Test that segment-level override takes precedence over category."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": ["Nudity"],
            "video_remediation": "blank"  # Override category default
        }
        mode = remediator.resolve_segment_mode(segment)
        
        assert mode == "blank"
    
    def test_resolve_segment_mode_precedence_category_over_global(self):
        """Test that category default takes precedence over global."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": ["Nudity"]
        }
        mode = remediator.resolve_segment_mode(segment)
        
        assert mode == "cut"
    
    def test_resolve_segment_mode_multiple_labels_most_restrictive(self):
        """Test mode resolution with multiple labels uses most restrictive."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {
                "Nudity": "cut",
                "Violence": "blank"
            }
        })
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": ["Nudity", "Violence"]
        }
        mode = remediator.resolve_segment_mode(segment)
        
        # "cut" is more restrictive than "blank"
        assert mode == "cut"
    
    def test_resolve_segment_mode_multiple_labels_all_blank(self):
        """Test mode resolution with multiple labels all blank."""
        remediator = VideoRemediator({
            "mode": "cut",
            "category_modes": {
                "Violence": "blank",
                "Profanity": "blank"
            }
        })
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": ["Violence", "Profanity"]
        }
        mode = remediator.resolve_segment_mode(segment)
        
        assert mode == "blank"
    
    def test_resolve_segment_mode_unknown_category(self):
        """Test mode resolution with unknown category falls back to global."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": ["UnknownCategory"]
        }
        mode = remediator.resolve_segment_mode(segment)
        
        # Unknown category, use global default
        assert mode == "blank"
    
    def test_resolve_segment_mode_invalid_segment_mode(self):
        """Test mode resolution with invalid segment mode falls back."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": ["Nudity"],
            "video_remediation": "invalid"
        }
        mode = remediator.resolve_segment_mode(segment)
        
        # Invalid segment mode, fall back to category
        assert mode == "cut"
    
    def test_resolve_segment_mode_no_labels(self):
        """Test mode resolution with no labels."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": []
        }
        mode = remediator.resolve_segment_mode(segment)
        
        assert mode == "blank"
    
    def test_resolve_segment_mode_no_category_modes_config(self):
        """Test mode resolution with no category_modes configured."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segment = {
            "start_time": "10",
            "end_time": "20",
            "labels": ["Nudity"]
        }
        mode = remediator.resolve_segment_mode(segment)
        
        # No category modes, use global default
        assert mode == "cut"
    
    def test_resolve_category_mode_single_label(self):
        """Test category mode resolution with single label."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        mode = remediator._resolve_category_mode(["Nudity"])
        assert mode == "cut"
    
    def test_resolve_category_mode_no_labels(self):
        """Test category mode resolution with no labels."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        mode = remediator._resolve_category_mode([])
        assert mode is None
    
    def test_resolve_category_mode_no_matching_categories(self):
        """Test category mode resolution with no matching categories."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        mode = remediator._resolve_category_mode(["UnknownCategory"])
        assert mode is None


class TestAllowOverride:
    """Test allow override filtering."""
    
    def test_filter_allowed_segments_none_allowed(self):
        """Test filtering when no segments are allowed."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segments = [
            {"start_time": "10", "end_time": "20"},
            {"start_time": "30", "end_time": "40"}
        ]
        
        filtered = remediator.filter_allowed_segments(segments)
        assert len(filtered) == 2
    
    def test_filter_allowed_segments_all_allowed(self):
        """Test filtering when all segments are allowed."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segments = [
            {"start_time": "10", "end_time": "20", "allow": True},
            {"start_time": "30", "end_time": "40", "allow": True}
        ]
        
        filtered = remediator.filter_allowed_segments(segments)
        assert len(filtered) == 0
    
    def test_filter_allowed_segments_mixed(self):
        """Test filtering with mix of allowed and not allowed."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segments = [
            {"start_time": "10", "end_time": "20", "allow": False},
            {"start_time": "30", "end_time": "40", "allow": True},
            {"start_time": "50", "end_time": "60"}  # No allow field
        ]
        
        filtered = remediator.filter_allowed_segments(segments)
        assert len(filtered) == 2
        assert filtered[0]["start_time"] == "10"
        assert filtered[1]["start_time"] == "50"
    
    def test_filter_allowed_segments_precedence_over_mode(self):
        """Test that allow takes precedence over segment mode."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segments = [
            {
                "start_time": "10",
                "end_time": "20",
                "allow": True,
                "video_remediation": "cut"  # Should be ignored due to allow
            }
        ]
        
        filtered = remediator.filter_allowed_segments(segments)
        assert len(filtered) == 0


class TestCombinedRemediation:
    """Test combined audio and video remediation support."""
    
    def test_group_segments_by_mode_all_blank(self):
        """Test grouping when all segments use blank mode."""
        remediator = VideoRemediator({"mode": "blank"})
        
        segments = [
            {"start_time": "10", "end_time": "20"},
            {"start_time": "30", "end_time": "40"}
        ]
        
        groups = remediator.group_segments_by_mode(segments)
        
        assert len(groups["blank"]) == 2
        assert len(groups["cut"]) == 0
    
    def test_group_segments_by_mode_all_cut(self):
        """Test grouping when all segments use cut mode."""
        remediator = VideoRemediator({"mode": "cut"})
        
        segments = [
            {"start_time": "10", "end_time": "20"},
            {"start_time": "30", "end_time": "40"}
        ]
        
        groups = remediator.group_segments_by_mode(segments)
        
        assert len(groups["blank"]) == 0
        assert len(groups["cut"]) == 2
    
    def test_group_segments_by_mode_mixed(self):
        """Test grouping with mixed modes."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        segments = [
            {"start_time": "10", "end_time": "20", "labels": ["Nudity"]},
            {"start_time": "30", "end_time": "40", "labels": ["Violence"]},
            {"start_time": "50", "end_time": "60", "video_remediation": "cut"}
        ]
        
        groups = remediator.group_segments_by_mode(segments)
        
        assert len(groups["blank"]) == 1  # Violence segment
        assert len(groups["cut"]) == 2    # Nudity + explicit cut
    
    def test_group_segments_by_mode_with_allow_filtered(self):
        """Test grouping after filtering allowed segments."""
        remediator = VideoRemediator({
            "mode": "blank",
            "category_modes": {"Nudity": "cut"}
        })
        
        segments = [
            {"start_time": "10", "end_time": "20", "labels": ["Nudity"]},
            {"start_time": "30", "end_time": "40", "labels": ["Violence"], "allow": True},
            {"start_time": "50", "end_time": "60", "labels": ["Profanity"]}
        ]
        
        # First filter allowed segments
        filtered = remediator.filter_allowed_segments(segments)
        
        # Then group by mode
        groups = remediator.group_segments_by_mode(filtered)
        
        assert len(groups["cut"]) == 1    # Nudity
        assert len(groups["blank"]) == 1  # Profanity
        # Violence was filtered out
