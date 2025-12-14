"""Command-line interface for video-censor-personal."""

import argparse
import logging
from pathlib import Path


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


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging based on log level.

    Args:
        log_level: One of "INFO", "DEBUG", or "TRACE".
            - INFO: Standard info logging
            - DEBUG: Debug-level logging
            - TRACE: Debug-level logging (detailed output handled separately)
    """
    # TRACE uses DEBUG level for Python logging; detailed output is handled separately
    level = logging.DEBUG if log_level in ("DEBUG", "TRACE") else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
