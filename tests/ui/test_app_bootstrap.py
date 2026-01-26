"""Tests for desktop application bootstrap and initialization.

These tests validate that the DesktopApp can be initialized correctly,
window properties are set, and no import errors occur during UI setup.
"""

import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock

from video_censor_personal.ui.main import DesktopApp


@pytest.mark.ui
class TestAppBootstrap:
    """Test suite for application initialization and bootstrap."""

    def test_application_initializes_without_errors(self, app: DesktopApp) -> None:
        """Test that application initializes without raising exceptions.
        
        Validates that:
        - DesktopApp can be instantiated
        - No import errors occur during initialization
        - The root window is created and exists
        """
        assert app is not None
        assert app.root is not None
        assert app.root.winfo_exists()

    def test_window_title_is_set_correctly(self, app: DesktopApp) -> None:
        """Test that window title is set to "Video Censor Personal - Preview Editor".
        
        Validates that:
        - Window title is correctly initialized
        - Title matches expected default value
        """
        assert app.root.title() == "Video Censor Personal - Preview Editor"

    def test_window_title_can_be_customized(self) -> None:
        """Test that window title can be customized on initialization.
        
        Validates that:
        - DesktopApp constructor accepts title parameter
        - Custom title is applied to the window
        """
        custom_title = "Custom Title"
        app = DesktopApp(title=custom_title)
        try:
            assert app.root.title() == custom_title
        finally:
            app.root.destroy()

    def test_window_is_created_successfully_on_first_initialization(
        self, app: DesktopApp
    ) -> None:
        """Test that window is created and is visible after initialization.
        
        Validates that:
        - Window widget exists immediately after __init__
        - Window can report its dimensions (has been updated)
        - Window has valid geometry
        """
        assert app.root.winfo_exists()
        
        # Update to ensure geometry is calculated
        app.root.update_idletasks()
        
        # Verify window has valid dimensions
        width = app.root.winfo_width()
        height = app.root.winfo_height()
        assert width > 0, "Window width should be positive"
        assert height > 0, "Window height should be positive"

    def test_no_module_import_errors_when_initializing_ui(self) -> None:
        """Test that importing and initializing UI code causes no import errors.
        
        Validates that:
        - video_censor_personal.ui.main module can be imported
        - customtkinter dependency is available
        - No circular imports or missing dependencies occur
        """
        try:
            from video_censor_personal.ui import main
            import customtkinter  # noqa: F401
        except ImportError as e:
            pytest.fail(f"Import error in UI module: {e}")

    def test_app_can_be_instantiated_multiple_times(self) -> None:
        """Test that multiple DesktopApp instances can be created sequentially.
        
        Validates that:
        - Application state doesn't prevent multiple instantiations
        - Each instance is independent
        - Resources are not permanently consumed
        """
        app1 = DesktopApp()
        app2 = DesktopApp()
        
        try:
            assert app1 is not app2
            assert app1.root is not app2.root
            assert app1.root.title() == app2.root.title()
        finally:
            app1.root.destroy()
            app2.root.destroy()


@pytest.mark.ui
class TestWindowMaximization:
    """Test suite for window maximization on application startup."""

    def test_setup_window_maximizes_window(self) -> None:
        """Test that _setup_window maximizes the window to fill the screen.
        
        This test verifies:
        1. On Windows: state("zoomed") is called
        2. On macOS/Linux: geometry is set to screen dimensions
        """
        from video_censor_personal.ui import preview_editor
        
        # Create a mock root object to track calls
        mock_root = MagicMock()
        mock_root.state.return_value = None
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        
        # Patch ctk.CTk to return our mock
        with patch.object(preview_editor, 'ctk') as mock_ctk:
            mock_ctk.CTk.return_value = mock_root
            mock_ctk.CTkFrame = MagicMock()
            mock_ctk.CTkLabel = MagicMock()
            
            # Create a minimal app instance
            app = preview_editor.PreviewEditorApp.__new__(preview_editor.PreviewEditorApp)
            app.root = mock_root
            app.profiler = MagicMock()
            
            # Call the _setup_window method
            app._setup_window()
            
            # Verify state("zoomed") was called (Windows path)
            mock_root.state.assert_called_with("zoomed")

    def test_setup_window_fallback_unix_geometry(self) -> None:
        """Test that _setup_window falls back to geometry on Unix systems.
        
        Simulates a TclError to test the macOS/Linux fallback path.
        """
        from video_censor_personal.ui import preview_editor
        
        # Create a mock root that raises TclError on state()
        mock_root = MagicMock()
        mock_root.state.side_effect = tk.TclError("zoom not supported")
        mock_root.winfo_screenwidth.return_value = 2560
        mock_root.winfo_screenheight.return_value = 1440
        
        with patch.object(preview_editor, 'ctk') as mock_ctk:
            mock_ctk.CTk.return_value = mock_root
            mock_ctk.CTkFrame = MagicMock()
            mock_ctk.CTkLabel = MagicMock()
            
            # Create a minimal app instance
            app = preview_editor.PreviewEditorApp.__new__(preview_editor.PreviewEditorApp)
            app.root = mock_root
            app.profiler = MagicMock()
            
            # Call the _setup_window method
            app._setup_window()
            
            # Verify state() was attempted
            mock_root.state.assert_called_with("zoomed")
            
            # Verify geometry was called with full screen size at origin
            geometry_calls = [str(call) for call in mock_root.geometry.call_args_list]
            assert any("2560x1440" in call for call in geometry_calls), \
                f"Expected geometry with 2560x1440, got: {geometry_calls}"

    def test_setup_window_grid_configuration(self) -> None:
        """Test that grid is configured for responsive layout."""
        from video_censor_personal.ui import preview_editor
        
        mock_root = MagicMock()
        mock_root.state.return_value = None
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        
        with patch.object(preview_editor, 'ctk') as mock_ctk:
            mock_ctk.CTk.return_value = mock_root
            mock_ctk.CTkFrame = MagicMock()
            mock_ctk.CTkLabel = MagicMock()
            
            app = preview_editor.PreviewEditorApp.__new__(preview_editor.PreviewEditorApp)
            app.root = mock_root
            app.profiler = MagicMock()
            
            # Call _setup_window
            app._setup_window()
            
            # Verify grid_rowconfigure and grid_columnconfigure were called
            assert mock_root.grid_rowconfigure.called, "grid_rowconfigure should be called"
            assert mock_root.grid_columnconfigure.called, "grid_columnconfigure should be called"
            
            # Verify the main content row (row 0) has weight=1 (expandable)
            grid_row_calls = mock_root.grid_rowconfigure.call_args_list
            row_0_weights = [
                call_obj[1].get('weight')
                for call_obj in grid_row_calls
                if call_obj[0][0] == 0
            ]
            assert 1 in row_0_weights, f"Row 0 should be expandable (weight=1), got: {row_0_weights}"
            
            # Verify the main content column (column 0) has weight=1 (expandable)
            grid_col_calls = mock_root.grid_columnconfigure.call_args_list
            col_0_weights = [
                call_obj[1].get('weight')
                for call_obj in grid_col_calls
                if call_obj[0][0] == 0
            ]
            assert 1 in col_0_weights, f"Column 0 should be expandable (weight=1), got: {col_0_weights}"
