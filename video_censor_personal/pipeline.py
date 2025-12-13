"""End-to-end analysis pipeline for video processing.

Orchestrates video extraction, frame sampling, detection pipeline execution,
and result aggregation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from video_censor_personal.detection import DetectionPipeline, get_detector_registry
from video_censor_personal.frame import DetectionResult
from video_censor_personal.output import generate_json_output, merge_segments
from video_censor_personal.video_extraction import VideoExtractor

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orchestrates end-to-end video analysis workflow.

    Coordinates:
    1. Video frame extraction at configured sample rate
    2. Detection pipeline execution on sampled frames
    3. Result aggregation and merging
    4. JSON output generation

    Attributes:
        video_path: Path to the input video file.
        config: Configuration dictionary with detectors and processing settings.
        extractor: VideoExtractor instance for frame/audio extraction.
        detection_pipeline: DetectionPipeline instance for detector orchestration.
    """

    def __init__(
        self,
        video_path: str,
        config: Dict[str, Any],
        detector_list: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize the analysis pipeline.

        Args:
            video_path: Path to the input video file.
            config: Configuration dictionary with analysis settings.
            detector_list: Optional list of detector configs. If None, uses config['detectors'].

        Raises:
            FileNotFoundError: If video file does not exist.
            ValueError: If configuration or detectors are invalid.
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        self.config = config
        self.extractor: Optional[VideoExtractor] = None
        self.detection_pipeline: Optional[DetectionPipeline] = None

        # Prepare detector configuration
        detector_configs = detector_list or config.get("detectors")
        if not detector_configs:
            # Fall back to auto-discovery from detections section
            detector_configs = self._auto_discover_detectors(config)

        # Create pipeline config with detectors
        pipeline_config = {"detectors": detector_configs}
        self.detection_pipeline = DetectionPipeline(pipeline_config)

        logger.info(
            f"Initialized AnalysisPipeline for video: {self.video_path} "
            f"with {len(self.detection_pipeline.detectors)} detector(s)"
        )

    def _auto_discover_detectors(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Auto-discover detector configuration from detections section.

        Generates a default LLaVA detector covering all enabled categories.

        Args:
            config: Configuration dictionary.

        Returns:
            List of detector configuration dictionaries.
        """
        detections = config.get("detections", {})
        enabled_categories = [
            cat for cat, cat_config in detections.items()
            if isinstance(cat_config, dict) and cat_config.get("enabled")
        ]

        if not enabled_categories:
            logger.warning("No enabled detection categories found; using empty detector list")
            return []

        # Capitalize category names for detector
        categories = [cat.capitalize() for cat in enabled_categories]

        # Return default LLaVA detector
        return [
            {
                "type": "llava",
                "name": "llava-vision",
                "categories": categories,
                "model_name": "liuhaotian/llava-v1.5-7b",
            }
        ]

    def analyze(self) -> List[DetectionResult]:
        """Run end-to-end analysis pipeline on video.

        Extracts frames at configured sample rate, runs detection pipeline
        on each frame, and aggregates results.

        Returns:
            List of DetectionResult objects from all frames.

        Raises:
            RuntimeError: If video extraction or detection fails.
        """
        logger.info(f"Starting analysis of video: {self.video_path}")
        all_results: List[DetectionResult] = []

        try:
            # Initialize extractor
            self.extractor = VideoExtractor(str(self.video_path))
            logger.debug(
                f"Video info: {self.extractor.get_frame_count()} frames, "
                f"{self.extractor.get_fps():.2f} fps, "
                f"{self.extractor.get_duration_seconds():.2f} seconds"
            )

            # Get sample rate from config
            from video_censor_personal.config import get_sample_rate_from_config
            sample_rate = get_sample_rate_from_config(self.config)
            logger.debug(f"Frame sample rate: {sample_rate} seconds")

            # Extract audio once for all detectors
            audio_data = None
            if any(hasattr(d, "detect") for d in self.detection_pipeline.detectors):
                try:
                    audio_segment = self.extractor.extract_audio()
                    audio_data = audio_segment.data
                    logger.debug(f"Extracted audio: {audio_segment.duration():.2f} seconds")
                except Exception as e:
                    logger.warning(f"Failed to extract audio (continuing without it): {e}")

            # Extract and analyze frames
            frame_count = 0
            for frame in self.extractor.extract_frames(sample_rate=sample_rate):
                try:
                    frame_count += 1
                    logger.debug(f"Analyzing frame {frame.index} at {frame.timestamp_str()}")

                    # Run detection pipeline on frame
                    results = self.detection_pipeline.analyze_frame(frame, audio_data=audio_data)
                    all_results.extend(results)

                    if results:
                        logger.debug(
                            f"Frame {frame.index}: {len(results)} detection(s) found"
                        )

                except Exception as e:
                    logger.error(
                        f"Error analyzing frame {frame.index}: {e}",
                        exc_info=True,
                    )
                    # Continue with next frame
                    continue

            logger.info(
                f"Analysis complete: {frame_count} frames analyzed, "
                f"{len(all_results)} total detections found"
            )
            return all_results

        finally:
            # Cleanup
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up pipeline resources (extractor, detectors).

        Called automatically at end of analyze(), but can be called explicitly
        to free resources early.
        """
        if self.extractor is not None:
            try:
                self.extractor.close()
                logger.debug("Closed video extractor")
            except Exception as e:
                logger.error(f"Error closing extractor: {e}")
            self.extractor = None

        if self.detection_pipeline is not None:
            try:
                self.detection_pipeline.cleanup()
                logger.debug("Cleaned up detection pipeline")
            except Exception as e:
                logger.error(f"Error cleaning up detection pipeline: {e}")

    def __enter__(self) -> "AnalysisPipeline":
        """Context manager entry.

        Returns:
            Self for use in with statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit.

        Ensures cleanup happens even if exceptions occur.
        """
        self.cleanup()


class AnalysisRunner:
    """Helper class to run analysis pipeline from CLI.

    Wraps AnalysisPipeline to handle end-to-end execution including
    output generation.
    """

    def __init__(self, video_path: str, config: Dict[str, Any], config_path: str) -> None:
        """Initialize analysis runner.

        Args:
            video_path: Path to input video file.
            config: Configuration dictionary.
            config_path: Path to configuration file (for metadata).
        """
        self.video_path = video_path
        self.config = config
        self.config_path = config_path

    def run(self, output_path: str) -> Dict[str, Any]:
        """Run analysis and generate JSON output.

        Args:
            output_path: Path where JSON output should be written.

        Returns:
            Output dictionary that was written to file.

        Raises:
            Exception: If analysis or output generation fails.
        """
        logger.info(f"Running analysis: {self.video_path} -> {output_path}")

        with AnalysisPipeline(self.video_path, self.config) as pipeline:
            # Run analysis
            detections = pipeline.analyze()

            # Get video duration
            extractor = VideoExtractor(str(self.video_path))
            try:
                video_duration = extractor.get_duration_seconds()
            finally:
                extractor.close()

            # Merge detection segments
            merge_threshold = self.config.get("processing", {}).get(
                "segment_merge", {}
            ).get("merge_threshold", 2.0)
            merged_segments = merge_segments(detections, threshold=merge_threshold)

            # Generate output
            output_dict = generate_json_output(
                merged_segments,
                self.video_path,
                video_duration,
                self.config_path,
                self.config,
            )

            # Write output
            from video_censor_personal.output import write_output
            write_output(output_dict, output_path, self.config)

            logger.info(f"Analysis complete. Output written to: {output_path}")
            return output_dict
