"""Tests for GPU device detection utilities."""

from unittest.mock import MagicMock, patch
import sys

import pytest


class TestGetDevice:
    """Test get_device() function."""

    def test_auto_detect_cuda_when_available(self):
        """Test auto-detection selects CUDA when available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            result = get_device()
            assert result == "cuda"

    def test_auto_detect_mps_when_cuda_unavailable(self):
        """Test auto-detection selects MPS when CUDA unavailable."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            result = get_device()
            assert result == "mps"

    def test_auto_detect_cpu_fallback(self):
        """Test auto-detection falls back to CPU when no GPU available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            result = get_device()
            assert result == "cpu"

    def test_manual_override_cuda(self):
        """Test manual override to CUDA device."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            result = get_device(config_override="cuda")
            assert result == "cuda"

    def test_manual_override_mps(self):
        """Test manual override to MPS device."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            result = get_device(config_override="mps")
            assert result == "mps"

    def test_manual_override_cpu(self):
        """Test manual override to CPU device."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            result = get_device(config_override="cpu")
            assert result == "cpu"

    def test_manual_override_cuda_unavailable_raises_error(self):
        """Test error when CUDA override requested but unavailable."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            with pytest.raises(ValueError, match="cuda.*not available"):
                get_device(config_override="cuda")

    def test_manual_override_mps_unavailable_raises_error(self):
        """Test error when MPS override requested but unavailable."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            with pytest.raises(ValueError, match="mps.*not available"):
                get_device(config_override="mps")

    def test_manual_override_unknown_device_raises_error(self):
        """Test error when unknown device specified."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            with pytest.raises(ValueError, match="Unknown device"):
                get_device(config_override="tpu")

    def test_manual_override_case_insensitive(self):
        """Test that device override is case-insensitive."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            result = get_device(config_override="CUDA")
            assert result == "cuda"

    def test_manual_override_strips_whitespace(self):
        """Test that device override handles whitespace."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import get_device
            result = get_device(config_override="  cuda  ")
            assert result == "cuda"


class TestGetAvailableDevices:
    """Test _get_available_devices() helper."""

    def test_returns_only_cpu_when_no_gpu(self):
        """Test returns only CPU when no GPU available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import _get_available_devices
            result = _get_available_devices()
            assert result == ["cpu"]

    def test_includes_cuda_when_available(self):
        """Test includes CUDA when available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.backends.mps.is_available.return_value = False
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import _get_available_devices
            result = _get_available_devices()
            assert "cuda" in result
            assert "cpu" in result

    def test_includes_mps_when_available(self):
        """Test includes MPS when available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        
        with patch.dict(sys.modules, {"torch": mock_torch}):
            from video_censor_personal.device_utils import _get_available_devices
            result = _get_available_devices()
            assert "mps" in result
            assert "cpu" in result
