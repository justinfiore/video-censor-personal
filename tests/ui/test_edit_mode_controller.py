"""Tests for EditModeController."""

import pytest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from video_censor_personal.ui.segment_manager import Segment, SegmentManager, Detection
from video_censor_personal.ui.edit_mode_controller import EditModeController, EditState


@pytest.fixture
def sample_segment():
    """Create a sample segment for testing."""
    return Segment(
        id="test-segment-1",
        start_time=10.0,
        end_time=20.0,
        duration_seconds=10.0,
        labels=["Violence", "Profanity"],
        description="Test segment",
        confidence=0.9,
        detections=[
            Detection(label="Violence", confidence=0.9, reasoning="Test")
        ],
        allow=False,
        reviewed=False
    )


@pytest.fixture
def sample_json_data():
    return {
        "file": "/path/to/video.mp4",
        "segments": [
            {
                "start_time": 10.0,
                "end_time": 20.0,
                "duration_seconds": 10.0,
                "labels": ["Violence", "Profanity"],
                "description": "Test segment",
                "confidence": 0.9,
                "detections": [
                    {"label": "Violence", "confidence": 0.9, "reasoning": "Test"}
                ],
                "allow": False
            },
            {
                "start_time": 30.0,
                "end_time": 40.0,
                "duration_seconds": 10.0,
                "labels": ["Profanity"],
                "description": "Second segment",
                "confidence": 0.8,
                "detections": [],
                "allow": False
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


@pytest.fixture
def segment_manager(temp_json_file):
    """Create a segment manager with test data."""
    manager = SegmentManager()
    manager.load_from_json(temp_json_file)
    return manager


@pytest.fixture
def controller(segment_manager):
    """Create an EditModeController with test segment manager."""
    return EditModeController(segment_manager)


class TestEditModeControllerBasics:
    """Test basic edit mode controller functionality."""
    
    def test_initial_state(self, controller):
        """Test controller starts in non-editing mode."""
        assert controller.is_editing is False
        assert controller.current_segment_id is None
        assert controller.edited_start is None
        assert controller.edited_end is None
        assert controller.edited_labels is None
    
    def test_enter_edit_mode(self, controller, sample_segment):
        """Test entering edit mode."""
        controller.enter_edit_mode(sample_segment)
        
        assert controller.is_editing is True
        assert controller.current_segment_id == "test-segment-1"
        assert controller.edited_start == 10.0
        assert controller.edited_end == 20.0
        assert controller.edited_labels == ["Violence", "Profanity"]
    
    def test_enter_edit_mode_callback(self, controller, sample_segment):
        """Test that edit mode callback is invoked."""
        callback = MagicMock()
        controller.set_on_edit_mode_changed(callback)
        
        controller.enter_edit_mode(sample_segment)
        callback.assert_called_once_with(True)
    
    def test_cancel_restores_original_values(self, controller, sample_segment):
        """Test that cancel exits edit mode without changes."""
        controller.enter_edit_mode(sample_segment)
        
        controller.update_start(5.0)
        controller.update_end(25.0)
        
        controller.cancel()
        
        assert controller.is_editing is False
        assert controller.current_segment_id is None
    
    def test_cancel_callback(self, controller, sample_segment):
        """Test that cancel invokes callback."""
        callback = MagicMock()
        controller.set_on_edit_mode_changed(callback)
        
        controller.enter_edit_mode(sample_segment)
        callback.reset_mock()
        
        controller.cancel()
        callback.assert_called_once_with(False)
    
    def test_cancel_when_not_editing(self, controller):
        """Test that cancel does nothing when not in edit mode."""
        controller.cancel()
        assert controller.is_editing is False


class TestEditModeControllerApply:
    """Test applying changes."""
    
    def test_apply_persists_changes(self, controller, segment_manager):
        """Test that apply persists changes via segment manager."""
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        controller.update_start(5.0)
        controller.update_end(15.0)
        
        result = controller.apply()
        segment_manager.flush_sync()
        
        assert result is True
        assert controller.is_editing is False
        
        updated_segment = segment_manager.get_segment_by_id("0")
        assert updated_segment.start_time == 5.0
        assert updated_segment.end_time == 15.0
    
    def test_apply_callback(self, controller, segment_manager):
        """Test that apply invokes callbacks."""
        segment = segment_manager.get_segment_by_id("0")
        
        mode_callback = MagicMock()
        update_callback = MagicMock()
        controller.set_on_edit_mode_changed(mode_callback)
        controller.set_on_segment_updated(update_callback)
        
        controller.enter_edit_mode(segment)
        mode_callback.reset_mock()
        
        controller.apply()
        
        mode_callback.assert_called_once_with(False)
        update_callback.assert_called_once_with("0")
    
    def test_apply_when_not_editing(self, controller):
        """Test that apply returns False when not in edit mode."""
        result = controller.apply()
        assert result is False


class TestEditModeControllerTimeUpdates:
    """Test time update functionality."""
    
    def test_update_start(self, controller, sample_segment):
        """Test updating start time."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.update_start(5.0)
        
        assert result is True
        assert controller.edited_start == 5.0
    
    def test_update_start_snaps_to_100ms(self, controller, sample_segment):
        """Test that start time snaps to 100ms increments."""
        controller.enter_edit_mode(sample_segment)
        
        controller.update_start(5.123)
        assert abs(controller.edited_start - 5.1) < 0.001
        
        controller.update_start(5.178)
        assert abs(controller.edited_start - 5.2) < 0.001
    
    def test_update_start_callback(self, controller, sample_segment):
        """Test that start time callback is invoked."""
        callback = MagicMock()
        controller.set_on_start_time_changed(callback)
        
        controller.enter_edit_mode(sample_segment)
        controller.update_start(5.0)
        
        callback.assert_called_with(5.0)
    
    def test_update_start_rejects_negative(self, controller, sample_segment):
        """Test that negative start times are rejected."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.update_start(-5.0)
        
        assert result is False
        assert controller.edited_start == 10.0
    
    def test_update_start_cannot_cross_end(self, controller, sample_segment):
        """Test that start cannot exceed or equal end - minimum duration."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.update_start(19.95)
        
        assert result is False
        assert controller.edited_start == 10.0
    
    def test_update_end(self, controller, sample_segment):
        """Test updating end time."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.update_end(25.0)
        
        assert result is True
        assert controller.edited_end == 25.0
    
    def test_update_end_snaps_to_100ms(self, controller, sample_segment):
        """Test that end time snaps to 100ms increments."""
        controller.enter_edit_mode(sample_segment)
        
        controller.update_end(25.123)
        assert abs(controller.edited_end - 25.1) < 0.001
        
        controller.update_end(25.178)
        assert abs(controller.edited_end - 25.2) < 0.001
    
    def test_update_end_callback(self, controller, sample_segment):
        """Test that end time callback is invoked."""
        callback = MagicMock()
        controller.set_on_end_time_changed(callback)
        
        controller.enter_edit_mode(sample_segment)
        controller.update_end(25.0)
        
        callback.assert_called_with(25.0)
    
    def test_update_end_cannot_cross_start(self, controller, sample_segment):
        """Test that end cannot be less than or equal to start + minimum duration."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.update_end(10.05)
        
        assert result is False
        assert controller.edited_end == 20.0
    
    def test_update_when_not_editing(self, controller):
        """Test updates return False when not in edit mode."""
        assert controller.update_start(5.0) is False
        assert controller.update_end(25.0) is False


class TestEditModeControllerLabels:
    """Test label editing functionality."""
    
    def test_add_label(self, controller, sample_segment):
        """Test adding a label."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.add_label("NewLabel")
        
        assert result is True
        assert "NewLabel" in controller.edited_labels
    
    def test_add_duplicate_label(self, controller, sample_segment):
        """Test that duplicate labels are rejected."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.add_label("Violence")
        
        assert result is False
        assert controller.edited_labels.count("Violence") == 1
    
    def test_add_label_callback(self, controller, sample_segment):
        """Test that labels callback is invoked on add."""
        callback = MagicMock()
        controller.set_on_labels_changed(callback)
        
        controller.enter_edit_mode(sample_segment)
        controller.add_label("NewLabel")
        
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert "NewLabel" in call_args
    
    def test_remove_label(self, controller, sample_segment):
        """Test removing a label."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.remove_label("Violence")
        
        assert result is True
        assert "Violence" not in controller.edited_labels
    
    def test_remove_nonexistent_label(self, controller, sample_segment):
        """Test that removing nonexistent label returns False."""
        controller.enter_edit_mode(sample_segment)
        
        result = controller.remove_label("NonexistentLabel")
        
        assert result is False
    
    def test_remove_label_callback(self, controller, sample_segment):
        """Test that labels callback is invoked on remove."""
        callback = MagicMock()
        controller.set_on_labels_changed(callback)
        
        controller.enter_edit_mode(sample_segment)
        controller.remove_label("Violence")
        
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert "Violence" not in call_args
    
    def test_label_operations_when_not_editing(self, controller):
        """Test label operations return False when not in edit mode."""
        assert controller.add_label("Label") is False
        assert controller.remove_label("Label") is False


class TestEditModeControllerHasChanges:
    """Test change detection."""
    
    def test_has_changes_initial(self, controller, sample_segment):
        """Test has_changes returns False initially."""
        controller.enter_edit_mode(sample_segment)
        assert controller.has_changes() is False
    
    def test_has_changes_after_start_update(self, controller, sample_segment):
        """Test has_changes returns True after start time change."""
        controller.enter_edit_mode(sample_segment)
        controller.update_start(5.0)
        assert controller.has_changes() is True
    
    def test_has_changes_after_end_update(self, controller, sample_segment):
        """Test has_changes returns True after end time change."""
        controller.enter_edit_mode(sample_segment)
        controller.update_end(25.0)
        assert controller.has_changes() is True
    
    def test_has_changes_after_label_add(self, controller, sample_segment):
        """Test has_changes returns True after adding label."""
        controller.enter_edit_mode(sample_segment)
        controller.add_label("NewLabel")
        assert controller.has_changes() is True
    
    def test_has_changes_after_label_remove(self, controller, sample_segment):
        """Test has_changes returns True after removing label."""
        controller.enter_edit_mode(sample_segment)
        controller.remove_label("Violence")
        assert controller.has_changes() is True
    
    def test_has_changes_when_not_editing(self, controller):
        """Test has_changes returns False when not in edit mode."""
        assert controller.has_changes() is False


class TestEditModeControllerZoom:
    """Test zoom range calculation."""
    
    def test_get_zoom_range(self, controller, sample_segment):
        """Test zoom range calculation."""
        controller.enter_edit_mode(sample_segment)
        
        zoom_start, zoom_end = controller.get_zoom_range(100.0)
        
        assert zoom_start == 0.0  # max(0, 10 - 30) = 0
        assert zoom_end == 50.0   # min(100, 20 + 30) = 50
    
    def test_get_zoom_range_clamped(self, controller, sample_segment):
        """Test zoom range is clamped to video duration."""
        controller.enter_edit_mode(sample_segment)
        
        zoom_start, zoom_end = controller.get_zoom_range(25.0)
        
        assert zoom_start == 0.0
        assert zoom_end == 25.0
    
    def test_get_zoom_range_when_not_editing(self, controller):
        """Test zoom range returns full video when not editing."""
        zoom_start, zoom_end = controller.get_zoom_range(100.0)
        
        assert zoom_start == 0.0
        assert zoom_end == 100.0
    
    def test_get_zoom_range_custom_buffer(self, controller, sample_segment):
        """Test zoom range with custom buffer."""
        controller.enter_edit_mode(sample_segment)
        
        zoom_start, zoom_end = controller.get_zoom_range(100.0, buffer=10.0)
        
        assert zoom_start == 0.0   # max(0, 10 - 10) = 0
        assert zoom_end == 30.0    # min(100, 20 + 10) = 30


class TestEditModeControllerEnterWhileEditing:
    """Test entering edit mode while already editing."""
    
    def test_enter_while_editing_exits_previous(self, controller, sample_segment):
        """Test that entering edit mode while editing cancels previous edit."""
        second_segment = Segment(
            id="test-segment-2",
            start_time=30.0,
            end_time=40.0,
            duration_seconds=10.0,
            labels=["Other"],
            description="Second segment",
            confidence=0.8,
            detections=[],
            allow=False,
            reviewed=False
        )
        
        controller.enter_edit_mode(sample_segment)
        controller.update_start(5.0)
        
        controller.enter_edit_mode(second_segment)
        
        assert controller.current_segment_id == "test-segment-2"
        assert controller.edited_start == 30.0
        assert controller.edited_end == 40.0
