"""Tests for the integration of diagnostics, recovery, and bug reports within RemediationManager.

Verifies that error handling in _apply_final_metadata, _apply_audio_remediation,
and _apply_video_remediation correctly generates warnings, diagnoses errors,
and produces bug reports when appropriate.
"""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from video_censor_personal.remediation import RemediationManager
from video_censor_personal.remediation_diagnostics import FileOrigin


logger = logging.getLogger(__name__)


class TestRemediationErrorRecoveryIntegration:
    """Integration tests for diagnostics + recovery + bug reports in RemediationManager."""

    def _make_manager(self, tmp_path, output_video_path=None, remediated_audio_path=None):
        """Helper to create a RemediationManager with a real tmp_path video file."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"\x00" * 1024)

        config = {
            "remediation": {
                "audio": {"enabled": True, "mode": "silence"},
                "video": {"enabled": True, "mode": "blank"},
            }
        }

        out_path = output_video_path or str(tmp_path / "output.mp4")
        manager = RemediationManager(
            str(video_file),
            config,
            output_video_path=out_path,
            config_file="video-censor.yaml",
        )

        if remediated_audio_path is not None:
            manager.remediated_audio_path = remediated_audio_path

        return manager

    def test_metadata_failure_generates_diagnosis_and_bug_report(self, tmp_path):
        """Metadata failure produces a warning with diagnosis and bug report."""
        manager = self._make_manager(tmp_path)

        output_path = Path(manager.output_video_path)
        output_path.write_bytes(b"\x00" * 512)

        bug_report_text = (
            "Please report this issue at:\n"
            "  https://github.com/justinfiore/video-censor-personal/issues\n"
        )

        with patch(
            "video_censor_personal.video_metadata.extract_existing_metadata",
            return_value={},
        ), patch(
            "video_censor_personal.video_metadata.extract_original_title",
            return_value="Test",
        ), patch(
            "video_censor_personal.video_metadata.create_censored_title",
            return_value="Test (Censored)",
        ), patch(
            "video_censor_personal.video_metadata.build_remediation_metadata",
            return_value={},
        ), patch(
            "video_censor_personal.video_metadata.log_metadata",
        ), patch(
            "video_censor_personal.remediation.subprocess.run",
            side_effect=RuntimeError("moov atom not found"),
        ), patch(
            "video_censor_personal.remediation_diagnostics.generate_bug_report",
            return_value=bug_report_text,
        ):
            manager._apply_final_metadata()

        assert len(manager.warnings) == 1
        warning = manager.warnings[0]
        assert warning["phase"] == "metadata"
        assert warning["file_origin"] == FileOrigin.PIPELINE_INTERMEDIATE
        assert warning["bug_report"] is not None
        assert "github.com/justinfiore/video-censor-personal/issues" in warning["bug_report"]
        assert "Metadata application skipped" in warning["message"]

    def test_audio_remediation_failure_user_input_no_bug_report(self, tmp_path):
        """Audio remediation failure on user input has no bug report."""
        manager = self._make_manager(tmp_path)

        audio_np = np.zeros(48000, dtype=np.float32)

        with patch(
            "video_censor_personal.audio_remediator.AudioRemediator.remediate",
            side_effect=RuntimeError("Invalid data found when processing input"),
        ):
            with pytest.raises(RuntimeError, match="Invalid data found"):
                manager._apply_audio_remediation(
                    audio_data=audio_np,
                    audio_sample_rate=48000,
                    detections_or_segments=[],
                )

        assert len(manager.warnings) == 1
        warning = manager.warnings[0]
        assert warning["file_origin"] == FileOrigin.USER_INPUT
        assert warning["bug_report"] is None

    def test_video_remediation_failure_pipeline_intermediate_generates_bug_report(self, tmp_path):
        """Video remediation failure on pipeline intermediate file produces a bug report."""
        audio_path = tmp_path / "remediated_audio.wav"
        audio_path.write_bytes(b"\x00" * 256)
        manager = self._make_manager(
            tmp_path, remediated_audio_path=str(audio_path),
        )

        output_path = Path(manager.output_video_path)
        output_path.write_bytes(b"\x00" * 512)

        segments = [
            {"start_time": 1.0, "end_time": 2.0, "labels": ["violence"], "allow": False},
        ]

        with patch(
            "video_censor_personal.video_remediator.VideoRemediator.apply",
            side_effect=RuntimeError(
                "Could not write header: incorrect codec parameters"
            ),
        ):
            with pytest.raises(RuntimeError, match="Could not write header"):
                manager._apply_video_remediation(
                    segments=segments,
                    video_width=1920,
                    video_height=1080,
                    video_duration=10.0,
                )

        assert len(manager.warnings) == 1
        warning = manager.warnings[0]
        assert warning["file_origin"] == FileOrigin.PIPELINE_INTERMEDIATE
        assert warning["bug_report"] is not None
        assert "github.com/justinfiore/video-censor-personal/issues" in warning["bug_report"]

    def test_warnings_summary_returns_none_when_no_errors(self, tmp_path):
        """get_warnings_summary returns None when there are no warnings."""
        manager = self._make_manager(tmp_path)
        assert manager.get_warnings_summary() is None

    def test_multiple_warnings_are_collected(self, tmp_path):
        """Multiple add_warning calls accumulate and appear in summary."""
        manager = self._make_manager(tmp_path)

        manager.add_warning("audio_remediation", "Audio problem", FileOrigin.USER_INPUT)
        manager.add_warning("metadata", "Metadata problem", FileOrigin.PIPELINE_INTERMEDIATE)

        assert len(manager.warnings) == 2

        summary = manager.get_warnings_summary()
        assert summary is not None
        assert "audio_remediation" in summary
        assert "metadata" in summary
