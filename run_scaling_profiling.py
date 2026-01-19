#!/usr/bin/env python3
"""Script to run profiling on small and large videos for scaling analysis."""

import os
import sys
import json
import tempfile
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Import UI components
from video_censor_personal.ui.preview_editor import PreviewEditorApp, logger

def create_synthetic_json(output_path: str, num_segments: int, video_file: str = "test_video.mp4") -> None:
    """Create a synthetic JSON file with the specified number of segments.
    
    Args:
        output_path: Path where JSON will be saved
        num_segments: Number of segments to generate
        video_file: Video file path to reference in JSON
    """
    segments = []
    duration_per_segment = 3600 / max(num_segments, 1)  # Assume 1 hour video
    
    labels_options = [
        ["Nudity"],
        ["Violence"],
        ["Sexual Theme"],
        ["Profanity"],
        ["Nudity", "Sexual Theme"],
        ["Violence", "Profanity"],
    ]
    
    for i in range(num_segments):
        segment = {
            "start_time": i * duration_per_segment,
            "end_time": (i + 1) * duration_per_segment,
            "duration_seconds": duration_per_segment,
            "labels": labels_options[i % len(labels_options)],
            "description": f"Detected {', '.join(labels_options[i % len(labels_options)])}",
            "confidence": 0.5 + (i % 50) / 100.0,
            "detections": [
                {
                    "label": label,
                    "confidence": 0.5 + (i % 50) / 100.0,
                    "reasoning": f"Test detection for {label}"
                }
                for label in labels_options[i % len(labels_options)]
            ],
            "allow": i % 2 == 0  # Alternate allow/disallow
        }
        segments.append(segment)
    
    data = {
        "metadata": {
            "file": video_file,
            "duration": "01:00:00",
            "duration_seconds": 3600,
            "processed_at": "2026-01-01T00:00:00Z",
            "config": "test.yaml",
            "output_file": f"output_{os.path.basename(video_file)}"
        },
        "segments": segments
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Created {output_path} with {num_segments} segments")

def run_profiling_test(num_segments: int, test_name: str, temp_dir: str) -> Dict[str, float]:
    """Run a profiling test with the specified number of segments.
    
    Args:
        num_segments: Number of segments to test
        test_name: Name of the test for logging
        temp_dir: Temporary directory for test files
        
    Returns:
        Dictionary of timing metrics from profiler
    """
    print(f"\n{'='*60}")
    print(f"Running profiling test: {test_name} ({num_segments} segments)")
    print(f"{'='*60}")
    
    # Create temporary JSON file
    json_path = os.path.join(temp_dir, f"test_{num_segments}_segments.json")
    create_synthetic_json(json_path, num_segments)
    
    # Clear logs before test
    log_path = Path("logs/ui.log")
    if log_path.exists():
        log_path.unlink()
    
    # Create profiler directly (simulating what PreviewEditorApp does)
    from video_censor_personal.ui.performance_profiler import PerformanceProfiler
    from video_censor_personal.ui.segment_manager import SegmentManager
    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl
    
    profiler = PerformanceProfiler()
    
    # Simulate JSON loading phase
    profiler.start_phase(f"JSON Loading ({num_segments} segments)")
    
    # Time JSON parsing
    profiler.start_operation("JSON parsing and segment manager load")
    segment_manager = SegmentManager()
    segment_manager.load_from_json(json_path)
    profiler.end_operation("JSON parsing and segment manager load")
    
    # Get segments
    segments = segment_manager.get_all_segments()
    profiler.start_operation("Segment list population")
    
    # We can't test UI widget creation without a window, so we just measure data loading
    # In real scenario, SegmentListPaneImpl.load_segments() would be called here
    parse_start = time.time()
    unique_labels = set()
    for seg in segments:
        unique_labels.update(seg.labels)
    parse_time = time.time() - parse_start
    
    profiler.end_operation("Segment list population")
    profiler.end_phase(f"JSON Loading ({num_segments} segments)")
    
    # Print summary
    print(f"\nTiming Results for {num_segments} segments:")
    for op_name, elapsed in profiler.get_all_timings().items():
        print(f"  {op_name}: {elapsed:.3f}s")
    
    return profiler.get_all_timings()

def main():
    """Run profiling tests."""
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        results = {}
        
        # Test configurations
        test_configs = [
            (15, "Small Video (15 segments)"),
            (50, "Medium Video (50 segments)"),
            (100, "Large Video (100 segments)"),
            (206, "Extra Large Video (206 segments)"),
        ]
        
        for num_segments, test_name in test_configs:
            try:
                timings = run_profiling_test(num_segments, test_name, temp_dir)
                results[test_name] = timings
            except Exception as e:
                print(f"Error during test: {e}")
                import traceback
                traceback.print_exc()
        
        # Print summary comparison
        print(f"\n{'='*60}")
        print("SUMMARY COMPARISON")
        print(f"{'='*60}")
        
        for test_name, timings in results.items():
            print(f"\n{test_name}:")
            for op_name, elapsed in timings.items():
                print(f"  {op_name}: {elapsed:.3f}s")

if __name__ == "__main__":
    main()
