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
    
    def extract_non_censored_segments(
        self,
        segments: List[Dict[str, Any]],
        video_duration: float,
    ) -> List[Dict[str, float]]:
        """Extract non-censored segments for cut mode.
        
        Inverts the censored segments to get the segments that should be kept.
        
        Args:
            segments: List of censored segment dicts with start_time, end_time.
            video_duration: Total video duration in seconds.
        
        Returns:
            List of segment dicts with 'start' and 'end' (in seconds).
        """
        if not segments:
            # No censored segments, keep entire video
            return [{"start": 0.0, "end": video_duration}]
        
        # Parse and sort censored segments by start time
        censored = []
        for segment in segments:
            start = self._parse_timecode(segment["start_time"])
            end = self._parse_timecode(segment["end_time"])
            censored.append({"start": start, "end": end})
        
        censored.sort(key=lambda x: x["start"])
        
        # Extract non-censored segments
        keep_segments = []
        current_pos = 0.0
        
        for segment in censored:
            # Add segment before this censored part
            if current_pos < segment["start"]:
                keep_segments.append({
                    "start": current_pos,
                    "end": segment["start"]
                })
            
            # Move position to end of censored segment
            current_pos = max(current_pos, segment["end"])
        
        # Add final segment if there's video left after last censored part
        if current_pos < video_duration:
            keep_segments.append({
                "start": current_pos,
                "end": video_duration
            })
        
        return keep_segments
    
    def generate_concat_file(
        self,
        segments: List[Dict[str, float]],
        concat_file_path: str,
    ) -> None:
        """Generate ffmpeg concat demuxer file for cut mode.
        
        Creates a text file listing video segments to concatenate.
        
        Args:
            segments: List of segment dicts with 'start' and 'end' (in seconds).
            concat_file_path: Path where concat file will be written.
        """
        with open(concat_file_path, "w") as f:
            for segment in segments:
                # Write in concat demuxer format
                # Note: We'll extract segments first, then list them here
                f.write(f"file 'segment_{segment['start']}_{segment['end']}.mp4'\n")
    
    def apply_cut_mode(
        self,
        input_video: str,
        output_video: str,
        censored_segments: List[Dict[str, Any]],
        video_duration: float,
        work_dir: Optional[str] = None,
    ) -> None:
        """Apply cut mode remediation to video.
        
        Extracts non-censored segments and concatenates them together.
        
        Args:
            input_video: Path to input video file.
            output_video: Path to output video file.
            censored_segments: List of censored segment dicts.
            video_duration: Total video duration in seconds.
            work_dir: Working directory for temporary files (default: temp dir).
        
        Raises:
            RuntimeError: If ffmpeg fails.
        """
        import tempfile
        import shutil
        
        # Extract non-censored segments
        keep_segments = self.extract_non_censored_segments(
            censored_segments, video_duration
        )
        
        if not keep_segments:
            logger.warning("No segments to keep; entire video is censored")
            return
        
        # Create working directory
        if work_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="video_cut_")
        else:
            temp_dir = work_dir
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            segment_files = []
            
            # Extract each non-censored segment
            for i, segment in enumerate(keep_segments):
                segment_file = Path(temp_dir) / f"segment_{i}.mp4"
                
                cmd = [
                    "ffmpeg",
                    "-i", input_video,
                    "-ss", str(segment["start"]),
                    "-to", str(segment["end"]),
                    "-c:v", "libx264",  # Re-encode video
                    "-c:a", "aac",  # Re-encode audio
                    "-preset", "ultrafast",
                    "-avoid_negative_ts", "1",
                    "-y",
                    str(segment_file)
                ]
                
                logger.debug(f"Extracting segment {i}: {segment['start']}-{segment['end']}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to extract segment {i}: {result.stderr}")
                
                segment_files.append(segment_file)
            
            # Create concat file
            concat_file = Path(temp_dir) / "concat.txt"
            with open(concat_file, "w") as f:
                for segment_file in segment_files:
                    # Use relative paths for concat file
                    f.write(f"file '{segment_file.name}'\n")
            
            # Concatenate segments
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c:v", "copy",  # Copy video stream
                "-c:a", "copy" if len(segment_files) > 0 else "aac",  # Copy audio if present
                "-y",
                output_video
            ]
            
            logger.debug(f"Concatenating {len(segment_files)} segments")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to concatenate segments: {result.stderr}")
            
            logger.info(f"Cut mode applied: kept {len(keep_segments)} segments")
            
        finally:
            # Clean up temporary directory
            if work_dir is None:
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def resolve_segment_mode(
        self,
        segment: Dict[str, Any],
    ) -> str:
        """Resolve the remediation mode for a segment using three-tier hierarchy.
        
        Precedence (first match wins):
        1. Segment-level override: segment.video_remediation field
        2. Category-based default: category_modes config per category
        3. Global default: self.mode
        
        For segments with multiple labels, uses most restrictive mode (cut > blank).
        
        Args:
            segment: Segment dict with optional video_remediation and labels fields.
        
        Returns:
            Resolved mode ("blank" or "cut").
        """
        # Tier 1: Segment-level override
        segment_mode = segment.get("video_remediation")
        if segment_mode:
            # Validate segment mode
            valid_modes = {"blank", "cut"}
            if segment_mode not in valid_modes:
                logger.warning(
                    f"Invalid segment mode '{segment_mode}' at {segment.get('start_time')}, "
                    f"using category/global default"
                )
            else:
                logger.debug(f"Using segment-level mode: {segment_mode}")
                return segment_mode
        
        # Tier 2: Category-based default
        labels = segment.get("labels", [])
        if labels and self.category_modes:
            category_mode = self._resolve_category_mode(labels)
            if category_mode:
                logger.debug(f"Using category mode: {category_mode} for labels {labels}")
                return category_mode
        
        # Tier 3: Global default
        logger.debug(f"Using global mode: {self.mode}")
        return self.mode
    
    def _resolve_category_mode(self, labels: List[str]) -> Optional[str]:
        """Resolve mode from multiple category labels.
        
        Uses most restrictive mode when multiple labels present.
        "cut" is more restrictive than "blank".
        
        Args:
            labels: List of category labels.
        
        Returns:
            Resolved mode or None if no category has configured mode.
        """
        if not labels:
            return None
        
        modes = []
        for label in labels:
            if label in self.category_modes:
                modes.append(self.category_modes[label])
        
        if not modes:
            return None
        
        # "cut" is more restrictive than "blank"
        if "cut" in modes:
            return "cut"
        
        return "blank"
