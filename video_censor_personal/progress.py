"""Progress bar utilities for video processing."""

import sys
import time
from typing import Optional

from tqdm import tqdm


class VideoProgressBar:
    """Progress bar for video processing with time estimates.
    
    Displays:
    - Percentage complete
    - Current time position / Total duration
    - Time elapsed
    - Estimated time remaining
    - Visual progress bar
    """

    def __init__(
        self,
        total_duration: float,
        description: str = "Processing",
        disable: bool = False,
    ) -> None:
        """Initialize video progress bar.
        
        Args:
            total_duration: Total video duration in seconds.
            description: Description text for the progress bar.
            disable: If True, disable progress bar display.
        """
        self.total_duration = total_duration
        self.description = description
        self.disable = disable
        self._pbar: Optional[tqdm] = None
        self._start_time: Optional[float] = None
        self._last_position: float = 0.0
        
    def start(self) -> None:
        """Start the progress bar."""
        if self.disable:
            return
            
        self._start_time = time.time()
        self._pbar = tqdm(
            total=100,
            desc=self.description,
            unit="%",
            bar_format=(
                "{desc}: {percentage:3.0f}%|{bar}| "
                "{n:.1f}/{total:.0f}% "
                "[{elapsed}<{remaining}, {rate_fmt}]"
            ),
            file=sys.stderr,
            leave=True,
        )
        
    def update(self, current_position: float) -> None:
        """Update progress bar to current video position.
        
        Args:
            current_position: Current position in video (seconds).
        """
        if self.disable or self._pbar is None:
            return
            
        if self.total_duration <= 0:
            return
            
        percentage = min(100.0, (current_position / self.total_duration) * 100)
        delta = percentage - self._last_position
        if delta > 0:
            self._pbar.update(delta)
            self._last_position = percentage
            
        # Update postfix with time info
        elapsed = time.time() - (self._start_time or time.time())
        if percentage > 0:
            estimated_total = elapsed / (percentage / 100)
            remaining = max(0, estimated_total - elapsed)
        else:
            remaining = 0
            
        self._pbar.set_postfix_str(
            f"{self._format_time(current_position)}/{self._format_time(self.total_duration)} "
            f"ETA: {self._format_time(remaining)}"
        )
        
    def close(self) -> None:
        """Close the progress bar."""
        if self._pbar is not None:
            self._pbar.update(100 - self._last_position)
            self._pbar.close()
            self._pbar = None
            
    def __enter__(self) -> "VideoProgressBar":
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
        
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as HH:MM:SS or MM:SS.
        
        Args:
            seconds: Time in seconds.
            
        Returns:
            Formatted time string.
        """
        if seconds < 0:
            return "00:00"
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


class DebugOutput:
    """Helper for structured debug output when --debug is enabled."""
    
    def __init__(self, enabled: bool = False) -> None:
        """Initialize debug output helper.
        
        Args:
            enabled: If True, output debug information.
        """
        self.enabled = enabled
        self._indent = 0
        
    def section(self, title: str) -> None:
        """Print a section header.
        
        Args:
            title: Section title.
        """
        if not self.enabled:
            return
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"DEBUG: {title}", file=sys.stderr)
        print(f"{'=' * 60}", file=sys.stderr)
        
    def subsection(self, title: str) -> None:
        """Print a subsection header.
        
        Args:
            title: Subsection title.
        """
        if not self.enabled:
            return
        print(f"\n{'-' * 40}", file=sys.stderr)
        print(f"  {title}", file=sys.stderr)
        print(f"{'-' * 40}", file=sys.stderr)
        
    def info(self, message: str) -> None:
        """Print debug info message.
        
        Args:
            message: Message to print.
        """
        if not self.enabled:
            return
        indent = "  " * self._indent
        print(f"{indent}[DEBUG] {message}", file=sys.stderr)
        
    def detail(self, key: str, value: object) -> None:
        """Print a key-value detail.
        
        Args:
            key: Detail key/name.
            value: Detail value.
        """
        if not self.enabled:
            return
        indent = "  " * (self._indent + 1)
        print(f"{indent}{key}: {value}", file=sys.stderr)
        
    def frame_info(
        self,
        frame_index: int,
        timestamp: float,
        detections: int,
    ) -> None:
        """Print frame processing info.
        
        Args:
            frame_index: Frame index.
            timestamp: Frame timestamp in seconds.
            detections: Number of detections found.
        """
        if not self.enabled:
            return
        ts_str = VideoProgressBar._format_time(timestamp)
        print(
            f"  [Frame {frame_index:4d}] {ts_str} - {detections} detection(s)",
            file=sys.stderr,
        )
        
    def detector_result(
        self,
        detector_name: str,
        category: str,
        confidence: float,
    ) -> None:
        """Print detector result.
        
        Args:
            detector_name: Name of detector.
            category: Detection category.
            confidence: Detection confidence.
        """
        if not self.enabled:
            return
        print(
            f"    [{detector_name}] {category}: {confidence:.2%}",
            file=sys.stderr,
        )
        
    def step(self, description: str) -> None:
        """Print a processing step.
        
        Args:
            description: Step description.
        """
        if not self.enabled:
            return
        print(f"  → {description}", file=sys.stderr)
