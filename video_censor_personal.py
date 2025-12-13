#!/usr/bin/env python3
"""Main entry point for video-censor-personal application."""

import logging
import sys
from pathlib import Path

from video_censor_personal.cli import parse_args, setup_logging
from video_censor_personal.config import ConfigError, load_config
from video_censor_personal.pipeline import AnalysisRunner

logger = logging.getLogger(__name__)


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        # Parse command-line arguments
        args = parse_args()

        # Setup logging
        setup_logging(verbose=args.verbose)

        logger.info("Starting video-censor-personal")
        logger.debug(f"Input file: {args.input}")
        logger.debug(f"Output file: {args.output}")
        logger.debug(f"Config file: {args.config}")
        if args.output_video:
            logger.debug(f"Output video file: {args.output_video}")

        # Validate input file exists
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"Input file not found: {args.input}")
            return 1

        # Load and validate configuration
        try:
            config = load_config(args.config)
            logger.info("Configuration loaded and validated successfully")
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            return 1

        # Validate audio remediation and output-video argument
        remediation_enabled = (
            config.get("audio", {})
            .get("remediation", {})
            .get("enabled", False)
        )

        if remediation_enabled and not args.output_video:
            logger.error(
                "ERROR: Audio remediation is enabled in config, but "
                "--output-video argument is missing.\n\n"
                "To use audio remediation, provide output video path:\n"
                "  python video_censor_personal.py --input video.mp4 "
                "--config config.yaml --output results.json "
                "--output-video output.mp4\n\n"
                "Or disable audio remediation in config:\n"
                "  audio.remediation.enabled: false"
            )
            return 1

        if args.output_video and not remediation_enabled:
            logger.error(
                "ERROR: --output-video argument provided, but audio remediation "
                "is not enabled in config.\n\n"
                "--output-video requires audio remediation to be enabled.\n"
                "Enable remediation in config:\n"
                "  audio.remediation.enabled: true\n\n"
                "Or remove the --output-video argument."
            )
            return 1

        # Run analysis pipeline
        try:
            runner = AnalysisRunner(
                args.input,
                config,
                args.config,
                output_video_path=args.output_video,
            )
            runner.run(args.output)
            logger.info("Processing complete")
            return 0

        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
            return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
