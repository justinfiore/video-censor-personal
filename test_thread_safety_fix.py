#!/usr/bin/env python3
"""Test script to verify the thread-safety fix for canvas updates."""

import sys
import os
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/test_fix.log')
    ]
)
logger = logging.getLogger(__name__)

# Expected log markers that should appear
EXPECTED_MARKERS = [
    "Render thread received first frame from queue",
    "First frame queued for canvas update",
    "CANVAS UPDATE: Received queued frame",
    "CANVAS UPDATED SUCCESSFULLY"
]

def check_logs():
    """Check if the fix is working by looking for expected log markers."""
    logger.info("Checking logs for thread-safety fix validation...")
    
    log_file = "logs/ui.log"
    if not os.path.exists(log_file):
        logger.error(f"Log file not found: {log_file}")
        return False
    
    with open(log_file, 'r') as f:
        log_content = f.read()
    
    found_markers = {}
    for marker in EXPECTED_MARKERS:
        found = marker in log_content
        found_markers[marker] = found
        status = "✓" if found else "✗"
        logger.info(f"{status} {marker}")
    
    all_found = all(found_markers.values())
    
    if all_found:
        logger.info("\n✓ ALL EXPECTED MARKERS FOUND - Thread-safety fix is working!")
        return True
    else:
        missing = [m for m, found in found_markers.items() if not found]
        logger.error(f"\n✗ MISSING MARKERS (pipeline breaks here):")
        for marker in missing:
            logger.error(f"  - {marker}")
        
        # Additional diagnostics
        logger.error("\nDIAGNOSTICS:")
        if "Render thread received first frame from queue" in log_content:
            logger.error("  - Render thread IS receiving frames")
            if "First frame queued for canvas update" not in log_content:
                logger.error("  - But render thread is NOT queueing them for display")
                logger.error("  - Check: PIL import, Image.fromarray, PhotoImage creation")
        
        if "Starting playback" in log_content:
            logger.error("  - Playback started")
        
        if "Extracting audio" in log_content:
            logger.error("  - Audio extraction started")
        
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("VIDEO PLAYER THREAD-SAFETY FIX TEST")
    print("="*60 + "\n")
    
    success = check_logs()
    sys.exit(0 if success else 1)
