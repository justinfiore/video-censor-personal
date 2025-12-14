"""Loading spinner for model GPU loading operations."""

import sys
import threading
import time
from contextlib import contextmanager
from typing import Optional


class LoadingSpinner:
    """Animated spinner for long-running operations without progress tracking.

    Displays a spinning animation with model name and size to indicate
    active loading when progress callbacks are not available.
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    INTERVAL = 0.1  # seconds between frames

    def __init__(
        self,
        model_name: str,
        model_size_bytes: Optional[int] = None,
        device: str = "GPU",
    ) -> None:
        """Initialize the spinner.

        Args:
            model_name: Name of the model being loaded.
            model_size_bytes: Optional size in bytes for display.
            device: Target device name (e.g., "cuda", "mps", "GPU").
        """
        self.model_name = model_name
        self.model_size_bytes = model_size_bytes
        self.device = device
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}PB"

    def _build_message(self) -> str:
        """Build the loading message string."""
        msg = f"Loading {self.model_name} to {self.device}"
        if self.model_size_bytes:
            msg += f" ({self._format_size(self.model_size_bytes)})"
        return msg

    def _spin(self) -> None:
        """Run the spinner animation in a background thread."""
        message = self._build_message()
        frame_idx = 0

        while not self._stop_event.is_set():
            frame = self.FRAMES[frame_idx % len(self.FRAMES)]
            line = f"\r{frame} {message}..."
            sys.stderr.write(line)
            sys.stderr.flush()
            frame_idx += 1
            time.sleep(self.INTERVAL)

        sys.stderr.write(f"\r✓ {message} - done\n")
        sys.stderr.flush()

    def start(self) -> None:
        """Start the spinner animation."""
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the spinner animation."""
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=1.0)
        self._thread = None


@contextmanager
def loading_spinner(
    model_name: str,
    model_size_bytes: Optional[int] = None,
    device: str = "GPU",
):
    """Context manager for displaying a loading spinner.

    Args:
        model_name: Name of the model being loaded.
        model_size_bytes: Optional size in bytes for display.
        device: Target device name.

    Yields:
        The spinner instance.

    Example:
        with loading_spinner("llava-v1.5-7b", 14_000_000_000, "cuda"):
            model = load_model()
    """
    spinner = LoadingSpinner(model_name, model_size_bytes, device)
    spinner.start()
    try:
        yield spinner
    finally:
        spinner.stop()


class TaskSpinner:
    """Animated spinner for generic long-running tasks.

    Displays a spinning animation with a custom message.
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    INTERVAL = 0.1

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """Initialize the spinner.

        Args:
            message: Main message to display.
            details: Optional additional details (e.g., duration, size).
        """
        self.message = message
        self.details = details
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _build_message(self) -> str:
        """Build the display message."""
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message

    def _spin(self) -> None:
        """Run the spinner animation."""
        message = self._build_message()
        frame_idx = 0

        while not self._stop_event.is_set():
            frame = self.FRAMES[frame_idx % len(self.FRAMES)]
            line = f"\r{frame} {message}..."
            sys.stderr.write(line)
            sys.stderr.flush()
            frame_idx += 1
            time.sleep(self.INTERVAL)

        sys.stderr.write(f"\r✓ {message} - done\n")
        sys.stderr.flush()

    def start(self) -> None:
        """Start the spinner."""
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the spinner."""
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=1.0)
        self._thread = None


@contextmanager
def task_spinner(message: str, details: Optional[str] = None):
    """Context manager for a generic task spinner.

    Args:
        message: Task description.
        details: Optional details like duration or count.

    Yields:
        The spinner instance.

    Example:
        with task_spinner("Transcribing audio", "120.5s"):
            transcribe_audio()
    """
    spinner = TaskSpinner(message, details)
    spinner.start()
    try:
        yield spinner
    finally:
        spinner.stop()
