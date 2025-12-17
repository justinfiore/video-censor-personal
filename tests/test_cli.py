"""Tests for command-line interface module."""

import pytest

from video_censor_personal.cli import parse_args, create_parser


class TestCreateParser:
    """Test argument parser creation."""

    def test_parser_has_input_argument(self):
        """Parser should have --input argument."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4"])
        assert args.input == "video.mp4"

    def test_parser_has_output_argument(self):
        """Parser should have --output argument."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4", "--output", "results.json"])
        assert args.output == "results.json"

    def test_parser_default_output(self):
        """Default output should be results.json."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4"])
        assert args.output == "results.json"

    def test_parser_has_config_argument(self):
        """Parser should have --config argument."""
        parser = create_parser()
        args = parser.parse_args(
            ["--input", "video.mp4", "--config", "config.yaml"]
        )
        assert args.config == "config.yaml"

    def test_parser_config_optional(self):
        """Config argument should be optional."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4"])
        assert args.config is None

    def test_parser_has_log_level(self):
        """Parser should have --log-level argument."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4", "--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_parser_log_level_default_info(self):
        """Log level should default to INFO."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4"])
        assert args.log_level == "INFO"

    def test_parser_log_level_trace(self):
        """Parser should accept TRACE log level."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4", "--log-level", "TRACE"])
        assert args.log_level == "TRACE"

    def test_parser_log_level_case_insensitive_lowercase(self):
        """Parser should accept lowercase log levels."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4", "--log-level", "debug"])
        assert args.log_level == "DEBUG"

    def test_parser_log_level_case_insensitive_mixed(self):
        """Parser should accept mixed-case log levels."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4", "--log-level", "Info"])
        assert args.log_level == "INFO"

    def test_parser_log_level_case_insensitive_trace_lowercase(self):
        """Parser should accept lowercase trace level."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4", "--log-level", "trace"])
        assert args.log_level == "TRACE"

    def test_parser_log_level_invalid_rejected(self):
        """Parser should reject invalid log levels."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--input", "video.mp4", "--log-level", "INVALID"])

    def test_parser_has_version(self):
        """Parser should have --version argument."""
        parser = create_parser()
        # Version will cause sys.exit, so we just check it exists
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])


class TestParseArgs:
    """Test argument parsing."""

    def test_parse_required_arguments(self):
        """Should parse required arguments."""
        args = parse_args(["--input", "video.mp4"])
        assert args.input == "video.mp4"

    def test_parse_all_arguments(self):
        """Should parse all arguments."""
        args = parse_args(
            [
                "--input",
                "video.mp4",
                "--output",
                "out.json",
                "--config",
                "config.yaml",
                "--log-level",
                "DEBUG",
            ]
        )
        assert args.input == "video.mp4"
        assert args.output == "out.json"
        assert args.config == "config.yaml"
        assert args.log_level == "DEBUG"

    def test_parse_missing_required_input(self):
        """Should error on missing required --input argument."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_parse_input_with_spaces(self):
        """Should handle file paths with spaces."""
        args = parse_args(["--input", "/path/to/my video file.mp4"])
        assert args.input == "/path/to/my video file.mp4"

    def test_parse_absolute_paths(self):
        """Should handle absolute paths."""
        args = parse_args(
            [
                "--input",
                "/home/user/videos/test.mp4",
                "--output",
                "/home/user/results/output.json",
            ]
        )
        assert args.input == "/home/user/videos/test.mp4"
        assert args.output == "/home/user/results/output.json"

    def test_parse_relative_paths(self):
        """Should handle relative paths."""
        args = parse_args(
            [
                "--input",
                "./videos/test.mp4",
                "--output",
                "../results/output.json",
            ]
        )
        assert args.input == "./videos/test.mp4"
        assert args.output == "../results/output.json"


class TestInputSegmentsArgument:
    """Test --input-segments argument parsing."""

    def test_parser_has_input_segments_argument(self):
        """Parser should have --input-segments argument."""
        parser = create_parser()
        args = parser.parse_args([
            "--input", "video.mp4",
            "--input-segments", "segments.json",
        ])
        assert args.input_segments == "segments.json"

    def test_input_segments_is_optional(self):
        """--input-segments should be optional."""
        parser = create_parser()
        args = parser.parse_args(["--input", "video.mp4"])
        assert args.input_segments is None

    def test_input_segments_with_output_video(self):
        """--input-segments should work with --output-video."""
        parser = create_parser()
        args = parser.parse_args([
            "--input", "video.mp4",
            "--input-segments", "segments.json",
            "--output-video", "output.mp4",
        ])
        assert args.input_segments == "segments.json"
        assert args.output_video == "output.mp4"


class TestParserHelpText:
    """Test that help text is clear and complete."""

    def test_parser_has_description(self):
        """Parser should have helpful description."""
        parser = create_parser()
        assert "video" in parser.description.lower()
        assert "analyze" in parser.description.lower()

    def test_parser_has_epilog(self):
        """Parser should have usage example."""
        parser = create_parser()
        assert parser.epilog is not None
        assert "example" in parser.epilog.lower()
        assert "python" in parser.epilog.lower()

    def test_argument_help_text_exists(self):
        """All arguments should have help text."""
        parser = create_parser()
        for action in parser._actions:
            if action.dest not in ["help", "version"]:
                assert action.help is not None and action.help != ""
