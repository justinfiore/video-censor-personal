"""Video remediation engine for blanking or cutting detected visual content."""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VideoRemediator:
    """Applies remediation (blank or cut) to detected video segments.
    
    Takes video and detection results, then modifies video by either:
    - Blanking (replacing with solid color screen, keeping audio)
    - Cutting (removing segment entirely from timeline)
    
    Attributes:
        enabled: Whether remediation is active.
        mode: "blank" or "cut".
        blank_color: Hex color for blank mode (e.g., "#000000").
        category_modes: Per-category mode overrides.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize video remediator.
        
        Args:
            config: Configuration dict with:
                - enabled: bool, whether remediation is active (default: False)
                - mode: "blank" or "cut" (default: "blank")
                - blank_color: Hex color string (default: "#000000")
                - category_modes: Dict mapping categories to modes
        
        Raises:
            ValueError: If config is invalid.
        """
        self.enabled = config.get("enabled", False)
        self.mode = config.get("mode", "blank")
        self.blank_color = config.get("blank_color", "#000000")
        self.category_modes = config.get("category_modes", {})
        
        # Validate mode
        valid_modes = {"blank", "cut"}
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid remediation mode: {self.mode}. Must be one of {valid_modes}")
        
        # Validate category modes
        for category, mode in self.category_modes.items():
            if mode not in valid_modes:
                raise ValueError(
                    f"Invalid mode for category '{category}': {mode}. Must be one of {valid_modes}"
                )
        
        # Validate color format
        if not self._is_valid_hex_color(self.blank_color):
            raise ValueError(f"Invalid hex color: {self.blank_color}")
        
        logger.debug(
            f"Initialized VideoRemediator: enabled={self.enabled}, "
            f"mode={self.mode}, blank_color={self.blank_color}"
        )
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """Validate hex color format.
        
        Args:
            color: Hex color string (e.g., "#000000" or "#000").
        
        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(color, str):
            return False
        if not color.startswith("#"):
            return False
        if len(color) not in [4, 7]:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    def _hex_to_ffmpeg_color(self, hex_color: str) -> str:
        """Convert hex color to ffmpeg color format.
        
        Args:
            hex_color: Hex color string (e.g., "#000000" or "#000").
        
        Returns:
            ffmpeg color string (e.g., "0x000000").
        """
        # Convert short form (#RGB) to long form (#RRGGBB)
        if len(hex_color) == 4:
            r, g, b = hex_color[1], hex_color[2], hex_color[3]
            hex_color = f"#{r}{r}{g}{g}{b}{b}"
        
        # Convert #RRGGBB to 0xRRGGBB for ffmpeg
        return f"0x{hex_color[1:]}"
    
    def build_blank_filter_chain(
        self,
        segments: List[Dict[str, Any]],
        video_width: int,
        video_height: int,
    ) -> str:
        """Build ffmpeg filter chain for blank mode.
        
        Creates a filter_complex expression that blanks video segments
        using drawbox with between(t,start,end) expressions.
        
        Args:
            segments: List of segment dicts with start_time, end_time.
            video_width: Video width in pixels.
            video_height: Video height in pixels.
        
        Returns:
            ffmpeg filter_complex string.
        """
        if not segments:
            return ""
        
        # Convert hex color to ffmpeg format
        color = self._hex_to_ffmpeg_color(self.blank_color)
        
        # Build filter chain with drawbox for each segment
        filters = []
        for segment in segments:
            start = self._parse_timecode(segment["start_time"])
            end = self._parse_timecode(segment["end_time"])
            
            # Use drawbox with enable expression for time-based blanking
            # drawbox fills the entire frame with the specified color
            filter_expr = (
                f"drawbox=x=0:y=0:w={video_width}:h={video_height}:"
                f"color={color}:t=fill:enable='between(t,{start},{end})'"
            )
            filters.append(filter_expr)
        
        # Chain all drawbox filters together
        if filters:
            return ",".join(filters)
        
        return ""
    
    def _parse_timecode(self, timecode: str) -> float:
        """Parse timecode string to seconds.
        
        Supports formats:
        - HH:MM:SS
        - HH:MM:SS.mmm
        - SS.mmm
        
        Args:
            timecode: Timecode string.
        
        Returns:
            Time in seconds (float).
        
        Raises:
            ValueError: If timecode format is invalid.
        """
        try:
            # Handle HH:MM:SS[.mmm] format
            if ":" in timecode:
                parts = timecode.split(":")
                if len(parts) == 3:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            
            # Handle plain seconds format
            return float(timecode)
        
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid timecode format: {timecode}") from e
