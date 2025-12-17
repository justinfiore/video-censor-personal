"""Video remediation engine for blanking or cutting detected visual content."""

import logging
import shutil
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
            # Handle plain numeric seconds format (int or float)
            if isinstance(timecode, (int, float)):
                return float(timecode)
            
            # Handle string formats
            timecode_str = str(timecode)
            
            # Handle HH:MM:SS[.mmm] format
            if ":" in timecode_str:
                parts = timecode_str.split(":")
                if len(parts) == 3:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            
            # Handle plain seconds format (string)
            return float(timecode_str)
        
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
    
    def filter_allowed_segments(
        self,
        segments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Filter out segments marked as allowed.
        
        Segments with "allow": true should not be remediated.
        
        Args:
            segments: List of segment dicts with optional allow field.
        
        Returns:
            List of segments to remediate (those without allow=true).
        """
        filtered = []
        for segment in segments:
            if segment.get("allow", False):
                logger.debug(
                    f"Skipping allowed segment at {segment.get('start_time')}"
                )
                continue
            filtered.append(segment)
        
        logger.info(f"Filtered {len(segments) - len(filtered)} allowed segments")
        return filtered
    
    def group_segments_by_mode(
        self,
        segments: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group segments by remediation mode.
        
        Useful for combined remediation where different modes may be used.
        
        Args:
            segments: List of segment dicts.
        
        Returns:
            Dict mapping mode ("blank" or "cut") to list of segments.
        """
        groups = {"blank": [], "cut": []}
        
        for segment in segments:
            mode = self.resolve_segment_mode(segment)
            groups[mode].append(segment)
        
        logger.debug(
            f"Grouped segments: {len(groups['blank'])} blank, {len(groups['cut'])} cut"
        )
        return groups
    
    def validate_timecode(self, timecode: str) -> bool:
        """Validate timecode format.
        
        Args:
            timecode: Timecode string to validate.
        
        Returns:
            True if valid, False otherwise.
        """
        try:
            self._parse_timecode(timecode)
            return True
        except ValueError:
            return False
    
    def check_disk_space(
        self,
        output_path: str,
        required_mb: int = 100,
    ) -> bool:
        """Check if sufficient disk space is available.
        
        Args:
            output_path: Path to output file/directory.
            required_mb: Required space in MB (default: 100MB).
        
        Returns:
            True if sufficient space available, False otherwise.
        """
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir = Path.cwd()
        
        stat = shutil.disk_usage(output_dir)
        available_mb = stat.free / (1024 * 1024)
        
        if available_mb < required_mb:
            logger.warning(
                f"Low disk space: {available_mb:.1f}MB available, "
                f"{required_mb}MB required"
            )
            return False
        
        return True
    
    def apply(
        self,
        input_video: str,
        output_video: str,
        segments: List[Dict[str, Any]],
        video_duration: float,
        video_width: int,
        video_height: int,
    ) -> None:
        """Apply video remediation to input video.
        
        Applies configured remediation mode (blank or cut) to detected segments.
        Filters out segments marked with "allow": true.
        
        Args:
            input_video: Path to input video file.
            output_video: Path to output video file.
            segments: List of detected segments with start_time, end_time, etc.
            video_duration: Total video duration in seconds.
            video_width: Video width in pixels.
            video_height: Video height in pixels.
        
        Raises:
            RuntimeError: If remediation fails.
        """
        if not self.enabled:
            logger.debug("Video remediation disabled, skipping")
            return
        
        # Filter out allowed segments
        segments_to_remediate = self.filter_allowed_segments(segments)
        
        if not segments_to_remediate:
            logger.info("No segments to remediate (all marked as allowed)")
            # Copy input to output if no remediation needed
            import shutil
            shutil.copy2(input_video, output_video)
            return
        
        # Group by mode
        grouped = self.group_segments_by_mode(segments_to_remediate)
        
        has_blank = len(grouped["blank"]) > 0
        has_cut = len(grouped["cut"]) > 0
        
        logger.info(
            f"Applying video remediation: "
            f"{len(grouped['blank'])} blank, {len(grouped['cut'])} cut"
        )
        
        try:
            if has_blank and has_cut:
                # Mixed modes: apply blank first, then cut
                logger.debug("Mixed modes detected: applying blank then cut")
                import tempfile
                
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    temp_path = tmp.name
                
                try:
                    # Apply blank mode to temp file
                    self._apply_blank_mode_impl(
                        input_video, temp_path, grouped["blank"], video_width, video_height
                    )
                    
                    # Apply cut mode to final output (cutting from blanked video)
                    # Adjust blank segments to account for timeline, but use original timings
                    self.apply_cut_mode(
                        temp_path, output_video, grouped["cut"], video_duration
                    )
                finally:
                    Path(temp_path).unlink(missing_ok=True)
            
            elif has_blank:
                # Only blank mode
                self._apply_blank_mode_impl(
                    input_video, output_video, grouped["blank"], video_width, video_height
                )
            
            elif has_cut:
                # Only cut mode
                self.apply_cut_mode(
                    input_video, output_video, grouped["cut"], video_duration
                )
            
            logger.info(f"Video remediation complete: {output_video}")
        
        except Exception as e:
            logger.error(f"Video remediation failed: {e}", exc_info=True)
            raise RuntimeError(f"Video remediation failed: {e}") from e
    
    def _apply_blank_mode_impl(
        self,
        input_video: str,
        output_video: str,
        segments: List[Dict[str, Any]],
        video_width: int,
        video_height: int,
    ) -> None:
        """Apply blank mode using ffmpeg filter chain.
        
        Args:
            input_video: Path to input video.
            output_video: Path to output video.
            segments: List of segments to blank.
            video_width: Video width in pixels.
            video_height: Video height in pixels.
        
        Raises:
            RuntimeError: If ffmpeg fails.
        """
        filter_chain = self.build_blank_filter_chain(segments, video_width, video_height)
        
        cmd = [
            "ffmpeg",
            "-i", input_video,
            "-filter_complex", filter_chain,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-y",
            output_video
        ]
        
        logger.debug(f"Running ffmpeg blank mode: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            logger.error(f"ffmpeg stderr: {result.stderr}")
            raise RuntimeError(f"ffmpeg blank mode failed: {result.stderr}")
