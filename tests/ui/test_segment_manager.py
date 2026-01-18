import pytest
import json
import os
import tempfile
from video_censor_personal.ui.segment_manager import Segment, SegmentManager, Detection


@pytest.fixture
def sample_json_data():
    return {
        "file": "/path/to/video.mp4",
        "segments": [
            {
                "start_time": 10.5,
                "end_time": 15.2,
                "duration_seconds": 4.7,
                "labels": ["Profanity", "Violence"],
                "description": "Contains inappropriate content",
                "confidence": 0.92,
                "detections": [
                    {
                        "label": "Profanity",
                        "confidence": 0.95,
                        "reasoning": "Detected explicit language"
                    },
                    {
                        "label": "Violence",
                        "confidence": 0.89,
                        "reasoning": "Violent scene detected"
                    }
                ],
                "allow": False
            },
            {
                "start_time": 30.0,
                "end_time": 35.0,
                "duration_seconds": 5.0,
                "labels": ["Profanity"],
                "description": "Minor language issue",
                "confidence": 0.75,
                "detections": [
                    {
                        "label": "Profanity",
                        "confidence": 0.75,
                        "reasoning": "Mild language"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def temp_json_file(sample_json_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(sample_json_data, f)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_segment_from_dict():
    data = {
        "start_time": 10.0,
        "end_time": 20.0,
        "duration_seconds": 10.0,
        "labels": ["Test"],
        "description": "Test segment",
        "confidence": 0.9,
        "detections": [
            {
                "label": "Test",
                "confidence": 0.9,
                "reasoning": "Test reasoning"
            }
        ],
        "allow": True
    }
    
    segment = Segment.from_dict(data, "0")
    
    assert segment.id == "0"
    assert segment.start_time == 10.0
    assert segment.end_time == 20.0
    assert segment.duration_seconds == 10.0
    assert segment.labels == ["Test"]
    assert segment.description == "Test segment"
    assert segment.confidence == 0.9
    assert len(segment.detections) == 1
    assert segment.detections[0].label == "Test"
    assert segment.allow is True


def test_segment_from_dict_default_allow():
    data = {
        "start_time": 10.0,
        "end_time": 20.0,
        "duration_seconds": 10.0,
        "labels": ["Test"],
        "description": "Test segment",
        "confidence": 0.9,
        "detections": []
    }
    
    segment = Segment.from_dict(data, "0")
    assert segment.allow is False


def test_segment_to_dict():
    segment = Segment(
        id="0",
        start_time=10.0,
        end_time=20.0,
        duration_seconds=10.0,
        labels=["Test"],
        description="Test segment",
        confidence=0.9,
        detections=[Detection(label="Test", confidence=0.9, reasoning="Test reasoning")],
        allow=True
    )
    
    data = segment.to_dict()
    
    assert data['start_time'] == 10.0
    assert data['end_time'] == 20.0
    assert data['duration_seconds'] == 10.0
    assert data['labels'] == ["Test"]
    assert data['description'] == "Test segment"
    assert data['confidence'] == 0.9
    assert len(data['detections']) == 1
    assert data['detections'][0]['label'] == "Test"
    assert data['allow'] is True


def test_segment_manager_load_from_json(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    assert len(manager.segments) == 2
    assert manager.file_path == temp_json_file
    assert manager.video_file == "/path/to/video.mp4"
    
    assert manager.segments[0].start_time == 10.5
    assert manager.segments[0].end_time == 15.2
    assert manager.segments[0].labels == ["Profanity", "Violence"]
    assert manager.segments[0].allow is False
    
    assert manager.segments[1].start_time == 30.0
    assert manager.segments[1].allow is False


def test_segment_manager_load_nonexistent_file():
    manager = SegmentManager()
    
    with pytest.raises(FileNotFoundError):
        manager.load_from_json("/nonexistent/file.json")


def test_segment_manager_load_invalid_json():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        manager = SegmentManager()
        with pytest.raises(ValueError, match="Invalid JSON file"):
            manager.load_from_json(temp_path)
    finally:
        os.remove(temp_path)


def test_segment_manager_validate_schema_missing_segments():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump({"file": "video.mp4"}, f)
        temp_path = f.name
    
    try:
        manager = SegmentManager()
        with pytest.raises(ValueError, match="must contain 'segments'"):
            manager.load_from_json(temp_path)
    finally:
        os.remove(temp_path)


def test_segment_manager_validate_schema_missing_required_fields():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        data = {
            "segments": [
                {
                    "start_time": 10.0
                }
            ]
        }
        json.dump(data, f)
        temp_path = f.name
    
    try:
        manager = SegmentManager()
        with pytest.raises(ValueError, match="missing required field"):
            manager.load_from_json(temp_path)
    finally:
        os.remove(temp_path)


def test_segment_manager_get_all_segments(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    segments = manager.get_all_segments()
    assert len(segments) == 2


def test_segment_manager_get_segment_by_id(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    segment = manager.get_segment_by_id("0")
    assert segment is not None
    assert segment.start_time == 10.5
    
    segment = manager.get_segment_by_id("1")
    assert segment is not None
    assert segment.start_time == 30.0
    
    segment = manager.get_segment_by_id("999")
    assert segment is None


def test_segment_manager_toggle_allow(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    assert manager.segments[0].allow is False
    
    result = manager.toggle_allow("0")
    assert result is True
    assert manager.segments[0].allow is True
    
    result = manager.toggle_allow("0")
    assert result is False
    assert manager.segments[0].allow is False


def test_segment_manager_toggle_allow_invalid_id(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    with pytest.raises(ValueError, match="Segment not found"):
        manager.toggle_allow("999")


def test_segment_manager_set_allow(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    manager.set_allow("0", True)
    assert manager.segments[0].allow is True
    
    manager.set_allow("0", False)
    assert manager.segments[0].allow is False


def test_segment_manager_set_allow_invalid_id(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    with pytest.raises(ValueError, match="Segment not found"):
        manager.set_allow("999", True)


def test_segment_manager_save_to_json(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    manager.toggle_allow("0")
    manager.toggle_allow("1")
    
    manager.save_to_json()
    manager.flush_sync()  # Ensure immediate write (async queue is debounced)
    
    with open(temp_json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data['segments'][0]['allow'] is True
    assert data['segments'][1]['allow'] is True


def test_segment_manager_save_to_json_no_file_loaded():
    manager = SegmentManager()
    
    with pytest.raises(ValueError, match="No file loaded"):
        manager.save_to_json()


def test_segment_manager_get_segments_by_label(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    profanity_segments = manager.get_segments_by_label("Profanity")
    assert len(profanity_segments) == 2
    
    violence_segments = manager.get_segments_by_label("Violence")
    assert len(violence_segments) == 1
    
    nonexistent_segments = manager.get_segments_by_label("Nonexistent")
    assert len(nonexistent_segments) == 0


def test_segment_manager_get_segments_by_allow_status(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    not_allowed = manager.get_segments_by_allow_status(False)
    assert len(not_allowed) == 2
    
    manager.toggle_allow("0")
    
    allowed = manager.get_segments_by_allow_status(True)
    assert len(allowed) == 1
    
    not_allowed = manager.get_segments_by_allow_status(False)
    assert len(not_allowed) == 1


def test_segment_manager_batch_set_allow_by_label(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    count = manager.batch_set_allow_by_label("Profanity", True)
    assert count == 2
    assert manager.segments[0].allow is True
    assert manager.segments[1].allow is True
    
    count = manager.batch_set_allow_by_label("Violence", False)
    assert count == 1
    assert manager.segments[0].allow is False


def test_segment_manager_atomic_save(temp_json_file):
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    original_mtime = os.path.getmtime(temp_json_file)
    
    import time
    time.sleep(0.01)
    
    manager.toggle_allow("0")
    manager.save_to_json()
    manager.flush_sync()  # Ensure immediate write (async queue is debounced)
    
    new_mtime = os.path.getmtime(temp_json_file)
    assert new_mtime > original_mtime
    
    with open(temp_json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert 'segments' in data
    assert 'file' in data
    assert data['segments'][0]['allow'] is True


def test_segment_reviewed_field_default():
    """Test that reviewed field defaults to False."""
    segment = Segment(
        id="0",
        start_time=0.0,
        end_time=5.0,
        duration_seconds=5.0,
        labels=["Test"],
        description="Test segment",
        confidence=0.9,
        detections=[]
    )
    assert segment.reviewed is False


def test_segment_reviewed_field_from_dict():
    """Test parsing reviewed field from dict."""
    data_with_reviewed = {
        "start_time": 10.0,
        "end_time": 15.0,
        "duration_seconds": 5.0,
        "labels": ["Test"],
        "description": "Test",
        "confidence": 0.9,
        "detections": [],
        "reviewed": True
    }
    segment = Segment.from_dict(data_with_reviewed, "0")
    assert segment.reviewed is True
    
    # Test default when not present
    data_without_reviewed = {
        "start_time": 10.0,
        "end_time": 15.0,
        "duration_seconds": 5.0,
        "labels": ["Test"],
        "description": "Test",
        "confidence": 0.9,
        "detections": []
    }
    segment2 = Segment.from_dict(data_without_reviewed, "1")
    assert segment2.reviewed is False


def test_segment_reviewed_field_to_dict():
    """Test that reviewed field is serialized to dict."""
    segment = Segment(
        id="0",
        start_time=0.0,
        end_time=5.0,
        duration_seconds=5.0,
        labels=["Test"],
        description="Test segment",
        confidence=0.9,
        detections=[],
        reviewed=True
    )
    data = segment.to_dict()
    assert 'reviewed' in data
    assert data['reviewed'] is True


def test_segment_manager_set_reviewed(temp_json_file):
    """Test setting reviewed status for a segment."""
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    assert manager.segments[0].reviewed is False
    
    manager.set_reviewed("0", True)
    assert manager.segments[0].reviewed is True
    
    manager.set_reviewed("0", False)
    assert manager.segments[0].reviewed is False


def test_segment_manager_batch_set_reviewed(temp_json_file):
    """Test batch setting reviewed status."""
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    
    count = manager.batch_set_reviewed(["0", "1"], True)
    assert count == 2
    assert manager.segments[0].reviewed is True
    assert manager.segments[1].reviewed is True


def test_async_write_queue_debouncing():
    """Test that AsyncWriteQueue debounces writes."""
    from video_censor_personal.ui.segment_manager import AsyncWriteQueue
    import time
    
    write_count = [0]
    
    def mock_write():
        write_count[0] += 1
    
    queue = AsyncWriteQueue(mock_write, debounce_seconds=0.1)
    
    # Mark dirty multiple times quickly
    queue.mark_dirty()
    queue.mark_dirty()
    queue.mark_dirty()
    
    # Should be dirty
    assert queue.is_dirty() is True
    
    # Wait for debounce
    time.sleep(0.2)
    
    # Should have only one write
    assert write_count[0] == 1
    assert queue.is_dirty() is False
    
    queue.cleanup()


def test_async_write_queue_flush_sync():
    """Test synchronous flush."""
    from video_censor_personal.ui.segment_manager import AsyncWriteQueue
    
    write_count = [0]
    
    def mock_write():
        write_count[0] += 1
    
    queue = AsyncWriteQueue(mock_write, debounce_seconds=5.0)  # Long debounce
    
    queue.mark_dirty()
    assert queue.is_dirty() is True
    
    # Flush synchronously
    result = queue.flush_sync()
    assert result is True
    assert queue.is_dirty() is False
    assert write_count[0] == 1
    
    queue.cleanup()


def test_async_write_queue_status_callback():
    """Test status callback is invoked correctly."""
    from video_censor_personal.ui.segment_manager import AsyncWriteQueue
    import time
    
    status_changes = []
    
    def mock_write():
        pass
    
    def status_callback(is_dirty):
        status_changes.append(is_dirty)
    
    queue = AsyncWriteQueue(mock_write, debounce_seconds=0.1)
    queue.set_status_callback(status_callback)
    
    queue.mark_dirty()
    assert True in status_changes
    
    time.sleep(0.2)
    assert False in status_changes
    
    queue.cleanup()
