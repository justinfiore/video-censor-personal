"""Integration tests for pipeline model verification."""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from video_censor_personal.pipeline import AnalysisPipeline
from video_censor_personal.model_manager import ModelDownloadError


class TestPipelineModelVerification:
    """Tests for pipeline model verification integration."""

    def test_extract_model_requirements(self):
        """Test model requirement extraction from config."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
            "detectors": [
                {
                    "type": "llava",
                    "name": "vision",
                    "model_name": "llava-7b",
                    "categories": ["Nudity"],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            video_path.write_bytes(b"fake video")

            pipeline = AnalysisPipeline(
                str(video_path),
                config,
            )

            requirements = pipeline._extract_model_requirements()
            assert "llava-7b" in requirements

    def test_verify_models_with_sources(self):
        """Test model verification when sources defined."""
        test_content = b"model data"
        test_hash = hashlib.sha256(test_content).hexdigest()

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "models"
            cache_dir.mkdir()

            # Create test model file
            model_path = cache_dir / "test-model"
            model_path.write_bytes(test_content)

            config = {
                "detections": {
                    "nudity": {
                        "enabled": True,
                        "sensitivity": 0.7,
                        "model": "local",
                    }
                },
                "processing": {
                    "frame_sampling": {"strategy": "uniform"},
                    "segment_merge": {"merge_threshold": 2.0},
                    "max_workers": 4,
                },
                "output": {"format": "json"},
                "models": {
                    "cache_dir": str(cache_dir),
                    "sources": [
                        {
                            "name": "test-model",
                            "url": "https://example.com/model.bin",
                            "checksum": test_hash,
                            "size_bytes": len(test_content),
                        }
                    ],
                },
            }

            video_path = Path(tmpdir) / "test.mp4"
            video_path.write_bytes(b"fake video")

            pipeline = AnalysisPipeline(str(video_path), config)

            # Verify models without download (model already exists)
            result = pipeline.verify_models(download=False)
            assert result is True

    def test_verify_models_missing_raises_error(self):
        """Test model verification fails when models missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "models"
            cache_dir.mkdir()

            config = {
                "detections": {
                    "nudity": {
                        "enabled": True,
                        "sensitivity": 0.7,
                        "model": "local",
                    }
                },
                "processing": {
                    "frame_sampling": {"strategy": "uniform"},
                    "segment_merge": {"merge_threshold": 2.0},
                    "max_workers": 4,
                },
                "output": {"format": "json"},
                "models": {
                    "cache_dir": str(cache_dir),
                    "sources": [
                        {
                            "name": "missing-model",
                            "url": "https://example.com/model.bin",
                            "checksum": "hash123",
                            "size_bytes": 1000000,
                        }
                    ],
                },
            }

            video_path = Path(tmpdir) / "test.mp4"
            video_path.write_bytes(b"fake video")

            pipeline = AnalysisPipeline(str(video_path), config)

            # Verification without download should fail
            with pytest.raises(ModelDownloadError, match="Required models missing"):
                pipeline.verify_models(download=False)

    def test_lazy_detector_initialization(self):
        """Test that detection pipeline is lazily initialized."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            video_path.write_bytes(b"fake video")

            pipeline = AnalysisPipeline(str(video_path), config)

            # Detection pipeline should not be initialized yet
            assert pipeline.detection_pipeline is None

            # After calling _ensure_detection_pipeline, it should be initialized
            pipeline._ensure_detection_pipeline()
            assert pipeline.detection_pipeline is not None


class TestPipelineWithAutoDownload:
    """Tests for pipeline with automatic model download."""

    def test_pipeline_initialization_without_models(self):
        """Test pipeline initializes without models section."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            video_path.write_bytes(b"fake video")

            # Should initialize without errors
            pipeline = AnalysisPipeline(str(video_path), config)
            assert pipeline.config == config

    def test_verify_models_idempotent(self):
        """Test that verify_models is idempotent."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            video_path.write_bytes(b"fake video")

            pipeline = AnalysisPipeline(str(video_path), config)

            # First call should return True (no models required)
            result1 = pipeline.verify_models(download=False)
            assert result1 is True

            # Second call should also return True (already verified)
            result2 = pipeline.verify_models(download=False)
            assert result2 is True

    def test_error_messages_on_verification_failure(self):
        """Test error messages provide helpful guidance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "models"
            cache_dir.mkdir()

            config = {
                "detections": {
                    "nudity": {
                        "enabled": True,
                        "sensitivity": 0.7,
                        "model": "local",
                    }
                },
                "processing": {
                    "frame_sampling": {"strategy": "uniform"},
                    "segment_merge": {"merge_threshold": 2.0},
                    "max_workers": 4,
                },
                "output": {"format": "json"},
                "models": {
                    "cache_dir": str(cache_dir),
                    "sources": [
                        {
                            "name": "required-model",
                            "url": "https://example.com/model.bin",
                            "checksum": "hash123",
                            "size_bytes": 1000000,
                        }
                    ],
                },
            }

            video_path = Path(tmpdir) / "test.mp4"
            video_path.write_bytes(b"fake video")

            pipeline = AnalysisPipeline(str(video_path), config)

            # Check error message includes helpful guidance
            with pytest.raises(ModelDownloadError) as exc_info:
                pipeline.verify_models(download=False)

            error_msg = str(exc_info.value)
            assert "--download-models" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
