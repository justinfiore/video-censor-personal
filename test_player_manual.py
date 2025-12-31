#!/usr/bin/env python
"""Manual test of video player with audio."""

import sys
import os
import json
import logging
import threading
import time

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_player.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_censor_personal.ui.pyav_video_player import PyAVVideoPlayer
from video_censor_personal.ui.segment_manager import Segment

# Load test JSON
json_file = "/Users/justinfiore/workspace/personal/video-censor-personal/output-video/Psych1_1.json"

with open(json_file, 'r') as f:
    data = json.load(f)

video_path = data.get('metadata', {}).get('video_path', '')
if not video_path:
    video_path = "/Users/justinfiore/workspace/personal/video-censor-personal/video-samples/Psych1_1.mp4"
segments = [Segment.from_dict(s, f"segment_{i}") for i, s in enumerate(data.get('segments', []))]

logger.info(f"Video: {video_path}")
logger.info(f"Segments: {len(segments)}")

# Create player
try:
    player = PyAVVideoPlayer()
    logger.info("Player created")
    
    # Load video
    player.load(video_path)
    logger.info(f"Video loaded, duration={player.get_duration():.2f}s")
    
    # Seek to 42s
    player.seek(42.0)
    logger.info("Seeked to 42s")
    
    # Play
    logger.info("Starting playback...")
    player.play()
    
    # Let it play for 5 seconds
    for i in range(5):
        time.sleep(1)
        current = player.get_current_time()
        is_playing = player.is_playing()
        has_audio_player = player._audio_player is not None
        logger.info(f"t={current:.2f}s, playing={is_playing}, audio_player={has_audio_player}")
    
    logger.info("Test complete")
    player.cleanup()
    
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
