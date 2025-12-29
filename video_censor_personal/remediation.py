"""Shared remediation logic for both analysis and remediation-only modes.

This module provides unified remediation (audio and video) logic that can be used by both:
1. AnalysisPipeline (analysis mode with detection)
2. RemediationRunner (remediation-only mode with pre-loaded segments)

The key design principle is that both modes follow the same remediation sequence:
1. Apply audio remediation (using original timestamps)
2. Apply video remediation (may shift timelines via cuts)
3. Mux remediated audio back into video (with optional metadata tags)

This ensures consistent behavior regardless of whether segments came from detection or pre-loaded JSON.
"""

import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class RemediationManager:
    """Manages audio and video remediation for both analysis and remediation-only modes.
    
    Handles:
    - Audio remediation with arbitrary detection results or segments
    - Video remediation with tracking of output file states
    - Audio/video muxing with proper file sequencing
    - Temporary file management and cleanup
    """
    
    def __init__(
        self,
        input_video_path: str,
        config: Dict[str, Any],
        output_video_path: Optional[str] = None,
        log_level: str = "INFO",
        config_file: Optional[str] = None,
        segment_file: Optional[str] = None,
        processed_timestamp: Optional[datetime] = None,
    ) -> None:
        """Initialize remediation manager.
        
        Args:
            input_video_path: Path to the original input video file.
            config: Configuration dictionary with remediation settings.
            output_video_path: Optional path for final output video. If not specified,
                             no video output will be produced even if remediation is enabled.
            log_level: Logging level (INFO, DEBUG, TRACE).
            config_file: Optional path to the config file used (for metadata).
            segment_file: Optional path to the segment file used (for metadata).
            processed_timestamp: Optional datetime when remediation started (for metadata).
        """
        self.input_video_path = Path(input_video_path)
        if not self.input_video_path.exists():
            raise FileNotFoundError(f"Input video not found: {self.input_video_path}")
        
        self.config = config
        self.output_video_path = output_video_path
        self.log_level = log_level
        self.trace_enabled = log_level == "TRACE"
        
        # Metadata tracking for output video
        self.config_file = config_file
        self.segment_file = segment_file
        self.processed_timestamp = processed_timestamp or datetime.now()
        
        # Track intermediate file states
        self.remediated_audio_path: Optional[str] = None
        
        # Import debug output here to avoid circular imports
        from video_censor_personal.progress import DebugOutput
        self.debug_output = DebugOutput(enabled=self.trace_enabled)
    
    def apply_remediation(
        self,
        detections_or_segments: Union[
            List["DetectionResult"],  # For analysis mode: DetectionResult objects
            List[Dict[str, Any]],      # For remediation mode: segment dicts with allow flag
        ],
        segments_for_allow_check: Optional[List[Dict[str, Any]]] = None,
        audio_data: Optional[Any] = None,
        audio_sample_rate: Optional[int] = None,
        video_width: Optional[int] = None,
        video_height: Optional[int] = None,
        video_duration: Optional[float] = None,
        merged_segments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Apply all remediation in the correct order.
        
        This is the main entry point for both analysis and remediation-only modes.
        It orchestrates:
        1. Audio remediation (if enabled and audio data provided) → temp audio file
        2. Mux remediated audio with original video → output_video_path
        3. Video remediation on output_video_path (if enabled and output_video_path specified)
        
        This sequence ensures audio/video sync when video has cuts, since both tracks
        are already combined before video remediation runs.
        
        Args:
            detections_or_segments: Either DetectionResult objects or segment dicts.
                                   For segments with "allow" flag, pass segments_for_allow_check.
            segments_for_allow_check: Segment dicts that may have "allow" flag (to skip remediation).
                                     Only used for audio remediation when passed.
            audio_data: Original audio data (numpy array or bytes).
            audio_sample_rate: Sample rate of audio data.
            video_width: Video width (required for video remediation).
            video_height: Video height (required for video remediation).
            video_duration: Total video duration in seconds (required for video remediation).
            merged_segments: Merged/deduplicated segments for video remediation.
                            If None and detections_or_segments are dicts, will use those.
        
        Raises:
            ValueError: If required parameters are missing for enabled remediation.
            Exception: If remediation fails.
        """
        logger.info("Starting remediation sequence")
        
        # Step 1: Apply audio remediation (if enabled) → creates temp audio file
        if audio_data is not None and audio_sample_rate is not None:
            self._apply_audio_remediation(
                audio_data,
                audio_sample_rate,
                detections_or_segments,
                segments_for_allow_check,
            )
        
        # Step 2: Mux remediated audio into video (BEFORE video remediation)
        # This must happen BEFORE video remediation so audio/video are combined before video cutting
        if self.remediated_audio_path and self.output_video_path:
            self._mux_remediated_audio()
        
        # Step 3: Apply video remediation on output file (if enabled)
        # This operates on the output file that may already have muxed audio
        if merged_segments is not None:
            self._apply_video_remediation(
                merged_segments,
                video_width,
                video_height,
                video_duration,
            )
        elif isinstance(detections_or_segments, list) and len(detections_or_segments) > 0:
            # If detections_or_segments are dicts and no merged_segments provided, use them
            if isinstance(detections_or_segments[0], dict):
                self._apply_video_remediation(
                    detections_or_segments,
                    video_width,
                    video_height,
                    video_duration,
                )
    
    def _apply_audio_remediation(
        self,
        audio_data: Any,
        audio_sample_rate: int,
        detections_or_segments: Union[List["DetectionResult"], List[Dict[str, Any]]],
        segments_for_allow_check: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Apply audio remediation if enabled.
        
        Args:
            audio_data: Audio data (numpy array or bytes).
            audio_sample_rate: Sample rate in Hz.
            detections_or_segments: Either DetectionResult objects or segment dicts.
            segments_for_allow_check: Segment dicts with "allow" flag for skipping.
        """
        remediation_config = self.config.get("remediation", {}).get("audio", {})
        if not remediation_config.get("enabled", False):
            logger.debug("Audio remediation disabled")
            return
        
        self.debug_output.subsection("Audio Remediation")
        self.debug_output.step("Applying audio remediation...")
        self.debug_output.detail("Method", remediation_config.get("mode", "silence"))
        self.debug_output.detail("Sample rate", f"{audio_sample_rate} Hz")
        
        try:
            import numpy as np
            import soundfile as sf
            import io
            
            from video_censor_personal.audio_remediator import AudioRemediator
            
            # Convert audio to numpy if needed
            audio_np = audio_data
            if isinstance(audio_data, bytes):
                audio_np, sr = sf.read(
                    io.BytesIO(audio_data),
                    dtype='float32'
                )
                audio_sample_rate = sr
            
            remediator = AudioRemediator(remediation_config)
            
            # For DetectionResult objects, convert to segments if needed
            if segments_for_allow_check:
                # Using provided segments (remediation-only mode)
                remediated_audio = remediator.remediate(
                    audio_np,
                    audio_sample_rate,
                    detections_or_segments,
                    segments=segments_for_allow_check,
                )
            else:
                # Using detections directly (analysis mode)
                remediated_audio = remediator.remediate(
                    audio_np,
                    audio_sample_rate,
                    detections_or_segments,
                )
            
            # Write remediated audio
            output_audio_path = remediation_config.get(
                "output_path",
                tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            )
            remediator.write_audio(
                remediated_audio,
                audio_sample_rate,
                output_audio_path
            )
            self.remediated_audio_path = output_audio_path
            logger.info(f"Remediated audio saved to: {output_audio_path}")
            self.debug_output.step(f"Audio saved to: {output_audio_path}")
            
        except Exception as e:
            logger.error(f"Audio remediation failed: {e}", exc_info=True)
            self.debug_output.info(f"ERROR: Audio remediation failed: {e}")
            raise
    
    def _apply_video_remediation(
        self,
        segments: List[Dict[str, Any]],
        video_width: Optional[int] = None,
        video_height: Optional[int] = None,
        video_duration: Optional[float] = None,
    ) -> None:
        """Apply video remediation if enabled.
        
        At this point in the sequence:
        - If audio was remediated, it's already been muxed into output_video_path
        - If audio wasn't remediated, output_video_path may not exist yet
        
        When audio is remediated: operates directly on output_video_path (which has muxed audio)
        When audio isn't remediated: creates output_video_path by copying and remediating input
        
        Args:
            segments: List of segment dicts with start_time/end_time.
            video_width: Video width (required).
            video_height: Video height (required).
            video_duration: Video duration in seconds (required).
        """
        video_config = self.config.get("remediation", {}).get("video", {})
        if not video_config.get("enabled", False):
            logger.debug("Video remediation disabled")
            return
        
        if not self.output_video_path:
            logger.warning(
                "Video remediation enabled but output video path not specified. Skipping."
            )
            return
        
        if not video_width or not video_height or not video_duration:
            logger.warning(
                "Video remediation enabled but missing video metadata "
                f"(width={video_width}, height={video_height}, duration={video_duration}). Skipping."
            )
            return
        
        try:
            from video_censor_personal.video_remediator import VideoRemediator
            import shutil
            
            self.debug_output.subsection("Video Remediation")
            self.debug_output.step("Applying video remediation...")
            self.debug_output.detail("Mode", video_config.get("mode", "blank"))
            self.debug_output.detail("Segments", len(segments))
            
            logger.info(f"Using {len(segments)} segments for video remediation")
            
            # Format segments for remediation
            remediation_segments = self._format_segments_for_remediation(segments)
            
            if not remediation_segments:
                logger.info("No segments to remediate; ensuring output file exists")
                if not Path(self.output_video_path).exists():
                    logger.debug(f"Copying input to output")
                    shutil.copy2(str(self.input_video_path), self.output_video_path)
                self.debug_output.step("No segments to remediate")
                return
            
            # Initialize VideoRemediator
            remediator = VideoRemediator(video_config)
            
            # Determine input file for video remediation
            # At this point, if audio was remediated, it's already been muxed into output_video_path
            if self.remediated_audio_path:
                # Audio was remediated and already muxed into output_video_path
                # So video remediation operates directly on output_video_path
                # Must use a temp file since ffmpeg can't write to the same file it reads from
                video_input = self.output_video_path
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    video_output = tmp.name
                logger.debug(
                    f"Audio remediation detected; applying video remediation to muxed file"
                )
            else:
                # No audio remediation
                # Always use the original input file
                video_input = str(self.input_video_path)
                video_output = self.output_video_path
                logger.debug(f"No audio remediation; applying video remediation to original input")
            
            # Apply video remediation
            remediator.apply(
                video_input,
                video_output,
                remediation_segments,
                video_duration,
                video_width,
                video_height,
            )
            
            # If we used a temp file, move it to the final output
            if self.remediated_audio_path:
                shutil.move(video_output, self.output_video_path)
                logger.debug(f"Moved temp video remediation to output")
            
            logger.info(f"Video remediation saved to: {self.output_video_path}")
            self.debug_output.step("Video remediation complete")
        
        except Exception as e:
            logger.error(f"Video remediation failed: {e}", exc_info=True)
            self.debug_output.info(f"ERROR: Video remediation failed: {e}")
            raise

    
    def _mux_remediated_audio(self) -> None:
        """Mux remediated audio into video with optional metadata.
        
        This runs BEFORE video remediation, so it simply muxes the remediated audio
        with the original video, creating the output file that will be used as input
        for video remediation (if enabled).
        
        When video remediation is not enabled, this output file is the final result.
        When video remediation is enabled, it will operate on this output file in-place.
        
        Adds metadata tags (config file, segment file, timestamp, remediation flags)
        and updates the title with "(Censored)" suffix if configured.
        """
        if not self.remediated_audio_path or not self.output_video_path:
            logger.debug("No audio muxing needed (no remediated audio or no output path)")
            return
        
        self.debug_output.subsection("Video Muxing")
        self.debug_output.step("Muxing remediated audio into video...")
        
        try:
            from video_censor_personal.video_muxer import VideoMuxer
            from video_censor_personal.video_metadata import (
                extract_original_title,
                create_censored_title,
                build_remediation_metadata,
            )
            import shutil
            
            # Extract original title and create censored version
            original_title = extract_original_title(str(self.input_video_path))
            censored_title = create_censored_title(original_title, str(self.input_video_path))
            
            # Build remediation metadata if we have the required info
            metadata = {}
            if self.config_file and self.segment_file:
                audio_remediation_enabled = (
                    self.config.get("remediation", {}).get("audio", {}).get("enabled", False)
                )
                video_remediation_enabled = (
                    self.config.get("remediation", {}).get("video", {}).get("enabled", False)
                )
                metadata = build_remediation_metadata(
                    self.config_file,
                    self.segment_file,
                    self.processed_timestamp,
                    audio_remediation_enabled,
                    video_remediation_enabled,
                )
                logger.debug(f"Built remediation metadata: {len(metadata)} tags")
            else:
                logger.debug("Skipping remediation metadata (config_file or segment_file not provided)")
            
            # Mux remediated audio with the original video
            # (or with pre-existing output if skip chapters already created it)
            if Path(self.output_video_path).exists():
                video_source = self.output_video_path
                logger.debug("Muxing into pre-existing output file (e.g., from skip chapters)")
            else:
                video_source = str(self.input_video_path)
                logger.debug("Muxing remediated audio with original video")
            
            muxer = VideoMuxer(
                video_source,
                self.remediated_audio_path,
                metadata=metadata,
                title=censored_title,
            )
            
            # Always use a temp file to avoid ffmpeg's limitation with moving files it's writing to
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                temp_output = tmp.name
            
            muxer.mux_video(temp_output)
            
            # Replace the output file with the muxed version
            shutil.move(temp_output, self.output_video_path)
            logger.debug(f"Moved temp muxed video to: {self.output_video_path}")
            
            logger.info(f"Audio muxed into video with metadata: {self.output_video_path}")
            self.debug_output.step(f"Audio muxed into video with metadata: {self.output_video_path}")
        
        except Exception as e:
            logger.error(f"Video muxing failed: {e}", exc_info=True)
            self.debug_output.info(f"ERROR: Video muxing failed: {e}")
            raise
    
    def _format_segments_for_remediation(
        self,
        merged_segments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Format merged segments for video remediator.
        
        Args:
            merged_segments: List of segment dicts with float times.
        
        Returns:
            List of segments formatted for video remediation.
        """
        formatted = []
        for segment in merged_segments:
            formatted_segment = {
                "start_time": segment["start_time"],  # Keep as float (seconds)
                "end_time": segment["end_time"],      # Keep as float (seconds)
                "labels": segment.get("labels", []),
            }
            
            # Copy over other fields if present
            if "confidence" in segment:
                formatted_segment["confidence"] = segment["confidence"]
            if "allow" in segment:
                formatted_segment["allow"] = segment["allow"]
            if "detections" in segment:
                formatted_segment["detections"] = segment["detections"]
            
            formatted.append(formatted_segment)
        
        return formatted
    
    def cleanup(self) -> None:
        """Clean up temporary files created during remediation."""
        if self.remediated_audio_path:
            try:
                Path(self.remediated_audio_path).unlink(missing_ok=True)
                logger.debug(f"Cleaned up remediated audio: {self.remediated_audio_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up remediated audio: {e}")
