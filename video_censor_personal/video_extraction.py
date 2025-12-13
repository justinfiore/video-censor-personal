"""Video extraction module for frame and audio extraction using ffmpeg."""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator, Optional

import cv2
import numpy as np

from video_censor_personal.frame import AudioSegment, Frame

logger = logging.getLogger(__name__)


def _check_ffmpeg_available() -> bool:
    """Check if ffmpeg is available in the system PATH.

    Returns:
        True if ffmpeg is available, False otherwise.
    """
    return shutil.which("ffmpeg") is not None


class VideoExtractor:
    """Extract frames and audio from video files.

    This class provides utilities for extracting video frames at configurable
    sample rates and extracting audio streams for content detection.

    Attributes:
        video_path: Path to the input video file.
        _capture: OpenCV VideoCapture object.
        _audio_cache: Cached audio segment (lazy extraction).
        _temp_files: List of temporary files created (for cleanup).
    """

    def __init__(self, video_path: str) -> None:
        """Initialize VideoExtractor with a video file.

        Args:
            video_path: Path to the input video file.

        Raises:
            FileNotFoundError: If video file does not exist.
            RuntimeError: If video file cannot be opened.
        """
        self.video_path = Path(video_path)

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        self._capture = cv2.VideoCapture(str(self.video_path))
        if not self._capture.isOpened():
            raise RuntimeError(
                f"Failed to open video file: {self.video_path}. "
                "Ensure the file format is supported and not corrupted."
            )

        self._audio_cache: Optional[AudioSegment] = None
        self._temp_files: list[Path] = []

    def get_frame_count(self) -> int:
        """Get total number of frames in video.

        Returns:
            Total frame count.
        """
        return int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT))

    def get_duration_seconds(self) -> float:
        """Get video duration in seconds.

        Returns:
            Duration in seconds.
        """
        fps = self.get_fps()
        frame_count = self.get_frame_count()
        if fps <= 0:
            return 0.0
        return frame_count / fps

    def get_fps(self) -> float:
        """Get frames per second of video.

        Returns:
            Frames per second.
        """
        return float(self._capture.get(cv2.CAP_PROP_FPS))

    def extract_frames(
        self, sample_rate: float = 1.0
    ) -> Generator[Frame, None, None]:
        """Extract frames at specified sample rate.

        Yields frames from the video at the specified time interval.
        For example, sample_rate=1.0 yields one frame per second.

        Args:
            sample_rate: Seconds between extracted frames. If 0, extracts
                all frames.

        Yields:
            Frame objects with index, timecode, and pixel data.
        """
        fps = self.get_fps()
        if fps <= 0:
            logger.warning("Invalid FPS detected; cannot extract frames")
            return

        frame_interval = int(fps * sample_rate) if sample_rate > 0 else 1
        frame_index = 0
        extracted_count = 0

        # Reset capture to beginning
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

        while True:
            ret, frame_data = self._capture.read()
            if not ret:
                break

            if sample_rate == 0 or frame_index % frame_interval == 0:
                timecode = frame_index / fps
                yield Frame(
                    index=extracted_count, timecode=timecode, data=frame_data
                )
                extracted_count += 1

            frame_index += 1

    def _get_audio_sample_rate(self) -> Optional[int]:
        """Detect audio sample rate from video using ffprobe.

        Returns:
            Sample rate in Hz, or None if detection fails.
        """
        try:
            import json
            import subprocess
            
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=sample_rate",
                "-of", "json",
                str(self.video_path),
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            if streams:
                return int(streams[0].get("sample_rate", 0))
            return None
        except Exception as e:
            logger.warning(f"Failed to detect audio sample rate: {e}")
            return None

    def extract_audio(self) -> AudioSegment:
        """Extract audio stream from video file.

        Returns audio as a cached numpy array at original sample rate.
        Subsequent calls return the cached result without re-invoking ffmpeg.

        Returns:
            AudioSegment object with audio data and metadata.

        Raises:
            RuntimeError: If ffmpeg is not available or audio extraction fails.
        """
        if self._audio_cache is not None:
            return self._audio_cache

        if not _check_ffmpeg_available():
            raise RuntimeError(
                "ffmpeg is not available. Please install ffmpeg to extract "
                "audio. See installation instructions in README.md."
            )

        duration = self.get_duration_seconds()

        # Create temporary file for audio extraction
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = Path(temp_audio.name)
        temp_audio.close()
        self._temp_files.append(temp_path)

        try:
            # Extract audio using ffmpeg at original sample rate and channels
            # We preserve all channels and sample rate for remediation fidelity.
            # Detection pipelines can downmix/downsample as needed.
            cmd = [
                "ffmpeg",
                "-i",
                str(self.video_path),
                "-q:a",
                "9",
                "-y",
                str(temp_path),
            ]
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            # Read audio file
            with open(temp_path, "rb") as f:
                audio_data = f.read()

            # Get original sample rate from the video using ffprobe
            # Default to 48000 if detection fails
            sample_rate = self._get_audio_sample_rate() or 48000

            self._audio_cache = AudioSegment(
                start_time=0.0,
                end_time=duration,
                data=audio_data,
                sample_rate=sample_rate,
            )
            return self._audio_cache

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to extract audio from {self.video_path}: {e}"
            ) from e

    def extract_audio_segment(
        self, start_sec: float, end_sec: float
    ) -> AudioSegment:
        """Extract audio for specified time range.

        Uses cached full audio if available; otherwise extracts segment
        directly using ffmpeg.

        Args:
            start_sec: Start time in seconds.
            end_sec: End time in seconds.

        Returns:
            AudioSegment object for the specified time range.

        Raises:
            RuntimeError: If ffmpeg is not available or extraction fails.
        """
        if not _check_ffmpeg_available():
            raise RuntimeError(
                "ffmpeg is not available. Please install ffmpeg to extract "
                "audio segments."
            )

        # Create temporary file for segment
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = Path(temp_audio.name)
        temp_audio.close()
        self._temp_files.append(temp_path)

        try:
            # Extract audio segment using ffmpeg
            cmd = [
                "ffmpeg",
                "-i",
                str(self.video_path),
                "-ss",
                str(start_sec),
                "-to",
                str(end_sec),
                "-q:a",
                "9",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-y",
                str(temp_path),
            ]
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            # Read audio file
            with open(temp_path, "rb") as f:
                audio_data = f.read()

            return AudioSegment(
                start_time=start_sec,
                end_time=end_sec,
                data=audio_data,
                sample_rate=16000,
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to extract audio segment from {self.video_path}: {e}"
            ) from e

    def close(self) -> None:
        """Release resources and clean up temporary files.

        Closes the video file handle and removes temporary files created
        during extraction.
        """
        if self._capture is not None:
            self._capture.release()

        # Clean up temporary files
        for temp_file in self._temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except OSError as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

        self._temp_files.clear()

    def __enter__(self) -> "VideoExtractor":
        """Context manager entry.

        Returns:
            Self for use in with statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit.

        Ensures cleanup happens even if exceptions occur.
        """
        self.close()
