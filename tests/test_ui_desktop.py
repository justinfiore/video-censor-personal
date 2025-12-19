"""Unit tests for desktop UI module.

Tests bootstrap application initialization and basic structure.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_ctk():
    """Mock CustomTkinter to avoid Tk initialization in tests."""
    # Mock customtkinter module before import
    mock_module = MagicMock()
    mock_root = MagicMock()
    mock_root.winfo_width.return_value = 800
    mock_root.winfo_height.return_value = 600
    mock_root.winfo_screenwidth.return_value = 1920
    mock_root.winfo_screenheight.return_value = 1080

    mock_module.CTk = MagicMock(return_value=mock_root)
    mock_module.CTkFrame = MagicMock()

    sys.modules["customtkinter"] = mock_module

    yield mock_module, mock_root

    # Cleanup
    if "customtkinter" in sys.modules:
        del sys.modules["customtkinter"]
    if "video_censor_personal.ui.main" in sys.modules:
        del sys.modules["video_censor_personal.ui.main"]
    if "video_censor_personal.ui" in sys.modules:
        del sys.modules["video_censor_personal.ui"]


def test_desktop_app_initialization(mock_ctk):
    """Test DesktopApp initializes with correct window properties."""
    mock_ctk_module, mock_root = mock_ctk

    from video_censor_personal.ui.main import DesktopApp

    app = DesktopApp()

    # Verify window was created
    mock_ctk_module.CTk.assert_called()

    # Verify title was set
    mock_root.title.assert_called_with("Video Censor Personal")

    # Verify geometry was set
    assert mock_root.geometry.call_count >= 1


def test_desktop_app_custom_title(mock_ctk):
    """Test DesktopApp accepts custom window title."""
    mock_ctk_module, mock_root = mock_ctk

    from video_censor_personal.ui.main import DesktopApp

    custom_title = "Custom Title"
    app = DesktopApp(title=custom_title)

    mock_root.title.assert_called_with(custom_title)


def test_desktop_app_run_calls_mainloop(mock_ctk):
    """Test DesktopApp.run() starts the event loop."""
    mock_ctk_module, mock_root = mock_ctk

    from video_censor_personal.ui.main import DesktopApp

    app = DesktopApp()
    app.run()

    # Verify mainloop was called
    mock_root.mainloop.assert_called_once()


def test_launch_app_entry_point(mock_ctk):
    """Test launch_app entry point creates and runs app."""
    mock_ctk_module, mock_root = mock_ctk

    from video_censor_personal.ui.main import launch_app

    launch_app()

    # Verify CTk was called (app created)
    mock_ctk_module.CTk.assert_called()

    # Verify mainloop was called (app ran)
    mock_root.mainloop.assert_called_once()
