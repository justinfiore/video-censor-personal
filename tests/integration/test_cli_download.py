"""Integration tests for CLI with model auto-download."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

import pytest
import yaml

from video_censor_personal.cli import parse_args, create_parser
from video_censor_personal.config import ConfigError, load_config


class TestDownloadModelsFlag:
    """Tests for --download-models CLI flag."""

    def test_download_models_flag_recognized(self):
        """Test that --download-models flag is recognized by parser."""
        parser = create_parser()
        args = parser.parse_args(
            ["--input", "test.mp4", "--download-models"]
        )
        assert hasattr(args, "download_models")
        assert args.download_models is True

    def test_download_models_flag_optional(self):
        """Test that --download-models flag is optional."""
        parser = create_parser()
        args = parser.parse_args(["--input", "test.mp4"])
        assert args.download_models is False

    def test_download_models_flag_combined_with_other_args(self):
        """Test --download-models combined with other arguments."""
        parser = create_parser()
        args = parser.parse_args([
            "--input", "video.mp4",
            "--output", "results.json",
            "--config", "config.yaml",
            "--download-models",
            "--log-level", "DEBUG",
        ])
        assert args.download_models is True
        assert args.input == "video.mp4"
        assert args.output == "results.json"
        assert args.config == "config.yaml"
        assert args.log_level == "DEBUG"


class TestDownloadModelsIntegration:
    """Integration tests for download-models feature."""

    def test_config_with_model_sources(self):
        """Test loading configuration with model sources."""
        yaml_content = """
detections:
  nudity:
    enabled: true
    sensitivity: 0.7
    model: "local"

processing:
  frame_sampling:
    strategy: "uniform"
  segment_merge:
    merge_threshold: 2.0
  max_workers: 4

output:
  format: "json"

models:
  cache_dir: null
  sources:
    - name: "test-model"
      url: "https://example.com/model.bin"
      checksum: "abc123def456"
      size_bytes: 1000000
  auto_download: false
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            
            config = load_config(f.name)
            assert "models" in config
            assert config["models"]["sources"]
            assert len(config["models"]["sources"]) == 1
            assert config["models"]["sources"][0]["name"] == "test-model"

    def test_idempotent_downloads(self):
        """Test that downloads are skipped for valid models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "models"
            cache_dir.mkdir()

            # Create a model file with correct checksum
            model_content = b"model data"
            model_hash = hashlib.sha256(model_content).hexdigest()
            model_path = cache_dir / "test-model"
            model_path.write_bytes(model_content)

            yaml_content = f"""
detections:
  nudity:
    enabled: true
    sensitivity: 0.7
    model: "local"

processing:
  frame_sampling:
    strategy: "uniform"
  segment_merge:
    merge_threshold: 2.0
  max_workers: 4

output:
  format: "json"

models:
  cache_dir: "{cache_dir}"
  sources:
    - name: "test-model"
      url: "https://example.com/model.bin"
      checksum: "{model_hash}"
      size_bytes: {len(model_content)}
  auto_download: false
"""
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write(yaml_content)
                f.flush()

                from video_censor_personal.config import Config, ModelsConfig, ModelSource
                from video_censor_personal.model_manager import ModelManager

                config_dict = load_config(f.name)
                
                # Setup Config object
                config_obj = Config()
                if "models" in config_dict:
                    models_data = config_dict["models"]
                    sources = []
                    if "sources" in models_data and models_data["sources"]:
                        for source_data in models_data["sources"]:
                            sources.append(
                                ModelSource(
                                    name=source_data["name"],
                                    url=source_data["url"],
                                    checksum=source_data["checksum"],
                                    size_bytes=source_data["size_bytes"],
                                    algorithm=source_data.get("algorithm", "sha256"),
                                    optional=source_data.get("optional", False),
                                )
                            )
                    config_obj.models = ModelsConfig(
                        cache_dir=models_data.get("cache_dir"),
                        sources=sources,
                    )

                manager = ModelManager(config_obj)
                
                # First call should find model valid
                assert manager.is_model_valid("test-model") is True
                
                # verify_models should skip download since model is valid
                results = manager.verify_models()
                assert results["test-model"] is True


class TestProgressReporting:
    """Tests for progress reporting during downloads."""

    def test_progress_callback_invoked(self):
        """Test that progress callback is invoked during download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            from video_censor_personal.config import Config, ModelsConfig, ModelSource
            from video_censor_personal.model_manager import ModelManager
            from urllib.error import URLError

            config_obj = Config()
            test_content = b"test model data"
            test_hash = hashlib.sha256(test_content).hexdigest()

            source = ModelSource(
                name="test-model",
                url="https://example.com/model.bin",
                checksum=test_hash,
                size_bytes=len(test_content),
            )

            config_obj.models = ModelsConfig(
                cache_dir=str(cache_dir),
                sources=[source],
            )

            manager = ModelManager(config_obj)

            # Mock download_with_retry to simulate progress
            call_count = [0]
            progress_calls = []

            def mock_download(src, attempt, callback):
                temp_file = cache_dir / f".{src.name}.tmp"
                temp_file.write_bytes(test_content)
                if callback:
                    # Simulate progress callback
                    callback(src.name, len(test_content), len(test_content))
                    progress_calls.append((src.name, len(test_content)))
                return temp_file

            def progress_callback(name, done, total):
                progress_calls.append((name, done, total))

            with patch.object(manager, "_download_with_retry", side_effect=mock_download):
                manager.verify_models(
                    sources=[source],
                    progress_callback=progress_callback
                )

            # Check that callback was called
            assert len(progress_calls) > 0


class TestErrorMessages:
    """Tests for error messages and recovery guidance."""

    def test_download_failure_message(self):
        """Test error message on download failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from video_censor_personal.config import Config, ModelsConfig, ModelSource
            from video_censor_personal.model_manager import (
                ModelManager,
                ModelDownloadError,
            )
            from urllib.error import URLError

            config_obj = Config()
            source = ModelSource(
                name="unavailable-model",
                url="https://example.com/unavailable-model.bin",
                checksum="hash123",
                size_bytes=1000,
            )

            config_obj.models = ModelsConfig(
                cache_dir=tmpdir,
                sources=[source],
            )

            manager = ModelManager(config_obj)

            # Mock download_with_retry to always fail
            def mock_download_fail(src, attempt, callback):
                raise URLError("HTTP 404: Not Found")

            with patch.object(
                manager, "_download_with_retry", side_effect=mock_download_fail
            ):
                with pytest.raises(ModelDownloadError) as exc_info:
                    manager.verify_models(sources=[source])

                # Check error message includes helpful info
                error_str = str(exc_info.value)
                assert "unavailable-model" in error_str
                assert "3 attempts" in error_str
                assert "https://example.com/" in error_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
