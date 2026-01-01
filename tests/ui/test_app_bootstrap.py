"""Tests for desktop application bootstrap and initialization.

These tests validate that the DesktopApp can be initialized correctly,
window properties are set, and no import errors occur during UI setup.
"""

import pytest

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
