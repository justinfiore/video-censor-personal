import json
import logging
import os
import tempfile
import threading
from dataclasses import dataclass, asdict
from threading import Timer, Lock
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Individual detection within a segment."""
    label: str
    confidence: float
    reasoning: str


def _parse_time_to_seconds(time_value: Any) -> float:
    """Convert time value to seconds (float).
    
    Handles both float seconds and string time format (HH:MM:SS).
    
    Args:
        time_value: Either a float (seconds) or string (HH:MM:SS or MM:SS)
        
    Returns:
        Time in seconds as float
    """
    if isinstance(time_value, (int, float)):
        return float(time_value)
    
    if isinstance(time_value, str):
        parts = time_value.split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = int(parts[0]), float(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = int(parts[0]), int(parts[1]), float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0.0
    
    return 0.0


@dataclass
class Segment:
    """Represents a single detected segment."""
    id: str
    start_time: float
    end_time: float
    duration_seconds: float
    labels: List[str]
    description: str
    confidence: float
    detections: List[Detection]
    allow: bool = False
    reviewed: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], segment_id: str) -> 'Segment':
        """Create Segment from dictionary."""
        detections = [
            Detection(
                label=d.get('label', ''),
                confidence=d.get('confidence', 0.0),
                reasoning=d.get('reasoning', '')
            )
            for d in data.get('detections', [])
        ]
        
        return cls(
            id=segment_id,
            start_time=_parse_time_to_seconds(data.get('start_time', 0.0)),
            end_time=_parse_time_to_seconds(data.get('end_time', 0.0)),
            duration_seconds=data.get('duration_seconds', 0.0),
            labels=data.get('labels', []),
            description=data.get('description', ''),
            confidence=data.get('confidence', 0.0),
            detections=detections,
            allow=data.get('allow', False),
            reviewed=data.get('reviewed', False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Segment to dictionary."""
        result = {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': self.duration_seconds,
            'labels': self.labels,
            'description': self.description,
            'confidence': self.confidence,
            'detections': [
                {
                    'label': d.label,
                    'confidence': d.confidence,
                    'reasoning': d.reasoning
                }
                for d in self.detections
            ],
            'allow': self.allow,
            'reviewed': self.reviewed
        }
        return result


