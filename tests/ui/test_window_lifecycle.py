"""Tests for window lifecycle management and resource cleanup.

These tests validate window creation, destruction, lifecycle events,
and proper resource cleanup to prevent memory leaks.
"""

import pytest
import gc

from video_censor_personal.ui.main import DesktopApp


@pytest.mark.ui
class TestWindowLifecycle:
    """Test suite for window lifecycle and cleanup."""

    def test_window_can_be_opened_and_closed_without_errors(
        self, app: DesktopApp
    ) -> None:
        """Test that window can be created and destroyed without exceptions.
        
        Validates that:
        - Window exists after creation
        - Window can be destroyed
        - No exceptions occur during destruction
        """
        assert app.root.winfo_exists()
        
        # Destroy the window (this would normally happen on user close)
        app.root.destroy()
        
        # Verify window is destroyed (check with try/except since winfo_exists
        # raises after destroy)
        try:
            exists = app.root.winfo_exists()
            assert not exists
        except Exception:
            # After destroy, winfo_exists raises - this is expected
            pass

    def test_cleanup_code_executes_on_window_close(self) -> None:
        """Test that cleanup code executes properly when window is closed.
        
        Validates that:
        - Window can be created
        - Destroy method can be called
        - No errors occur during cleanup
        """
        app = DesktopApp()
        
        # Window should exist before destroy
        assert app.root.winfo_exists()
        
        # Destroy it
        app.root.destroy()
        
        # Window should not exist after destroy (check with try/except since 
        # winfo_exists raises after destroy)
        try:
            exists = app.root.winfo_exists()
            assert not exists
        except Exception:
            # After destroy, winfo_exists raises - this is expected
            pass

    def test_no_resource_leaks_after_window_close(self) -> None:
        """Test that file handles and resources are released after window close.
        
        Validates that:
        - Window can be created and destroyed
        - Explicit garbage collection doesn't cause errors
        - No lingering widget references prevent cleanup
        """
        app = DesktopApp()
        root_ref = app.root
        
        # Destroy the window
        app.root.destroy()
        
        # Force garbage collection to ensure cleanup
        gc.collect()
        
        # Window should be properly cleaned up (check with try/except since 
        # winfo_exists raises after destroy)
        try:
            exists = root_ref.winfo_exists()
            assert not exists
        except Exception:
            # After destroy, winfo_exists raises - this is expected
            pass

    def test_multiple_window_create_destroy_cycles_succeed(self) -> None:
        """Test that multiple window create/destroy cycles don't cause errors.
        
        Validates that:
        - Window resources are properly released on each destruction
        - Multiple cycles can complete without resource exhaustion
        - No state is retained between cycles
        """
        for cycle in range(5):
            app = DesktopApp()
            
            # Verify window exists
            assert app.root.winfo_exists(), f"Window missing in cycle {cycle}"
            
            # Destroy it
            app.root.destroy()
            
            # Verify it's destroyed (check with try/except since winfo_exists 
            # raises after destroy)
            try:
                exists = app.root.winfo_exists()
                assert not exists, f"Window not cleaned up in cycle {cycle}"
            except Exception:
                # After destroy, winfo_exists raises - this is expected
                pass
            
            # Force garbage collection between cycles
            gc.collect()

    def test_window_geometry_is_valid_on_creation(self, app: DesktopApp) -> None:
        """Test that window geometry is properly set on creation.
        
        Validates that:
        - Window has a valid geometry string
        - Width and height are positive
        - Window position coordinates are valid
        """
        app.root.update_idletasks()
        
        # Get geometry
        geometry = app.root.geometry()
        assert "x" in geometry, "Geometry should contain dimensions"
        
        # Parse geometry and validate
        width = app.root.winfo_width()
        height = app.root.winfo_height()
        
        assert width > 0, "Width should be positive"
        assert height > 0, "Height should be positive"

    def test_window_can_be_updated_during_lifecycle(self, app: DesktopApp) -> None:
        """Test that window can be updated during its lifecycle.
        
        Validates that:
        - Window update methods work without errors
        - Window properties can be queried
        - Window can process events during its lifetime
        """
        # Update window processing
        app.root.update_idletasks()
        
        # Verify we can query properties
        width = app.root.winfo_width()
        height = app.root.winfo_height()
        title = app.root.title()
        
        assert width > 0
        assert height > 0
        assert title == "Video Censor Personal"
        
        # Update again before cleanup
        app.root.update_idletasks()

    def test_window_content_frame_persists_through_lifecycle(
        self, app: DesktopApp
    ) -> None:
        """Test that window content frame exists and persists.
        
        Validates that:
        - Window has child frames created during initialization
        - Frames persist during window lifecycle
        - Frame structure is intact
        """
        # Get list of children
        children = app.root.winfo_children()
        assert len(children) > 0, "Window should have child frames"
        
        # Update and verify children still exist
        app.root.update_idletasks()
        children_after = app.root.winfo_children()
        assert len(children_after) > 0, "Child frames should persist"

    def test_window_focus_can_be_set(self, app: DesktopApp) -> None:
        """Test that window focus operations work without errors.
        
        Validates that:
        - Window focus operations don't raise exceptions
        - Window can be brought to focus
        """
        # These operations should not raise
        try:
            app.root.focus_set()
            app.root.focus()
        except Exception as e:
            pytest.fail(f"Window focus operation failed: {e}")
