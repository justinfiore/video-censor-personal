import pytest
import json
import os
import tempfile
from unittest.mock import Mock, MagicMock, patch
from video_censor_personal.ui.segment_manager import SegmentManager


@pytest.fixture
def sample_json_with_video():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        data = {
            "file": "test_video.mp4",
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Profanity"],
                    "description": "Test segment",
                    "confidence": 0.9,
                    "detections": [
                        {
                            "label": "Profanity",
                            "confidence": 0.9,
                            "reasoning": "Test"
                        }
                    ],
                    "allow": False
                }
            ]
        }
        json.dump(data, f)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_integration_load_and_toggle(sample_json_with_video):
    """Test end-to-end: load JSON, toggle allow, verify JSON updated."""
    manager = SegmentManager()
    manager.load_from_json(sample_json_with_video)
    
    assert len(manager.segments) == 1
    assert manager.segments[0].allow is False
    
    manager.toggle_allow("0")
    assert manager.segments[0].allow is True
    
    manager.save_to_json()
    
    with open(sample_json_with_video, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data['segments'][0]['allow'] is True


def test_integration_load_json_with_missing_allow_field():
    """Test loading JSON without allow field, verify default to false."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        data = {
            "file": "test_video.mp4",
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Test"],
                    "description": "Test",
                    "confidence": 0.9,
                    "detections": []
                }
            ]
        }
        json.dump(data, f)
        temp_path = f.name
    
    try:
        manager = SegmentManager()
        manager.load_from_json(temp_path)
        
        assert manager.segments[0].allow is False
        
    finally:
        os.remove(temp_path)


def test_integration_error_missing_file():
    """Test error scenario: missing file."""
    manager = SegmentManager()
    
    with pytest.raises(FileNotFoundError):
        manager.load_from_json("/nonexistent/file.json")


def test_integration_error_invalid_json():
    """Test error scenario: invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        manager = SegmentManager()
        
        with pytest.raises(ValueError):
            manager.load_from_json(temp_path)
            
    finally:
        os.remove(temp_path)


def test_integration_batch_allow_update(sample_json_with_video):
    """Test batch update of allow status by label."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        data = {
            "file": "test_video.mp4",
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Profanity"],
                    "description": "Test 1",
                    "confidence": 0.9,
                    "detections": [],
                    "allow": False
                },
                {
                    "start_time": 30.0,
                    "end_time": 35.0,
                    "duration_seconds": 5.0,
                    "labels": ["Profanity"],
                    "description": "Test 2",
                    "confidence": 0.8,
                    "detections": [],
                    "allow": False
                },
                {
                    "start_time": 50.0,
                    "end_time": 55.0,
                    "duration_seconds": 5.0,
                    "labels": ["Violence"],
                    "description": "Test 3",
                    "confidence": 0.85,
                    "detections": [],
                    "allow": False
                }
            ]
        }
        json.dump(data, f)
        temp_path = f.name
    
    try:
        manager = SegmentManager()
        manager.load_from_json(temp_path)
        
        count = manager.batch_set_allow_by_label("Profanity", True)
        assert count == 2
        
        assert manager.segments[0].allow is True
        assert manager.segments[1].allow is True
        assert manager.segments[2].allow is False
        
        manager.save_to_json()
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['segments'][0]['allow'] is True
        assert data['segments'][1]['allow'] is True
        assert data['segments'][2]['allow'] is False
        
    finally:
        os.remove(temp_path)


def test_integration_large_segment_list():
    """Test performance with large segment list (50+ segments)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        segments = []
        for i in range(100):
            segments.append({
                "start_time": i * 10.0,
                "end_time": (i * 10.0) + 5.0,
                "duration_seconds": 5.0,
                "labels": [f"Label{i % 3}"],
                "description": f"Segment {i}",
                "confidence": 0.9,
                "detections": [],
                "allow": False
            })
        
        data = {
            "file": "test_video.mp4",
            "segments": segments
        }
        json.dump(data, f)
        temp_path = f.name
    
    try:
        manager = SegmentManager()
        manager.load_from_json(temp_path)
        
        assert len(manager.segments) == 100
        
        for i in range(0, 100, 2):
            manager.toggle_allow(str(i))
        
        manager.save_to_json()
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i in range(100):
            expected_allow = (i % 2 == 0)
            assert data['segments'][i]['allow'] == expected_allow
            
    finally:
        os.remove(temp_path)


def test_integration_preserve_external_fields():
    """Test that saving preserves fields not modified by UI."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        data = {
            "file": "test_video.mp4",
            "custom_field": "custom_value",
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Test"],
                    "description": "Test",
                    "confidence": 0.9,
                    "detections": [],
                    "allow": False
                }
            ]
        }
        json.dump(data, f)
        temp_path = f.name
    
    try:
        manager = SegmentManager()
        manager.load_from_json(temp_path)
        
        manager.toggle_allow("0")
        manager.save_to_json()
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['custom_field'] == "custom_value"
        assert data['file'] == "test_video.mp4"
        assert data['segments'][0]['allow'] is True
        
    finally:
        os.remove(temp_path)
