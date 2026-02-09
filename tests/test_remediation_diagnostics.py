"""Tests for remediation_diagnostics module.

Tests error pattern registry, diagnosis, output file checking,
bug report generation, and warnings collector.
"""

import platform
import re
from unittest.mock import MagicMock, patch

import pytest

from video_censor_personal.remediation_diagnostics import (
    ERROR_PATTERNS,
    Diagnosis,
    FileOrigin,
    check_output_file,
    diagnose_error,
    generate_bug_report,
)
from video_censor_personal.remediation import RemediationManager


class TestErrorPatternRegistry:
    """Test the ERROR_PATTERNS registry."""

    def test_registry_has_at_least_9_entries(self):
        assert len(ERROR_PATTERNS) >= 9

    @pytest.mark.parametrize(
        "stderr_text,expected_template_fragment",
        [
            ("moov atom not found", "moov atom not found"),
            ("Invalid data found when processing input", "invalid data found when processing input"),
            ("non-existing PPS referenced", "corrupt H.264"),
            ("decode_slice_header error", "corrupt H.264"),
            ("Non-monotonous DTS", "disordered timestamps"),
            ("Could not write header", "codec mismatch"),
            ("incorrect codec parameters", "codec mismatch"),
            ("No space left on device", "disk is full"),
            ("Permission denied", "permission error"),
            ("PES packet size mismatch", "transport stream corruption"),
            ("Unknown encoder 'libfoo'", "codec that is not available"),
            ("Encoder libx265 not found", "codec that is not available"),
        ],
    )
    def test_pattern_matches_expected_stderr(self, stderr_text, expected_template_fragment):
        matched = None
        for pattern in ERROR_PATTERNS:
            if re.search(pattern.regex, stderr_text, re.IGNORECASE):
                matched = pattern
                break
        assert matched is not None, f"No pattern matched '{stderr_text}'"
        assert expected_template_fragment in matched.diagnosis_template


class TestDiagnoseError:
    """Test diagnose_error function."""

    def test_moov_atom_user_input_mentions_original(self):
        diag = diagnose_error("moov atom not found", "/tmp/video.mp4", FileOrigin.USER_INPUT)
        assert "original input file" in diag.diagnosis.lower()

    def test_moov_atom_pipeline_intermediate_mentions_bug(self):
        diag = diagnose_error("moov atom not found", "/tmp/inter.mp4", FileOrigin.PIPELINE_INTERMEDIATE)
        assert "intermediate file" in diag.diagnosis.lower()
        assert "bug" in diag.diagnosis.lower()

    def test_invalid_data_has_ignore_errors_strategy(self):
        diag = diagnose_error("Invalid data found when processing input", "/tmp/f.mp4", FileOrigin.USER_INPUT)
        assert diag.recovery_strategy == "ignore_errors"

    def test_corrupt_h264_has_ignore_errors_strategy(self):
        diag = diagnose_error("non-existing PPS referenced", "/tmp/f.mp4", FileOrigin.USER_INPUT)
        assert diag.recovery_strategy == "ignore_errors"

    def test_dts_has_genpts_strategy(self):
        diag = diagnose_error("Non-monotonous DTS in output", "/tmp/f.mp4", FileOrigin.USER_INPUT)
        assert diag.recovery_strategy == "genpts"

    def test_codec_header_has_re_encode_codec_strategy(self):
        diag = diagnose_error("Could not write header for output file", "/tmp/f.mp4", FileOrigin.PIPELINE_INTERMEDIATE)
        assert diag.recovery_strategy == "re_encode_codec"

    def test_disk_full_has_no_recovery_strategy(self):
        diag = diagnose_error("No space left on device", "/tmp/f.mp4", FileOrigin.USER_INPUT)
        assert diag.recovery_strategy is None

    def test_permission_denied_has_no_recovery_strategy(self):
        diag = diagnose_error("Permission denied", "/tmp/f.mp4", FileOrigin.USER_INPUT)
        assert diag.recovery_strategy is None

    def test_unknown_error_has_no_pattern_and_includes_stderr(self):
        stderr = "something completely unknown happened"
        diag = diagnose_error(stderr, "/tmp/f.mp4", FileOrigin.USER_INPUT)
        assert diag.pattern is None
        assert stderr in diag.diagnosis

    def test_diagnosis_always_includes_file_path_and_origin(self):
        diag = diagnose_error("moov atom not found", "/tmp/test.mp4", FileOrigin.USER_INPUT)
        assert diag.file_path == "/tmp/test.mp4"
        assert diag.file_origin == FileOrigin.USER_INPUT

        diag2 = diagnose_error("unknown xyz", "/tmp/other.mp4", FileOrigin.PIPELINE_INTERMEDIATE)
        assert diag2.file_path == "/tmp/other.mp4"
        assert diag2.file_origin == FileOrigin.PIPELINE_INTERMEDIATE


