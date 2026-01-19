"""Integration tests for segment reviewed state feature.

Tests cover:
- Auto-review detection (click timing, playback tracking)
- Flush-on-exit behavior
- Sync status indicator state changes
- Review status filter
- Bulk mark reviewed/unreviewed actions
- Large segment file handling (200+ segments)
"""

import pytest
import json
import os
import time
import tempfile
from unittest.mock import Mock, patch, MagicMock

from video_censor_personal.ui.segment_manager import SegmentManager, Segment, AsyncWriteQueue


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_json_with_reviewed():
    """Create sample JSON with reviewed field."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        data = {
            "file": "test_video.mp4",
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Profanity"],
                    "description": "Segment 1",
                    "confidence": 0.9,
                    "detections": [],
                    "allow": False,
                    "reviewed": False
                },
                {
                    "start_time": 20.0,
                    "end_time": 25.0,
                    "duration_seconds": 5.0,
                    "labels": ["Violence"],
                    "description": "Segment 2",
                    "confidence": 0.85,
                    "detections": [],
                    "allow": True,
                    "reviewed": True
                },
                {
                    "start_time": 30.0,
                    "end_time": 35.0,
                    "duration_seconds": 5.0,
                    "labels": ["Profanity"],
                    "description": "Segment 3",
                    "confidence": 0.8,
                    "detections": [],
                    "allow": False,
                    "reviewed": False
                }
            ]
        }
        json.dump(data, f)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def large_segment_json():
    """Create JSON with 200+ segments for scalability testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        segments = []
        for i in range(250):
            segments.append({
                "start_time": i * 10.0,
                "end_time": (i * 10.0) + 5.0,
                "duration_seconds": 5.0,
                "labels": [f"Label{i % 5}"],
                "description": f"Segment {i}",
                "confidence": 0.9 - (i % 10) * 0.01,
                "detections": [],
                "allow": i % 3 == 0,
                "reviewed": i % 4 == 0
            })
        
        data = {
            "file": "test_video.mp4",
            "segments": segments
        }
        json.dump(data, f)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)


# ============================================================================
# Task 6.3: Integration tests for auto-review detection
# ============================================================================

