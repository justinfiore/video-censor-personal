"""Desktop UI module for Video Censor Personal.

Provides a cross-platform graphical interface using CustomTkinter.
The UI serves as a convenience layer on top of the CLI infrastructure.
"""

from video_censor_personal.ui.main import launch_app

try:
    from video_censor_personal.ui.preview_editor import PreviewEditorApp, launch_preview_editor
    PREVIEW_EDITOR_AVAILABLE = True
except (ImportError, RuntimeError):
    PREVIEW_EDITOR_AVAILABLE = False
    PreviewEditorApp = None
    launch_preview_editor = None

__all__ = [
    "launch_app",
    "PreviewEditorApp",
    "launch_preview_editor",
    "PREVIEW_EDITOR_AVAILABLE",
]
