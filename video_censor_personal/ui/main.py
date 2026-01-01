"""Bootstrap desktop application using CustomTkinter.

Provides a cross-platform graphical interface for Video Censor Personal.
"""

from typing import Optional
import logging
import os
import sys
from pathlib import Path

from video_censor_personal.ui.preview_editor import PreviewEditorApp

# Alias for backward compatibility with tests
DesktopApp = PreviewEditorApp

# Setup logging for main module
# Get the workspace root (parent of video_censor_personal package)
workspace_root = Path(__file__).parent.parent.parent
log_dir = workspace_root / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "ui.log"

logger = logging.getLogger("video_censor_personal.ui.main")
if not logger.handlers:
    handler = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def launch_app(json_file: Optional[str] = None) -> None:
    """Entry point for launching the desktop application.
    
    Args:
        json_file: Optional path to JSON file to load on startup
    """
    logger.info(f"launch_app called with json_file={json_file}")
    try:
        app = PreviewEditorApp(json_file=json_file)
        logger.info("PreviewEditorApp created successfully, starting event loop")
        app.run()
        logger.info("Event loop exited normally")
    except Exception as e:
        logger.error(f"Fatal error in launch_app: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info(f"Script called with sys.argv: {sys.argv}")
    
    try:
        # Check for command-line argument first
        json_file = sys.argv[1] if len(sys.argv) > 1 else None
        logger.info(f"Extracted json_file from argv: {json_file}")
        
        # Fall back to environment variable (set by launch-ui.sh for macOS app bundle)
        if not json_file:
            json_file = os.environ.get("VIDEO_CENSOR_JSON_FILE")
            logger.info(f"Extracted json_file from environment: {json_file}")
        
        logger.info(f"Final json_file: {json_file}")
        launch_app(json_file=json_file)
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        # Also print to stderr for debugging
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