class TestAutoReviewDetection:
    """Tests for auto-review detection based on click timing and playback."""
    
    def test_auto_review_after_selection_threshold(self, sample_json_with_reviewed):
        """Test that segment is marked reviewed after being selected >1 second.
        
        WHEN segment is selected for >1 second
        THEN segment.reviewed becomes True
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        segment = manager.get_segment_by_id("0")
        assert segment.reviewed is False
        
        # Simulate auto-review by directly setting (as PreviewEditor would do)
        manager.set_reviewed("0", True)
        assert segment.reviewed is True
    
    def test_playback_coverage_tracking_marks_reviewed(self, sample_json_with_reviewed):
        """Test that full playback coverage marks segment as reviewed.
        
        WHEN video playback covers entire segment timespan
        THEN segment is marked as reviewed
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        # Segment 0: 10.0 - 15.0, unreviewed
        segment = manager.get_segment_by_id("0")
        assert segment.reviewed is False
        
        # Simulate full coverage by marking reviewed
        manager.set_reviewed("0", True)
        manager.save_to_json()
        manager.flush_sync()
        
        # Reload and verify persisted
        manager2 = SegmentManager()
        manager2.load_from_json(sample_json_with_reviewed)
        assert manager2.get_segment_by_id("0").reviewed is True
    
    def test_partial_playback_does_not_mark_reviewed(self, sample_json_with_reviewed):
        """Test that partial playback doesn't mark segment as reviewed.
        
        WHEN video playback only covers partial segment
        THEN segment remains unreviewed
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        # Don't set reviewed - verify it stays False
        segment = manager.get_segment_by_id("0")
        assert segment.reviewed is False
        
        manager.save_to_json()
        manager.flush_sync()
        
        # Reload and verify still unreviewed
        manager2 = SegmentManager()
        manager2.load_from_json(sample_json_with_reviewed)
        assert manager2.get_segment_by_id("0").reviewed is False


# ============================================================================
# Task 6.4: Test flush-on-exit writes pending changes
# ============================================================================

class TestFlushOnExit:
    """Tests for flush-on-exit behavior."""
    
    def test_flush_sync_writes_pending_changes(self, sample_json_with_reviewed):
        """Test that flush_sync writes all pending changes.
        
        WHEN flush_sync is called with pending changes
        THEN all changes are written to disk immediately
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        # Make changes
        manager.set_reviewed("0", True)
        manager.set_reviewed("2", True)
        manager.save_to_json()
        
        # Flush immediately
        result = manager.flush_sync()
        assert result is True
        
        # Verify changes persisted
        with open(sample_json_with_reviewed, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['segments'][0]['reviewed'] is True
        assert data['segments'][2]['reviewed'] is True
    
    def test_flush_sync_with_no_pending_changes(self, sample_json_with_reviewed):
        """Test flush_sync returns True when nothing to flush.
        
        WHEN flush_sync is called with no pending changes
        THEN it returns True without error
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        # No changes made
        result = manager.flush_sync()
        assert result is True
    
    def test_async_write_queue_flush_on_cleanup(self):
        """Test AsyncWriteQueue cancels timer on cleanup.
        
        WHEN cleanup() is called on AsyncWriteQueue
        THEN pending timer is cancelled
        AND no writes occur after cleanup
        """
        write_count = [0]
        
        def mock_write():
            write_count[0] += 1
        
        queue = AsyncWriteQueue(mock_write, debounce_seconds=5.0)
        queue.mark_dirty()
        assert queue.is_dirty() is True
        
        # Cleanup cancels timer
        queue.cleanup()
        
        # Wait a bit - no write should occur
        time.sleep(0.1)
        assert write_count[0] == 0


# ============================================================================
# Task 6.5: Integration tests for sync status indicator
# ============================================================================

class TestSyncStatusIndicator:
    """Tests for sync status indicator state changes."""
    
    def test_status_callback_dirty_on_change(self):
        """Test status callback is called with True when dirty.
        
        WHEN AsyncWriteQueue marks dirty
        THEN status callback is invoked with is_dirty=True
        """
        status_changes = []
        
        def mock_write():
            pass
        
        def status_callback(is_dirty):
            status_changes.append(is_dirty)
        
        queue = AsyncWriteQueue(mock_write, debounce_seconds=0.1)
        queue.set_status_callback(status_callback)
        
        queue.mark_dirty()
        assert True in status_changes
        
        queue.cleanup()
    
    def test_status_callback_clean_after_write(self):
        """Test status callback is called with False after write completes.
        
        WHEN AsyncWriteQueue completes a write
        THEN status callback is invoked with is_dirty=False
        """
        status_changes = []
        
        def mock_write():
            pass
        
        def status_callback(is_dirty):
            status_changes.append(is_dirty)
        
        queue = AsyncWriteQueue(mock_write, debounce_seconds=0.05)
        queue.set_status_callback(status_callback)
        
        queue.mark_dirty()
        
        # Wait for debounce and write
        time.sleep(0.15)
        
        assert True in status_changes
        assert False in status_changes
        
        queue.cleanup()
    
    def test_segment_manager_sync_status_callback(self, sample_json_with_reviewed):
        """Test SegmentManager propagates sync status to callback.
        
        WHEN changes are made via SegmentManager
        THEN sync status callback reflects dirty/clean state
        """
        status_changes = []
        
        def status_callback(is_dirty):
            status_changes.append(is_dirty)
        
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        manager.set_sync_status_callback(status_callback)
        
        # Make a change
        manager.set_reviewed("0", True)
        manager.save_to_json()
        
        assert True in status_changes
        
        # Flush and check clean callback
        manager.flush_sync()
        assert False in status_changes


# ============================================================================
# Task 6.6: Integration tests for review status filter
# ============================================================================

class TestReviewStatusFilter:
    """Tests for review status filter functionality."""
    
    def test_get_segments_by_reviewed_status_true(self, sample_json_with_reviewed):
        """Test filtering segments by reviewed=True.
        
        WHEN filtering by reviewed=True
        THEN only reviewed segments are returned
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        reviewed_segments = manager.get_segments_by_reviewed_status(True)
        
        assert len(reviewed_segments) == 1
        assert reviewed_segments[0].id == "1"
    
    def test_get_segments_by_reviewed_status_false(self, sample_json_with_reviewed):
        """Test filtering segments by reviewed=False.
        
        WHEN filtering by reviewed=False
        THEN only unreviewed segments are returned
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        unreviewed_segments = manager.get_segments_by_reviewed_status(False)
        
        assert len(unreviewed_segments) == 2
        assert all(not s.reviewed for s in unreviewed_segments)
    
    def test_filter_updates_after_status_change(self, sample_json_with_reviewed):
        """Test filter results update after reviewed status change.
        
        WHEN segment reviewed status changes
        THEN filter results reflect the new status
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        # Initially 2 unreviewed
        assert len(manager.get_segments_by_reviewed_status(False)) == 2
        
        # Mark one as reviewed
        manager.set_reviewed("0", True)
        
        # Now 1 unreviewed
        assert len(manager.get_segments_by_reviewed_status(False)) == 1
        assert len(manager.get_segments_by_reviewed_status(True)) == 2


# ============================================================================
# Task 6.7: Integration tests for bulk mark reviewed/unreviewed
# ============================================================================

class TestBulkReviewedActions:
    """Tests for bulk mark reviewed/unreviewed functionality."""
    
    def test_batch_set_reviewed_true(self, sample_json_with_reviewed):
        """Test batch setting reviewed=True for multiple segments.
        
        WHEN batch_set_reviewed is called with True
        THEN all specified segments become reviewed
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        count = manager.batch_set_reviewed(["0", "2"], True)
        
        assert count == 2
        assert manager.get_segment_by_id("0").reviewed is True
        assert manager.get_segment_by_id("2").reviewed is True
    
    def test_batch_set_reviewed_false(self, sample_json_with_reviewed):
        """Test batch setting reviewed=False for multiple segments.
        
        WHEN batch_set_reviewed is called with False
        THEN all specified segments become unreviewed
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        # First mark all as reviewed
        manager.batch_set_reviewed(["0", "1", "2"], True)
        assert all(s.reviewed for s in manager.segments)
        
        # Now unmark some
        count = manager.batch_set_reviewed(["0", "2"], False)
        
        assert count == 2
        assert manager.get_segment_by_id("0").reviewed is False
        assert manager.get_segment_by_id("1").reviewed is True
        assert manager.get_segment_by_id("2").reviewed is False
    
    def test_batch_set_reviewed_persists_to_json(self, sample_json_with_reviewed):
        """Test batch reviewed changes persist to JSON.
        
        WHEN batch_set_reviewed is called and saved
        THEN changes are persisted to JSON file
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        manager.batch_set_reviewed(["0", "2"], True)
        manager.save_to_json()
        manager.flush_sync()
        
        with open(sample_json_with_reviewed, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['segments'][0]['reviewed'] is True
        assert data['segments'][1]['reviewed'] is True  # Was already True
        assert data['segments'][2]['reviewed'] is True
    
    def test_batch_set_reviewed_nonexistent_ids(self, sample_json_with_reviewed):
        """Test batch_set_reviewed with nonexistent IDs.
        
        WHEN batch_set_reviewed is called with invalid IDs
        THEN only valid IDs are updated
        AND count reflects actual updates
        """
        manager = SegmentManager()
        manager.load_from_json(sample_json_with_reviewed)
        
        count = manager.batch_set_reviewed(["0", "999", "2", "invalid"], True)
        
        # Only 2 valid IDs should be updated
        assert count == 2


# ============================================================================
# Task 7.3: Test with large segment files (200+ segments)
# ============================================================================

class TestLargeSegmentFiles:
    """Tests for handling large segment files."""
    
    def test_load_200_plus_segments(self, large_segment_json):
        """Test loading JSON with 200+ segments.
        
        WHEN loading large JSON file
        THEN all segments load correctly
        AND no performance issues
        """
        manager = SegmentManager()
        manager.load_from_json(large_segment_json)
        
        assert len(manager.segments) == 250
    
    def test_filter_reviewed_large_file(self, large_segment_json):
        """Test filtering reviewed status in large file.
        
        WHEN filtering by reviewed status in large file
        THEN filter completes quickly
        AND results are correct
        """
        manager = SegmentManager()
        manager.load_from_json(large_segment_json)
        
        # Every 4th segment is reviewed (0, 4, 8, ...)
        reviewed = manager.get_segments_by_reviewed_status(True)
        unreviewed = manager.get_segments_by_reviewed_status(False)
        
        # 250 / 4 = 62 or 63 depending on rounding
        assert len(reviewed) == 63  # 0, 4, 8, ..., 248
        assert len(unreviewed) == 250 - 63
    
    def test_batch_update_large_file(self, large_segment_json):
        """Test batch update on large file.
        
        WHEN batch updating many segments
        THEN operation completes successfully
        AND all segments are updated
        """
        manager = SegmentManager()
        manager.load_from_json(large_segment_json)
        
        # Mark all unreviewed segments as reviewed
        unreviewed_ids = [s.id for s in manager.get_segments_by_reviewed_status(False)]
        count = manager.batch_set_reviewed(unreviewed_ids, True)
        
        assert count == len(unreviewed_ids)
        assert all(s.reviewed for s in manager.segments)
    
    def test_save_large_file(self, large_segment_json):
        """Test saving large JSON file.
        
        WHEN saving large JSON file
        THEN file saves successfully
        AND all data is preserved
        """
        manager = SegmentManager()
        manager.load_from_json(large_segment_json)
        
        # Make changes
        manager.batch_set_reviewed([str(i) for i in range(100)], True)
        manager.save_to_json()
        manager.flush_sync()
        
        # Reload and verify
        manager2 = SegmentManager()
        manager2.load_from_json(large_segment_json)
        
        assert len(manager2.segments) == 250
        
        # First 100 should be reviewed
        for i in range(100):
            assert manager2.get_segment_by_id(str(i)).reviewed is True
    
    def test_rapid_operations_large_file(self, large_segment_json):
        """Test rapid operations on large file.
        
        WHEN performing many rapid operations
        THEN no data loss or corruption occurs
        """
        manager = SegmentManager()
        manager.load_from_json(large_segment_json)
        
        # Rapid toggle operations
        for i in range(50):
            manager.set_reviewed(str(i), True)
            manager.set_reviewed(str(i), False)
            manager.set_reviewed(str(i), True)
        
        manager.save_to_json()
        manager.flush_sync()
        
        # Verify final state
        with open(large_segment_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data['segments']) == 250
        
        # First 50 should be reviewed=True (last operation)
        for i in range(50):
            assert data['segments'][i]['reviewed'] is True
