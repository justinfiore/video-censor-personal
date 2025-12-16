"""Command-line interface for video-censor-personal."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict


def create_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser for CLI.
    """
    parser = argparse.ArgumentParser(
        prog="video_censor_personal",
        description=(
            "Analyze videos to detect nudity, profanity, violence, sexual themes, "
            "and custom concepts."
        ),
        epilog=(
            "Example: python video_censor_personal.py --input video.mp4 "
            "--config config.yaml --output results.json"
        ),
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input video file",
        metavar="PATH",
    )

    parser.add_argument(
        "--output",
        type=str,
        required=False,
        help="Path to output results JSON file (default: results.json)",
        metavar="PATH",
        default="results.json",
    )

    parser.add_argument(
        "--config",
        type=str,
        required=False,
        help="Path to YAML configuration file (default: ./video-censor.yaml)",
        metavar="PATH",
    )

    parser.add_argument(
        "--output-video",
        type=str,
        required=False,
        help=(
            "Path to output video file with remediated audio "
            "(required if audio remediation enabled in config)"
        ),
        metavar="PATH",
    )

    parser.add_argument(
        "--download-models",
        action="store_true",
        help=(
            "Automatically download and verify required models before analysis. "
            "Models are downloaded only if missing or checksums don't match. "
            "Requires models.sources configured in YAML."
        ),
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["INFO", "DEBUG", "TRACE"],
        default="INFO",
        help=(
            "Set logging verbosity: INFO (default, with progress bar), "
            "DEBUG (debug logging + progress bar), "
            "TRACE (debug logging + detailed frame-by-frame output)"
        ),
    )

    parser.add_argument(
        "--allow-all-segments",
        action="store_true",
        help=(
            "During analysis phase, automatically mark all detected segments with 'allow: true' "
            "in the output JSON. Useful for preview/test runs. "
            "This flag only applies during analysis; it has no effect during remediation phase "
            "(when using --input-segments to load JSON from a previous analysis)."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


def parse_args(args=None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of arguments to parse (default: sys.argv[1:]).

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = create_parser()
    return parser.parse_args(args)


TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging based on log level.

    Args:
        log_level: One of "INFO", "DEBUG", or "TRACE".
            - INFO: Standard info logging
            - DEBUG: Debug-level logging
            - TRACE: Detailed frame-by-frame and model inference logging
    """
    if log_level == "TRACE":
        level = TRACE_LEVEL
    elif log_level == "DEBUG":
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def validate_cli_args(
    args: argparse.Namespace, config: Dict[str, Any]
) -> None:
    """Validate CLI arguments against configuration.

    Ensures consistency between CLI arguments and configuration, particularly
    for output video handling with audio remediation and skip chapters features.

    Args:
        args: Parsed command-line arguments.
        config: Configuration dictionary.

    Raises:
        SystemExit: If validation fails.
    """
    from video_censor_personal.config import is_skip_chapters_enabled

    logger = logging.getLogger(__name__)
    
    # Check if skip chapters is enabled
    skip_chapters_enabled = is_skip_chapters_enabled(config)
    
    # Check if audio remediation is enabled
    audio_remediation_enabled = config.get("audio", {}).get("remediation", {}).get("enabled", False)
    
    # Require --output-video when skip chapters is enabled
    if skip_chapters_enabled and not args.output_video:
        logger.error(
            "Skip chapters feature is enabled but --output-video is not specified. "
            "--output-video is required when skip chapters are enabled."
        )
        sys.exit(1)
    
    # Warn if --output-video is provided but neither feature needs it
    if args.output_video and not skip_chapters_enabled and not audio_remediation_enabled:
        logger.warning(
            "--output-video provided but skip chapters and audio remediation are both disabled. "
            "The output video file will not be generated."
        )
    
    # Check for input/output-video path match (overwrite protection)
    if args.output_video:
        input_path = Path(args.input).resolve()
        output_path = Path(args.output_video).resolve()
        
        if input_path == output_path:
            logger.warning(
                "WARNING: Output video file matches input file. "
                "This will overwrite the original video."
            )
            # Prompt for confirmation
            try:
                response = input("Continue? (y/n): ").strip().lower()
                if response != "y":
                    logger.info("Operation cancelled by user.")
                    sys.exit(0)
            except EOFError:
                # In non-interactive mode (e.g., CI/CD), treat as "no"
                logger.error(
                    "Cannot confirm overwrite in non-interactive mode. "
                    "Please use different input and output paths."
                )
                sys.exit(1)
