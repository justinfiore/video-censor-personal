"""Pytest configuration and fixtures for UI tests.

This module provides shared fixtures for testing the desktop UI (CustomTkinter).
It handles display setup for headless environments (Linux CI) and provides
fixtures for application initialization and window lifecycle testing.
"""

import os
import sys
import pytest
from typing import Generator

from video_censor_personal.ui.main import DesktopApp


def has_display() -> bool:
    """Check if a display server is available.
    
    On Linux, checks for X11 DISPLAY environment variable.
    On macOS and Windows, display is always available.
    
    Returns:
        True if display is available or not needed, False otherwise.
    """
    if sys.platform == "linux":
        return "DISPLAY" in os.environ
    # macOS and Windows always have display available
    return True


@pytest.fixture(scope="function")
def app() -> Generator[DesktopApp, None, None]:
    """Create an isolated DesktopApp instance for testing.
    
    This fixture:
    - Creates a fresh DesktopApp instance
    - Yields the instance for the test to use
    - Properly cleans up the window and all resources after the test
    
    The fixture has function scope to ensure test isolation - each test
    gets its own application instance with no shared state.
    
    Yields:
        DesktopApp: An initialized application instance.
    """
    application = DesktopApp()
    try:
        yield application
    finally:
        # Cleanup: destroy the window and release resources
        try:
            if application.root.winfo_exists():
                application.root.destroy()
        except Exception:
            pass  # Window may already be destroyed or not yet created


@pytest.fixture(scope="function")
def app_window(app: DesktopApp):
    """Get the root window from an application instance.
    
    This fixture provides access to the window widget for tests that need
    to interact with window-level properties or lifecycle.
    
    Args:
        app: The application fixture (provides isolated app instance).
    
    Yields:
        The CTk root window instance.
    """
    yield app.root
