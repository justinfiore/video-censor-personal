"""Integration tests for segment editing functionality.

Tests cover end-to-end workflows for:
- Edit mode workflow (enter, modify times, apply/cancel)
- Duplicate segment workflow
- Scrubber interaction (drag updates inputs, type updates scrubbers)
- Label editing (add/remove labels)

These tests validate that all components work together correctly:
EditModeController, SegmentManager, SegmentDetailsPaneImpl, and VideoPlayerPaneImpl.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from video_censor_personal.ui.segment_manager import SegmentManager, Segment, Detection
from video_censor_personal.ui.edit_mode_controller import EditModeController


@pytest.fixture
def sample_json_data():
    """Create sample JSON data with multiple segments."""
    return {
        "file": "test_video.mp4",
        "segments": [
            {
                "start_time": 10.0,
                "end_time": 20.0,
                "duration_seconds": 10.0,
                "labels": ["Violence", "Profanity"],
                "description": "First segment",
                "confidence": 0.9,
                "detections": [
                    {"label": "Violence", "confidence": 0.9, "reasoning": "Test"}
                ],
                "allow": False,
                "reviewed": False
            },
            {
                "start_time": 30.0,
                "end_time": 40.0,
                "duration_seconds": 10.0,
                "labels": ["Profanity"],
                "description": "Second segment",
                "confidence": 0.8,
                "detections": [],
                "allow": False,
                "reviewed": False
            },
            {
                "start_time": 50.0,
                "end_time": 60.0,
                "duration_seconds": 10.0,
                "labels": ["Violence"],
                "description": "Third segment",
                "confidence": 0.85,
                "detections": [],
                "allow": True,
                "reviewed": True
            }
        ]
    }


@pytest.fixture
def temp_json_file(sample_json_data):
    """Create temporary JSON file with sample data."""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8'
    ) as f:
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


class TestEditModeWorkflow:
    """Integration tests for edit mode workflow (task 6.2)."""
    
    def test_enter_edit_modify_times_and_apply(self, controller, segment_manager, temp_json_file):
        """Test complete edit workflow: enter, modify times, apply.
        
        WHEN user enters edit mode, modifies times, and applies
        THEN segment is updated with new times
        AND changes are persisted to JSON
        """
        segment = segment_manager.get_segment_by_id("0")
        original_start = segment.start_time
        original_end = segment.end_time
        
        controller.enter_edit_mode(segment)
        assert controller.is_editing is True
        assert controller.current_segment_id == "0"
        
        controller.update_start(5.0)
        controller.update_end(25.0)
        
        assert controller.edited_start == 5.0
        assert controller.edited_end == 25.0
        
        result = controller.apply()
        assert result is True
        assert controller.is_editing is False
        
        segment_manager.flush_sync()
        
        updated_segment = segment_manager.get_segment_by_id("0")
        assert updated_segment.start_time == 5.0
        assert updated_segment.end_time == 25.0
        assert updated_segment.duration_seconds == 20.0
        
        with open(temp_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['segments'][0]['start_time'] == 5.0
        assert data['segments'][0]['end_time'] == 25.0
    
    def test_enter_edit_modify_times_and_cancel(self, controller, segment_manager, temp_json_file):
        """Test edit workflow with cancel: enter, modify times, cancel.
        
        WHEN user enters edit mode, modifies times, and cancels
        THEN segment remains unchanged
        AND no changes are persisted to JSON
        """
        segment = segment_manager.get_segment_by_id("0")
        original_start = segment.start_time
        original_end = segment.end_time
        
        with open(temp_json_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        controller.enter_edit_mode(segment)
        
        controller.update_start(5.0)
        controller.update_end(25.0)
        
        assert controller.edited_start == 5.0
        assert controller.edited_end == 25.0
        
        controller.cancel()
        assert controller.is_editing is False
        
        segment = segment_manager.get_segment_by_id("0")
        assert segment.start_time == original_start
        assert segment.end_time == original_end
        
        with open(temp_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['segments'][0]['start_time'] == original_data['segments'][0]['start_time']
        assert data['segments'][0]['end_time'] == original_data['segments'][0]['end_time']
    
    def test_edit_mode_callbacks_fired_correctly(self, controller, segment_manager):
        """Test that edit mode callbacks are fired at appropriate times.
        
        WHEN user enters/exits edit mode
        THEN appropriate callbacks are invoked with correct values
        """
        segment = segment_manager.get_segment_by_id("0")
        
        mode_callback = MagicMock()
        start_callback = MagicMock()
        end_callback = MagicMock()
        update_callback = MagicMock()
        
        controller.set_on_edit_mode_changed(mode_callback)
        controller.set_on_start_time_changed(start_callback)
        controller.set_on_end_time_changed(end_callback)
        controller.set_on_segment_updated(update_callback)
        
        controller.enter_edit_mode(segment)
        mode_callback.assert_called_with(True)
        
        controller.update_start(5.0)
        start_callback.assert_called_with(5.0)
        
        controller.update_end(25.0)
        end_callback.assert_called_with(25.0)
        
        controller.apply()
        mode_callback.assert_called_with(False)
        update_callback.assert_called_with("0")
    
    def test_multiple_edits_same_segment(self, controller, segment_manager, temp_json_file):
        """Test multiple edit sessions on the same segment.
        
        WHEN user edits a segment multiple times
        THEN each edit session works correctly
        AND all changes accumulate properly
        """
        segment = segment_manager.get_segment_by_id("0")
        
        controller.enter_edit_mode(segment)
        controller.update_start(5.0)
        controller.apply()
        segment_manager.flush_sync()
        
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        controller.update_end(30.0)
        controller.apply()
        segment_manager.flush_sync()
        
        final_segment = segment_manager.get_segment_by_id("0")
        assert final_segment.start_time == 5.0
        assert final_segment.end_time == 30.0
        
        with open(temp_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['segments'][0]['start_time'] == 5.0
        assert data['segments'][0]['end_time'] == 30.0


class TestDuplicateSegmentWorkflow:
    """Integration tests for duplicate segment workflow (task 6.3)."""
    
    def test_duplicate_segment_creates_copy(self, segment_manager, temp_json_file):
        """Test duplicating a segment creates an independent copy.
        
        WHEN user duplicates a segment
        THEN new segment is created with same properties
        AND new segment has unique ID
        AND new segment is inserted after original
        """
        original_count = len(segment_manager.segments)
        original_segment = segment_manager.get_segment_by_id("0")
        
        new_segment = segment_manager.duplicate_segment("0")
        segment_manager.flush_sync()
        
        assert len(segment_manager.segments) == original_count + 1
        assert new_segment.id != original_segment.id
        assert new_segment.start_time == original_segment.start_time
        assert new_segment.end_time == original_segment.end_time
        assert new_segment.labels == original_segment.labels
        assert new_segment.description == original_segment.description
        
        original_index = segment_manager.segments.index(original_segment)
        new_index = segment_manager.segments.index(new_segment)
        assert new_index == original_index + 1
        
        with open(temp_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert len(data['segments']) == original_count + 1
    
    def test_edit_duplicated_segment_original_unchanged(self, controller, segment_manager, temp_json_file):
        """Test editing duplicated segment leaves original unchanged.
        
        WHEN user duplicates and edits the new segment
        THEN original segment is unchanged
        AND only new segment is modified
        """
        original_segment = segment_manager.get_segment_by_id("0")
        original_start = original_segment.start_time
        original_end = original_segment.end_time
        
        new_segment = segment_manager.duplicate_segment("0")
        segment_manager.flush_sync()
        
        controller.enter_edit_mode(new_segment)
        controller.update_start(original_start - 5.0)
        controller.update_end(original_end + 5.0)
        controller.apply()
        segment_manager.flush_sync()
        
        original_after = segment_manager.get_segment_by_id("0")
        assert original_after.start_time == original_start
        assert original_after.end_time == original_end
        
        edited_new = segment_manager.get_segment_by_id(new_segment.id)
        assert edited_new.start_time == original_start - 5.0
        assert edited_new.end_time == original_end + 5.0
    
    def test_duplicate_preserves_allow_but_clears_reviewed(self, segment_manager):
        """Test duplicate preserves allow status but clears reviewed.
        
        WHEN user duplicates a reviewed segment
        THEN new segment has same allow status
        AND new segment is marked as not reviewed
        """
        segment = segment_manager.get_segment_by_id("2")
        assert segment.allow is True
        assert segment.reviewed is True
        
        new_segment = segment_manager.duplicate_segment("2")
        
        assert new_segment.allow == segment.allow
        assert new_segment.reviewed is False


class TestScrubberInteraction:
    """Integration tests for scrubber interaction (task 6.4).
    
    Note: These tests verify the controller logic that would be triggered
    by scrubber drag operations. Actual UI drag events are tested in
    test_video_player_pane.py.
    """
    
    def test_scrubber_drag_updates_controller_start_time(self, controller, segment_manager):
        """Test scrubber drag updates start time with 100ms snap.
        
        WHEN user drags start scrubber to new position
        THEN controller start time is updated
        AND time is snapped to 100ms
        """
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        start_callback = MagicMock()
        controller.set_on_start_time_changed(start_callback)
        
        controller.update_start(5.123)
        
        assert abs(controller.edited_start - 5.1) < 0.001
        start_callback.assert_called_once()
        call_arg = start_callback.call_args[0][0]
        assert abs(call_arg - 5.1) < 0.001
    
    def test_scrubber_drag_updates_controller_end_time(self, controller, segment_manager):
        """Test scrubber drag updates end time with 100ms snap.
        
        WHEN user drags end scrubber to new position
        THEN controller end time is updated
        AND time is snapped to 100ms
        """
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        end_callback = MagicMock()
        controller.set_on_end_time_changed(end_callback)
        
        controller.update_end(25.789)
        
        assert abs(controller.edited_end - 25.8) < 0.001
        end_callback.assert_called_once()
        call_arg = end_callback.call_args[0][0]
        assert abs(call_arg - 25.8) < 0.001
    
    def test_scrubber_cannot_cross_minimum_duration(self, controller, segment_manager):
        """Test scrubbers enforce minimum segment duration.
        
        WHEN user drags scrubbers too close together
        THEN update is rejected
        AND minimum 100ms duration is enforced
        """
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        original_end = controller.edited_end
        
        result = controller.update_start(original_end - 0.05)
        assert result is False
        assert controller.edited_start == segment.start_time
        
        result = controller.update_end(segment.start_time + 0.05)
        assert result is False
        assert controller.edited_end == original_end
    
    def test_time_input_change_triggers_update(self, controller, segment_manager):
        """Test time input changes update controller.
        
        WHEN user types in time input field
        THEN controller is updated with parsed value
        AND scrubber position would update via callback
        """
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        start_callback = MagicMock()
        controller.set_on_start_time_changed(start_callback)
        
        result = controller.update_start(5.5)
        
        assert result is True
        assert controller.edited_start == 5.5
        start_callback.assert_called_with(5.5)
    
    def test_zoom_range_calculation(self, controller, segment_manager):
        """Test zoom range is calculated correctly for edit mode.
        
        WHEN edit mode is entered
        THEN zoom range is [start - 30s, end + 30s] clamped to video bounds
        """
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        zoom_start, zoom_end = controller.get_zoom_range(video_duration=100.0)
        
        assert zoom_start == 0.0
        assert zoom_end == 50.0


class TestLabelEditing:
    """Integration tests for label editing (task 6.5)."""
    
    def test_add_label_to_segment(self, controller, segment_manager, temp_json_file):
        """Test adding a label to a segment.
        
        WHEN user adds a label during edit mode
        THEN label is added to edited labels
        AND changes persist when applied
        """
        segment = segment_manager.get_segment_by_id("1")
        original_labels = segment.labels.copy()
        
        controller.enter_edit_mode(segment)
        
        result = controller.add_label("NewLabel")
        assert result is True
        assert "NewLabel" in controller.edited_labels
        
        controller.apply()
        segment_manager.flush_sync()
        
        updated_segment = segment_manager.get_segment_by_id("1")
        assert "NewLabel" in updated_segment.labels
        
        with open(temp_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "NewLabel" in data['segments'][1]['labels']
    
    def test_remove_label_from_segment(self, controller, segment_manager, temp_json_file):
        """Test removing a label from a segment.
        
        WHEN user removes a label during edit mode
        THEN label is removed from edited labels
        AND changes persist when applied
        """
        segment = segment_manager.get_segment_by_id("0")
        assert "Violence" in segment.labels
        
        controller.enter_edit_mode(segment)
        
        result = controller.remove_label("Violence")
        assert result is True
        assert "Violence" not in controller.edited_labels
        
        controller.apply()
        segment_manager.flush_sync()
        
        updated_segment = segment_manager.get_segment_by_id("0")
        assert "Violence" not in updated_segment.labels
        
        with open(temp_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "Violence" not in data['segments'][0]['labels']
    
    def test_label_changes_callback_fired(self, controller, segment_manager):
        """Test label changes trigger callback.
        
        WHEN user adds or removes labels
        THEN labels callback is invoked with current label list
        """
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        labels_callback = MagicMock()
        controller.set_on_labels_changed(labels_callback)
        
        controller.add_label("NewLabel")
        
        labels_callback.assert_called_once()
        call_labels = labels_callback.call_args[0][0]
        assert "NewLabel" in call_labels
        assert "Violence" in call_labels
        
        labels_callback.reset_mock()
        
        controller.remove_label("Violence")
        
        labels_callback.assert_called_once()
        call_labels = labels_callback.call_args[0][0]
        assert "Violence" not in call_labels
        assert "NewLabel" in call_labels
    
    def test_add_existing_label_rejected(self, controller, segment_manager):
        """Test adding duplicate label is rejected.
        
        WHEN user tries to add a label that already exists
        THEN add_label returns False
        AND labels list is unchanged
        """
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        original_labels = controller.edited_labels.copy()
        
        result = controller.add_label("Violence")
        
        assert result is False
        assert controller.edited_labels == original_labels
    
    def test_remove_nonexistent_label_rejected(self, controller, segment_manager):
        """Test removing nonexistent label is rejected.
        
        WHEN user tries to remove a label that doesn't exist
        THEN remove_label returns False
        AND labels list is unchanged
        """
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        original_labels = controller.edited_labels.copy()
        
        result = controller.remove_label("NonexistentLabel")
        
        assert result is False
        assert controller.edited_labels == original_labels
    
    def test_cancel_discards_label_changes(self, controller, segment_manager):
        """Test canceling edit mode discards label changes.
        
        WHEN user modifies labels then cancels
        THEN segment labels remain unchanged
        """
        segment = segment_manager.get_segment_by_id("0")
        original_labels = segment.labels.copy()
        
        controller.enter_edit_mode(segment)
        controller.add_label("TempLabel")
        controller.remove_label("Violence")
        
        controller.cancel()
        
        current_segment = segment_manager.get_segment_by_id("0")
        assert current_segment.labels == original_labels


class TestDeleteSegmentWorkflow:
    """Integration tests for delete segment workflow."""
    
    def test_delete_segment_removes_from_list(self, segment_manager, temp_json_file):
        """Test deleting a segment removes it from the list.
        
        WHEN user deletes a segment
        THEN segment is removed from segment list
        AND next segment ID is returned for auto-selection
        """
        original_count = len(segment_manager.segments)
        
        next_id = segment_manager.delete_segment("0")
        segment_manager.flush_sync()
        
        assert len(segment_manager.segments) == original_count - 1
        assert segment_manager.get_segment_by_id("0") is None
        assert next_id == "1"
        
        with open(temp_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert len(data['segments']) == original_count - 1
    
    def test_delete_last_segment_returns_previous(self, segment_manager):
        """Test deleting last segment returns previous segment ID.
        
        WHEN user deletes the last segment in list
        THEN previous segment ID is returned
        """
        last_segment_id = segment_manager.segments[-1].id
        prev_segment_id = segment_manager.segments[-2].id
        
        next_id = segment_manager.delete_segment(last_segment_id)
        
        assert next_id == prev_segment_id
    
    def test_delete_only_segment_returns_none(self):
        """Test deleting the only segment returns None.
        
        WHEN user deletes the only segment
        THEN None is returned
        """
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            data = {
                "file": "test.mp4",
                "segments": [{
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "duration_seconds": 10.0,
                    "labels": ["Test"],
                    "description": "Only segment",
                    "confidence": 0.9,
                    "detections": [],
                    "allow": False
                }]
            }
            json.dump(data, f)
            temp_path = f.name
        
        try:
            manager = SegmentManager()
            manager.load_from_json(temp_path)
            
            next_id = manager.delete_segment("0")
            
            assert next_id is None
            assert len(manager.segments) == 0
        finally:
            os.remove(temp_path)


class TestHasChangesTracking:
    """Integration tests for change tracking."""
    
    def test_has_changes_detects_start_time_change(self, controller, segment_manager):
        """Test has_changes detects start time modification."""
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        assert controller.has_changes() is False
        
        controller.update_start(5.0)
        
        assert controller.has_changes() is True
    
    def test_has_changes_detects_end_time_change(self, controller, segment_manager):
        """Test has_changes detects end time modification."""
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        assert controller.has_changes() is False
        
        controller.update_end(25.0)
        
        assert controller.has_changes() is True
    
    def test_has_changes_detects_label_change(self, controller, segment_manager):
        """Test has_changes detects label modification."""
        segment = segment_manager.get_segment_by_id("0")
        controller.enter_edit_mode(segment)
        
        assert controller.has_changes() is False
        
        controller.add_label("NewLabel")
        
        assert controller.has_changes() is True
    
    def test_has_changes_false_when_reverted(self, controller, segment_manager):
        """Test has_changes is False when changes are reverted."""
        segment = segment_manager.get_segment_by_id("0")
        original_start = segment.start_time
        controller.enter_edit_mode(segment)
        
        controller.update_start(5.0)
        assert controller.has_changes() is True
        
        controller.update_start(original_start)
        assert controller.has_changes() is False