class TestCheckOutputFile:
    """Test check_output_file function."""

    def test_returns_none_for_valid_file(self, tmp_path):
        f = tmp_path / "valid.mp4"
        f.write_bytes(b"\x00" * 1024)
        result = check_output_file(str(f))
        assert result is None

    def test_returns_diagnosis_for_missing_file(self):
        result = check_output_file("/nonexistent/path/video.mp4")
        assert isinstance(result, Diagnosis)
        assert "does not exist" in result.diagnosis

    def test_returns_diagnosis_for_empty_file(self, tmp_path):
        f = tmp_path / "empty.mp4"
        f.write_bytes(b"")
        result = check_output_file(str(f))
        assert isinstance(result, Diagnosis)
        assert "0 bytes" in result.diagnosis

    def test_returned_diagnosis_has_pipeline_intermediate_origin(self, tmp_path):
        f = tmp_path / "empty.mp4"
        f.write_bytes(b"")
        result = check_output_file(str(f))
        assert result.file_origin == FileOrigin.PIPELINE_INTERMEDIATE


class TestGenerateBugReport:
    """Test generate_bug_report function."""

    @patch("video_censor_personal.remediation_diagnostics.platform.python_version", return_value="3.13.0")
    @patch("video_censor_personal.remediation_diagnostics.platform.platform", return_value="macOS-14.0-arm64")
    @patch("video_censor_personal.remediation_diagnostics.subprocess.run")
    def test_includes_phase_name(self, mock_run, _mock_plat, _mock_pyver):
        mock_run.return_value = MagicMock(stdout="ffmpeg version 6.0")
        report = generate_bug_report(
            phase="video_remediation",
            error_msg="some error",
            file_path="/tmp/f.mp4",
            command="video-censor run",
            config_file="config.yaml",
            input_file="input.mp4",
        )
        assert "video_remediation" in report

    @patch("video_censor_personal.remediation_diagnostics.platform.python_version", return_value="3.13.0")
    @patch("video_censor_personal.remediation_diagnostics.platform.platform", return_value="macOS-14.0-arm64")
    @patch("video_censor_personal.remediation_diagnostics.subprocess.run")
    def test_includes_first_three_error_lines(self, mock_run, _mock_plat, _mock_pyver):
        mock_run.return_value = MagicMock(stdout="ffmpeg version 6.0")
        error_msg = "line one\nline two\nline three\nline four"
        report = generate_bug_report(
            phase="muxing",
            error_msg=error_msg,
            file_path="/tmp/f.mp4",
            command="cmd",
            config_file="c.yaml",
            input_file="i.mp4",
        )
        assert "line one" in report
        assert "line two" in report
        assert "line three" in report

    @patch("video_censor_personal.remediation_diagnostics.platform.python_version", return_value="3.13.0")
    @patch("video_censor_personal.remediation_diagnostics.platform.platform", return_value="macOS-14.0-arm64")
    @patch("video_censor_personal.remediation_diagnostics.subprocess.run")
    def test_includes_github_issues_link(self, mock_run, _mock_plat, _mock_pyver):
        mock_run.return_value = MagicMock(stdout="ffmpeg version 6.0")
        report = generate_bug_report(
            phase="p", error_msg="err", file_path="/f",
            command="c", config_file="cf", input_file="if",
        )
        assert "https://github.com/justinfiore/video-censor-personal/issues" in report

    @patch("video_censor_personal.remediation_diagnostics.platform.python_version", return_value="3.13.0")
    @patch("video_censor_personal.remediation_diagnostics.platform.platform", return_value="macOS-14.0-arm64")
    @patch("video_censor_personal.remediation_diagnostics.subprocess.run")
    def test_includes_command_config_input(self, mock_run, _mock_plat, _mock_pyver):
        mock_run.return_value = MagicMock(stdout="ffmpeg version 6.0")
        report = generate_bug_report(
            phase="p", error_msg="err", file_path="/f",
            command="my-command --flag", config_file="my-config.yaml", input_file="my-input.mp4",
        )
        assert "my-command --flag" in report
        assert "my-config.yaml" in report
        assert "my-input.mp4" in report

    @patch("video_censor_personal.remediation_diagnostics.platform.python_version", return_value="3.13.0")
    @patch("video_censor_personal.remediation_diagnostics.platform.platform", return_value="macOS-14.0-arm64")
    @patch("video_censor_personal.remediation_diagnostics.subprocess.run")
    def test_includes_os_and_python_info(self, mock_run, _mock_plat, _mock_pyver):
        mock_run.return_value = MagicMock(stdout="ffmpeg version 6.0")
        report = generate_bug_report(
            phase="p", error_msg="err", file_path="/f",
            command="c", config_file="cf", input_file="if",
        )
        assert "macOS-14.0-arm64" in report
        assert "3.13.0" in report

    @patch("video_censor_personal.remediation_diagnostics.platform.python_version", return_value="3.13.0")
    @patch("video_censor_personal.remediation_diagnostics.platform.platform", return_value="macOS-14.0-arm64")
    @patch("video_censor_personal.remediation_diagnostics.subprocess.run")
    def test_title_includes_error_summary(self, mock_run, _mock_plat, _mock_pyver):
        mock_run.return_value = MagicMock(stdout="ffmpeg version 6.0")
        first_line = "A" * 80
        report = generate_bug_report(
            phase="p", error_msg=first_line, file_path="/f",
            command="c", config_file="cf", input_file="if",
        )
        expected_summary = first_line[:60]
        assert f"({expected_summary})" in report


