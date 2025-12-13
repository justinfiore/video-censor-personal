"""Video muxing engine for combining video and audio.

Re-muxes remediated audio back into original video container using ffmpeg.
Preserves video codec (lossless) and encodes audio as AAC.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VideoMuxer:
    """Re-muxes remediated audio into video container.
    
    Uses ffmpeg to combine original video with remediated audio WAV file,
    writing output as MP4 with video passthrough (no re-encoding) and
    AAC audio encoding.
    
    Attributes:
        original_video_path: Path to original video file.
        remediated_audio_path: Path to remediated audio WAV file.
    """
    
    def __init__(self, original_video_path: str, remediated_audio_path: str) -> None:
        """Initialize video muxer.
        
        Args:
            original_video_path: Path to original video file.
            remediated_audio_path: Path to remediated audio WAV file.
        
        Raises:
            FileNotFoundError: If input files don't exist.
        """
        self.original_video_path = Path(original_video_path)
        self.remediated_audio_path = Path(remediated_audio_path)
        
        if not self.original_video_path.exists():
            raise FileNotFoundError(
                f"Original video not found: {self.original_video_path}"
            )
        if not self.remediated_audio_path.exists():
            raise FileNotFoundError(
                f"Remediated audio not found: {self.remediated_audio_path}"
            )
        
        logger.debug(
            f"Initialized VideoMuxer: video={self.original_video_path}, "
            f"audio={self.remediated_audio_path}"
        )
    
    def mux_video(self, output_video_path: str) -> None:
        """Mux remediated audio into video.
        
        Uses ffmpeg command:
            ffmpeg -i original_video.mp4 -i remediated_audio.wav \
                   -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
                   -shortest output_video.mp4
        
        Flags:
            -c:v copy: Copy video codec (no re-encoding, fast)
            -c:a aac: Encode audio as AAC (compatible with most players)
            -map 0:v:0: Use first video stream from original video
            -map 1:a:0: Use first audio stream from remediated audio
            -shortest: Stop at shortest stream (handles any sample rate differences)
            -y: Overwrite output file
        
        Args:
            output_video_path: Path where muxed video will be saved.
        
        Raises:
            RuntimeError: If ffmpeg not available or muxing fails.
        """
        output_path = Path(output_video_path)
        
        # Check ffmpeg available
        if not self._check_ffmpeg():
            raise RuntimeError(
                "ffmpeg not available. Please install ffmpeg. "
                "See: https://ffmpeg.org/download.html"
            )
        
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(self.original_video_path),
            "-i", str(self.remediated_audio_path),
            "-c:v", "copy",    # Copy video codec (no re-encoding)
            "-c:a", "aac",     # Encode audio as AAC
            "-map", "0:v:0",   # Video from first input
            "-map", "1:a:0",   # Audio from second input
            "-shortest",       # Stop at shortest stream
            "-y",              # Overwrite output
            str(output_path),
        ]
        
        logger.info(f"Muxing video: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise RuntimeError(
                    f"ffmpeg muxing failed with exit code {result.returncode}: {error_msg}"
                )
            
            logger.info(f"Video muxing complete: {output_path}")
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("ffmpeg muxing timed out")
        except Exception as e:
            raise RuntimeError(f"Video muxing failed: {e}") from e
    
    @staticmethod
    def _check_ffmpeg() -> bool:
        """Check if ffmpeg is available in PATH.
        
        Returns:
            True if ffmpeg available, False otherwise.
        """
        import shutil
        return shutil.which("ffmpeg") is not None