class AsyncWriteQueue:
    """Async write queue with debouncing for batched JSON persistence.
    
    Buffers segment changes in memory and writes to disk at most once
    every debounce_seconds. Provides dirty state tracking and callbacks
    for sync status UI updates.
    """
    
    def __init__(self, write_fn: Callable[[], None], debounce_seconds: float = 2.0):
        self._write_fn = write_fn
        self._debounce = debounce_seconds
        self._dirty = False
        self._timer: Optional[Timer] = None
        self._lock = Lock()
        self._on_status_change: Optional[Callable[[bool], None]] = None
    
    def set_status_callback(self, callback: Callable[[bool], None]) -> None:
        """Set callback for sync status changes.
        
        Args:
            callback: Function called with True when dirty, False when clean
        """
        self._on_status_change = callback
    
    def mark_dirty(self) -> None:
        """Mark data as dirty and schedule a write."""
        with self._lock:
            was_dirty = self._dirty
            self._dirty = True
            logger.debug("AsyncWriteQueue: mark_dirty called, was_dirty=%s", was_dirty)
            if not was_dirty and self._on_status_change:
                logger.info("AsyncWriteQueue: Status changed to dirty, invoking callback")
                self._on_status_change(True)
            self._schedule_write()
    
    def _schedule_write(self) -> None:
        """Schedule a debounced write."""
        if self._timer:
            self._timer.cancel()
            logger.debug("AsyncWriteQueue: Cancelled existing timer")
        self._timer = Timer(self._debounce, self._flush)
        self._timer.daemon = True
        self._timer.start()
        logger.info("AsyncWriteQueue: Scheduled write in %.1f seconds", self._debounce)
    
    def _flush(self) -> None:
        """Flush pending changes to disk."""
        logger.debug("AsyncWriteQueue: _flush called")
        with self._lock:
            if self._dirty:
                logger.info("AsyncWriteQueue: Flushing pending changes to disk")
                try:
                    self._write_fn()
                    self._dirty = False
                    logger.info("AsyncWriteQueue: Save completed successfully, status now clean")
                    if self._on_status_change:
                        logger.debug("AsyncWriteQueue: Invoking status callback with is_dirty=False")
                        self._on_status_change(False)
                except Exception as e:
                    logger.error("AsyncWriteQueue: Save failed with exception: %s", e, exc_info=True)
            else:
                logger.debug("AsyncWriteQueue: _flush called but not dirty, skipping")
    
    def flush_sync(self, timeout: float = 10.0) -> bool:
        """Synchronously flush pending changes.
        
        Args:
            timeout: Maximum time to wait (not currently used, reserved for future)
            
        Returns:
            True if flush was successful or nothing to flush, False on error
        """
        logger.debug("AsyncWriteQueue: flush_sync called")
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
                logger.debug("AsyncWriteQueue: Cancelled pending timer in flush_sync")
            if self._dirty:
                logger.info("AsyncWriteQueue: Performing synchronous flush")
                try:
                    self._write_fn()
                    self._dirty = False
                    logger.info("AsyncWriteQueue: Synchronous flush completed successfully")
                    if self._on_status_change:
                        self._on_status_change(False)
                    return True
                except Exception as e:
                    logger.error("AsyncWriteQueue: Synchronous flush failed: %s", e, exc_info=True)
                    return False
            else:
                logger.debug("AsyncWriteQueue: flush_sync called but nothing to flush")
            return True
    
    def is_dirty(self) -> bool:
        """Check if there are pending changes."""
        with self._lock:
            return self._dirty
    
    def cleanup(self) -> None:
        """Cancel any pending timer."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None


class SegmentManager:
    """Manages segments loaded from JSON with in-memory modifications."""
    
    def __init__(self):
        self.segments: List[Segment] = []
        self.file_path: Optional[str] = None
        self.video_file: Optional[str] = None
        self.output_video_file: Optional[str] = None
        self._original_data: Optional[Dict[str, Any]] = None
        self._write_queue: Optional[AsyncWriteQueue] = None
    
    def _init_write_queue(self) -> None:
        """Initialize the async write queue."""
        if self._write_queue:
            self._write_queue.cleanup()
        self._write_queue = AsyncWriteQueue(self._do_save_to_json)
    
    def set_sync_status_callback(self, callback: Callable[[bool], None]) -> None:
        """Set callback for sync status changes.
        
        Args:
            callback: Function called with True when dirty, False when synchronized
        """
        if self._write_queue:
            self._write_queue.set_status_callback(callback)
    
    def load_from_json(self, file_path: str) -> None:
        """Load segments from JSON file.
        
        Args:
            file_path: Path to JSON file containing detection results
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid or missing required fields
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
        
        self._validate_schema(data)
        self._original_data = data
        self.file_path = file_path
        
        # Get video file from metadata or legacy 'file' field
        metadata = data.get('metadata', {})
        video_file_ref = metadata.get('file') or data.get('file')
        
        # Resolve video file path relative to JSON directory
        self.video_file = self._resolve_video_path(file_path, video_file_ref)
        
        # Detect and add output video file to metadata if it exists
        self._detect_output_video(file_path)
        if self.output_video_file:
            if 'metadata' not in self._original_data:
                self._original_data['metadata'] = {}
            self._original_data['metadata']['output_file'] = self.output_video_file
        
        segments_data = data.get('segments', [])
        self.segments = [
            Segment.from_dict(seg, str(idx))
            for idx, seg in enumerate(segments_data)
        ]
        
        # Initialize async write queue
        self._init_write_queue()
    
    def _resolve_video_path(self, json_path: str, video_file_ref: str) -> str:
        """Resolve video file path, trying multiple strategies.
        
        Args:
            json_path: Path to JSON file
            video_file_ref: Video file reference from JSON
            
        Returns:
            Absolute path to video file if found, otherwise the reference as-is
        """
        if not video_file_ref:
            return video_file_ref
        
        # If already absolute, return as-is
        if os.path.isabs(video_file_ref):
            return video_file_ref
        
        json_dir = os.path.dirname(json_path)
        
        # Strategy 1: Relative to JSON directory
        path1 = os.path.join(json_dir, video_file_ref)
        if os.path.exists(path1):
            return os.path.abspath(path1)
        
        # Strategy 2: Relative to JSON's parent directory (common case where JSON is in output-video/)
        parent_dir = os.path.dirname(json_dir)
        path2 = os.path.join(parent_dir, video_file_ref)
        if os.path.exists(path2):
            return os.path.abspath(path2)
        
        # Strategy 3: Look in video-samples or similar subdirectories
        for subdir in ['video-samples', 'samples', 'videos']:
            path3 = os.path.join(parent_dir, subdir, video_file_ref)
            if os.path.exists(path3):
                return os.path.abspath(path3)
        
        # If nothing found, return as reference (will fail at runtime, but at least we tried)
        return video_file_ref
    
    def _detect_output_video(self, json_path: str) -> None:
        """Detect output video file in the same directory as the JSON.
        
        Looks for a file matching the pattern: {json_basename}-clean.{video_ext}
        
        Args:
            json_path: Path to the JSON file
        """
        self.output_video_file = None
        
        if not self.video_file:
            return
        
        json_dir = os.path.dirname(json_path)
        json_basename = os.path.basename(json_path)
        json_name_no_ext = os.path.splitext(json_basename)[0]
        
        # Get video extension from the original video file
        video_ext = os.path.splitext(self.video_file)[1].lower()
        if not video_ext:
            video_ext = '.mp4'  # Default to mp4
        
        # Look for output video with pattern: {json_name}-clean.{ext}
        output_video_name = f"{json_name_no_ext}-clean{video_ext}"
        output_video_path = os.path.join(json_dir, output_video_name)
        
        if os.path.exists(output_video_path):
            self.output_video_file = output_video_path
    
    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """Validate JSON schema.
        
        Args:
            data: Parsed JSON data
            
        Raises:
            ValueError: If schema is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")
        
        if 'segments' not in data:
            raise ValueError("JSON must contain 'segments' field")
        
        if not isinstance(data['segments'], list):
            raise ValueError("'segments' must be an array")
        
        for idx, segment in enumerate(data['segments']):
            required_fields = ['start_time', 'end_time', 'labels', 'detections']
            for field in required_fields:
                if field not in segment:
                    raise ValueError(f"Segment {idx} missing required field: {field}")
    
    def get_all_segments(self) -> List[Segment]:
        """Get all segments."""
        return self.segments
    
    def get_segment_by_id(self, segment_id: str) -> Optional[Segment]:
        """Get segment by ID."""
        for segment in self.segments:
            if segment.id == segment_id:
                return segment
        return None
    
    def toggle_allow(self, segment_id: str) -> bool:
        """Toggle allow status for a segment.
        
        Args:
            segment_id: ID of segment to toggle
            
        Returns:
            New allow status
            
        Raises:
            ValueError: If segment not found
        """
        segment = self.get_segment_by_id(segment_id)
        if segment is None:
            raise ValueError(f"Segment not found: {segment_id}")
        
        segment.allow = not segment.allow
        return segment.allow
    
    def set_allow(self, segment_id: str, allow: bool) -> None:
        """Set allow status for a segment.
        
        Args:
            segment_id: ID of segment to update
            allow: New allow status
            
        Raises:
            ValueError: If segment not found
        """
        segment = self.get_segment_by_id(segment_id)
        if segment is None:
            raise ValueError(f"Segment not found: {segment_id}")
        
        segment.allow = allow
    
    def save_to_json(self) -> None:
        """Queue async save of segments to JSON file.
        
        Uses the async write queue to batch writes. For immediate writes,
        use flush_sync() after calling this method.
        
        Raises:
            ValueError: If no file loaded
        """
        logger.debug("SegmentManager.save_to_json: Called, file_path=%s", self.file_path)
        if self.file_path is None:
            raise ValueError("No file loaded")
        
        if self._write_queue:
            logger.debug("SegmentManager.save_to_json: Calling mark_dirty on write queue")
            self._write_queue.mark_dirty()
        else:
            logger.debug("SegmentManager.save_to_json: No write queue, doing immediate save")
            self._do_save_to_json()
    
    def _do_save_to_json(self) -> None:
        """Perform the actual JSON file save with atomic write.
        
        Raises:
            ValueError: If no file loaded
            IOError: If write fails
        """
        logger.info("SegmentManager._do_save_to_json: Starting save to %s", self.file_path)
        if self.file_path is None:
            raise ValueError("No file loaded")
        
        if self._original_data is None:
            raise ValueError("No original data to save")
        
        output_data = self._original_data.copy()
        output_data['segments'] = [seg.to_dict() for seg in self.segments]
        
        # Make file paths relative to JSON directory if possible
        if 'metadata' in output_data:
            json_dir = os.path.dirname(self.file_path)
            
            # Make video_file relative to JSON directory
            if self.video_file:
                if os.path.isabs(self.video_file):
                    try:
                        relative_path = os.path.relpath(self.video_file, json_dir)
                        output_data['metadata']['file'] = relative_path
                    except ValueError:
                        # On Windows, relpath can fail if paths are on different drives
                        output_data['metadata']['file'] = self.video_file
                else:
                    output_data['metadata']['file'] = self.video_file
            
            # Make output_file relative to JSON directory
            if self.output_video_file:
                if os.path.isabs(self.output_video_file):
                    try:
                        relative_path = os.path.relpath(self.output_video_file, json_dir)
                        output_data['metadata']['output_file'] = relative_path
                    except ValueError:
                        # On Windows, relpath can fail if paths are on different drives
                        output_data['metadata']['output_file'] = self.output_video_file
                else:
                    output_data['metadata']['output_file'] = self.output_video_file
        
        dir_name = os.path.dirname(self.file_path)
        base_name = os.path.basename(self.file_path)
        
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=dir_name,
                prefix=f'.{base_name}.',
                suffix='.tmp',
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                json.dump(output_data, temp_file, indent=2)
                temp_path = temp_file.name
            
            os.replace(temp_path, self.file_path)
            logger.info("SegmentManager._do_save_to_json: Save completed successfully to %s", self.file_path)
            
        except Exception as e:
            logger.error("SegmentManager._do_save_to_json: Save failed: %s", e, exc_info=True)
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise IOError(f"Failed to save JSON file: {e}")
    
    def flush_sync(self, timeout: float = 10.0) -> bool:
        """Synchronously flush pending changes to disk.
        
        Args:
            timeout: Maximum time to wait (reserved for future use)
            
        Returns:
            True if flush was successful or nothing to flush, False on error
        """
        if self._write_queue:
            return self._write_queue.flush_sync(timeout)
        return True
    
    def cleanup(self) -> None:
        """Clean up resources including the async write queue."""
        if self._write_queue:
            self._write_queue.cleanup()
            self._write_queue = None
    
    def get_segments_by_label(self, label: str) -> List[Segment]:
        """Get all segments with a specific label."""
        return [seg for seg in self.segments if label in seg.labels]
    
    def get_segments_by_allow_status(self, allow: bool) -> List[Segment]:
        """Get all segments with specific allow status."""
        return [seg for seg in self.segments if seg.allow == allow]
    
    def batch_set_allow_by_label(self, label: str, allow: bool) -> int:
        """Set allow status for all segments with a specific label.
        
        Args:
            label: Label to filter by
            allow: New allow status
            
        Returns:
            Number of segments updated
        """
        count = 0
        for segment in self.segments:
            if label in segment.labels:
                segment.allow = allow
                count += 1
        return count
    
    def set_reviewed(self, segment_id: str, reviewed: bool) -> None:
        """Set reviewed status for a segment.
        
        Args:
            segment_id: ID of segment to update
            reviewed: New reviewed status
            
        Raises:
            ValueError: If segment not found
        """
        segment = self.get_segment_by_id(segment_id)
        if segment is None:
            raise ValueError(f"Segment not found: {segment_id}")
        
        segment.reviewed = reviewed
    
    def get_segments_by_reviewed_status(self, reviewed: bool) -> List[Segment]:
        """Get all segments with specific reviewed status."""
        return [seg for seg in self.segments if seg.reviewed == reviewed]
    
    def batch_set_reviewed(self, segment_ids: List[str], reviewed: bool) -> int:
        """Set reviewed status for multiple segments.
        
        Args:
            segment_ids: List of segment IDs to update
            reviewed: New reviewed status
            
        Returns:
            Number of segments updated
        """
        count = 0
        id_set = set(segment_ids)
        for segment in self.segments:
            if segment.id in id_set:
                segment.reviewed = reviewed
                count += 1
        return count
    
    def update_segment(
        self,
        segment_id: str,
        new_start_time: Optional[float] = None,
        new_end_time: Optional[float] = None,
        new_labels: Optional[List[str]] = None
    ) -> None:
        """Update segment properties.
        
        Args:
            segment_id: ID of segment to update
            new_start_time: New start time in seconds (optional)
            new_end_time: New end time in seconds (optional)
            new_labels: New labels list (optional)
            
        Raises:
            ValueError: If segment not found or times are invalid
        """
        segment = self.get_segment_by_id(segment_id)
        if segment is None:
            raise ValueError(f"Segment not found: {segment_id}")
        
        start = new_start_time if new_start_time is not None else segment.start_time
        end = new_end_time if new_end_time is not None else segment.end_time
        
        if start >= end:
            raise ValueError(f"Start time ({start}) must be less than end time ({end})")
        
        if start < 0:
            raise ValueError(f"Start time cannot be negative: {start}")
        
        if new_start_time is not None:
            segment.start_time = new_start_time
        if new_end_time is not None:
            segment.end_time = new_end_time
        
        segment.duration_seconds = segment.end_time - segment.start_time
        
        if new_labels is not None:
            segment.labels = new_labels
        
        self.save_to_json()
    
    def duplicate_segment(self, segment_id: str) -> Segment:
        """Duplicate a segment.
        
        Creates a new segment with the same properties but a unique ID.
        The new segment is inserted immediately after the original.
        
        Args:
            segment_id: ID of segment to duplicate
            
        Returns:
            The newly created segment
            
        Raises:
            ValueError: If segment not found
        """
        import uuid
        
        segment = self.get_segment_by_id(segment_id)
        if segment is None:
            raise ValueError(f"Segment not found: {segment_id}")
        
        new_segment = Segment(
            id=str(uuid.uuid4()),
            start_time=segment.start_time,
            end_time=segment.end_time,
            duration_seconds=segment.duration_seconds,
            labels=segment.labels.copy(),
            description=segment.description,
            confidence=segment.confidence,
            detections=[
                Detection(
                    label=d.label,
                    confidence=d.confidence,
                    reasoning=d.reasoning
                )
                for d in segment.detections
            ],
            allow=segment.allow,
            reviewed=False
        )
        
        original_index = self.segments.index(segment)
        self.segments.insert(original_index + 1, new_segment)
        
        self.save_to_json()
        
        return new_segment
    
    def delete_segment(self, segment_id: str) -> Optional[str]:
        """Delete a segment.
        
        Args:
            segment_id: ID of segment to delete
            
        Returns:
            ID of the next segment in list (for auto-selection), or None if no segments remain
            
        Raises:
            ValueError: If segment not found
        """
        segment = self.get_segment_by_id(segment_id)
        if segment is None:
            raise ValueError(f"Segment not found: {segment_id}")
        
        segment_index = self.segments.index(segment)
        self.segments.remove(segment)
        
        self.save_to_json()
        
        if not self.segments:
            return None
        
        if segment_index < len(self.segments):
            return self.segments[segment_index].id
        else:
            return self.segments[-1].id