class TestWarningsCollector:
    """Test warnings collector on RemediationManager."""

    def _make_manager(self, tmp_path):
        video_file = tmp_path / "test.mp4"
        video_file.touch()
        config = {"remediation": {"audio": {"enabled": False}, "video": {"enabled": False}}}
        return RemediationManager(str(video_file), config)

    def test_add_warning_adds_to_list(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.add_warning("audio_remediation", "test msg", FileOrigin.USER_INPUT)
        assert len(mgr.warnings) == 1
        assert mgr.warnings[0]["message"] == "test msg"

    def test_get_warnings_summary_returns_none_when_empty(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        assert mgr.get_warnings_summary() is None

    def test_get_warnings_summary_formats_single_warning(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.add_warning("muxing", "a single warning", FileOrigin.USER_INPUT)
        summary = mgr.get_warnings_summary()
        assert summary is not None
        assert "a single warning" in summary
        assert "muxing" in summary

    def test_get_warnings_summary_formats_multiple_warnings(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.add_warning("audio_remediation", "warning 1", FileOrigin.USER_INPUT)
        mgr.add_warning("video_remediation", "warning 2", FileOrigin.PIPELINE_INTERMEDIATE)
        summary = mgr.get_warnings_summary()
        assert "warning 1" in summary
        assert "warning 2" in summary

    def test_get_warnings_summary_includes_bug_report(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.add_warning("muxing", "msg", FileOrigin.PIPELINE_INTERMEDIATE, bug_report="BUG_REPORT_CONTENT")
        summary = mgr.get_warnings_summary()
        assert "BUG_REPORT_CONTENT" in summary

    def test_warning_includes_phase_message_origin(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.add_warning("video_remediation", "my message", FileOrigin.PIPELINE_INTERMEDIATE)
        w = mgr.warnings[0]
        assert w["phase"] == "video_remediation"
        assert w["message"] == "my message"
        assert w["file_origin"] == FileOrigin.PIPELINE_INTERMEDIATE
