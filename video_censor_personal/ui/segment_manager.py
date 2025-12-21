import json
import os
import tempfile
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


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
            allow=data.get('allow', False)
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
            'allow': self.allow
        }
        return result


class SegmentManager:
    """Manages segments loaded from JSON with in-memory modifications."""
    
    def __init__(self):
        self.segments: List[Segment] = []
        self.file_path: Optional[str] = None
        self.video_file: Optional[str] = None
        self.output_video_file: Optional[str] = None
        self._original_data: Optional[Dict[str, Any]] = None
    
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
        """Save segments to JSON file with atomic write.
        
        Raises:
            ValueError: If no file loaded
            IOError: If write fails
        """
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
            
        except Exception as e:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise IOError(f"Failed to save JSON file: {e}")
    
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
