"""Performance profiling utility for tracking UI initialization timing."""

import logging
import time
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger("video_censor_personal.ui")


class PerformanceProfiler:
    """Utility class for detailed performance profiling and timing instrumentation."""
    
    def __init__(self):
        """Initialize profiler with empty timings."""
        self.timings: Dict[str, float] = {}
        self.start_times: Dict[str, float] = {}
        self.phase_start_time: Optional[float] = None
    
    def start_phase(self, phase_name: str) -> None:
        """Mark the start of a profiling phase.
        
        Args:
            phase_name: Name of the phase (e.g., "JSON loading", "Segment list population")
        """
        self.phase_start_time = time.time()
        logger.debug(f"[PROFILE] Starting phase: {phase_name}")
    
    def end_phase(self, phase_name: str) -> float:
        """Mark the end of a profiling phase and log elapsed time.
        
        Args:
            phase_name: Name of the phase
            
        Returns:
            Elapsed time in seconds
        """
        if self.phase_start_time is None:
            logger.warning(f"[PROFILE] end_phase called for '{phase_name}' but no phase was started")
            return 0.0
        
        elapsed = time.time() - self.phase_start_time
        self.timings[phase_name] = elapsed
        logger.debug(f"[PROFILE] Completed phase: {phase_name} ({elapsed:.2f}s)")
        self.phase_start_time = None
        return elapsed
    
    def start_operation(self, operation_name: str) -> None:
        """Start timing an individual operation.
        
        Args:
            operation_name: Name of the operation (e.g., "Widget creation")
        """
        self.start_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str) -> float:
        """End timing an individual operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Elapsed time in seconds
        """
        if operation_name not in self.start_times:
            logger.warning(f"[PROFILE] end_operation called for '{operation_name}' but no start time recorded")
            return 0.0
        
        elapsed = time.time() - self.start_times[operation_name]
        self.timings[operation_name] = elapsed
        logger.debug(f"[PROFILE] Operation: {operation_name} ({elapsed:.3f}s)")
        del self.start_times[operation_name]
        return elapsed
    
    def add_timing(self, operation_name: str, elapsed_seconds: float) -> None:
        """Record a pre-calculated timing.
        
        Args:
            operation_name: Name of the operation
            elapsed_seconds: Elapsed time in seconds
        """
        self.timings[operation_name] = elapsed_seconds
        logger.debug(f"[PROFILE] Operation: {operation_name} ({elapsed_seconds:.3f}s)")
    
    def get_timing(self, operation_name: str) -> Optional[float]:
        """Get recorded timing for an operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Elapsed time in seconds, or None if not recorded
        """
        return self.timings.get(operation_name)
    
    def get_all_timings(self) -> Dict[str, float]:
        """Get all recorded timings.
        
        Returns:
            Dictionary mapping operation names to elapsed times
        """
        return self.timings.copy()
    
    def print_summary(self) -> None:
        """Print a summary of all recorded timings."""
        logger.info("=" * 60)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 60)
        
        total_time = sum(self.timings.values())
        
        for operation, elapsed in sorted(self.timings.items(), key=lambda x: x[1], reverse=True):
            percentage = (elapsed / total_time * 100) if total_time > 0 else 0
            logger.info(f"{operation:.<45} {elapsed:>8.2f}s ({percentage:>5.1f}%)")
        
        logger.info("-" * 60)
        logger.info(f"{'Total':.<45} {total_time:>8.2f}s")
        logger.info("=" * 60)
    
    def save_summary(self, output_file: str) -> None:
        """Save performance summary to a file.
        
        Args:
            output_file: Path to save the summary
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("PERFORMANCE SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            total_time = sum(self.timings.values())
            
            f.write("Detailed Timings:\n")
            for operation, elapsed in sorted(self.timings.items(), key=lambda x: x[1], reverse=True):
                percentage = (elapsed / total_time * 100) if total_time > 0 else 0
                f.write(f"{operation:.<45} {elapsed:>8.2f}s ({percentage:>5.1f}%)\n")
            
            f.write("-" * 60 + "\n")
            f.write(f"{'Total':.<45} {total_time:>8.2f}s\n")
            f.write("=" * 60 + "\n")
        
        logger.info(f"Performance summary saved to: {output_path}")
