"""Edit mode controller for segment editing state management.

This module provides the EditModeController class which manages the state machine
for segment editing in the preview editor UI. It coordinates between the video
player pane (timeline scrubbers) and the segment details pane (time inputs, labels).

State Machine:
    [View Mode] --("Edit Segment" click)--> [Edit Mode]
    [Edit Mode] --("Cancel" click)--> [View Mode] (discard changes)
    [Edit Mode] --("Apply" click)--> [View Mode] (persist changes)

Key Features:
    - Tracks original and edited segment values for cancel/apply
    - Snaps time values to 100ms increments for precision
    - Enforces minimum 100ms segment duration (scrubbers cannot cross)
    - Provides callbacks for UI component synchronization
    - Calculates timeline zoom range for focused editing

Usage Example:
    >>> from video_censor_personal.ui.edit_mode_controller import EditModeController
    >>> from video_censor_personal.ui.segment_manager import SegmentManager
    >>>
    >>> # Create controller with segment manager
    >>> manager = SegmentManager()
    >>> manager.load_from_json("detections.json")
    >>> controller = EditModeController(manager)
    >>>
    >>> # Set up callbacks for UI updates
    >>> controller.set_on_edit_mode_changed(lambda editing: print(f"Editing: {editing}"))
    >>> controller.set_on_start_time_changed(lambda t: print(f"Start: {t}"))
    >>> controller.set_on_end_time_changed(lambda t: print(f"End: {t}"))
    >>>
    >>> # Enter edit mode for a segment
    >>> segment = manager.get_segment_by_id("0")
    >>> controller.enter_edit_mode(segment)  # Triggers on_edit_mode_changed(True)
    >>>
    >>> # Update times (e.g., from scrubber drag)
    >>> controller.update_start(5.0)  # Snaps to 100ms, triggers callback
    >>> controller.update_end(15.0)
    >>>
    >>> # Check for changes before applying
    >>> if controller.has_changes():
    ...     controller.apply()  # Persists to segment manager
    >>> else:
    ...     controller.cancel()  # Discards changes
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Callable, List

from video_censor_personal.ui.segment_manager import Segment, SegmentManager

logger = logging.getLogger("video_censor_personal.ui")


@dataclass
class EditState:
    """Holds the current edit state for a segment."""
    segment_id: str
    original_start: float
    original_end: float
    original_labels: List[str]
    edited_start: float
    edited_end: float
    edited_labels: List[str]


class EditModeController:
    """Controls segment editing state and coordinates between UI components.
    
    Manages the state machine for edit mode:
    - View Mode (default): Normal segment display
    - Edit Mode: Active editing with scrubbers, time inputs, and label editing
    
    The controller maintains a copy of the original segment values to support
    Cancel functionality, and tracks edited values for Apply.
    """
    
    MINIMUM_SEGMENT_DURATION = 0.1  # 100ms minimum
    SNAP_INCREMENT = 0.1  # Snap to 100ms increments
    
    def __init__(self, segment_manager: SegmentManager):
        """Initialize the edit mode controller.
        
        Args:
            segment_manager: The segment manager for persisting changes
        """
        self._segment_manager = segment_manager
        self._edit_state: Optional[EditState] = None
        
        self._on_edit_mode_changed: Optional[Callable[[bool], None]] = None
        self._on_start_time_changed: Optional[Callable[[float], None]] = None
        self._on_end_time_changed: Optional[Callable[[float], None]] = None
        self._on_labels_changed: Optional[Callable[[List[str]], None]] = None
        self._on_segment_updated: Optional[Callable[[str], None]] = None
    
    @property
    def is_editing(self) -> bool:
        """Check if currently in edit mode."""
        return self._edit_state is not None
    
    @property
    def current_segment_id(self) -> Optional[str]:
        """Get the ID of the segment being edited."""
        return self._edit_state.segment_id if self._edit_state else None
    
    @property
    def edited_start(self) -> Optional[float]:
        """Get the current edited start time."""
        return self._edit_state.edited_start if self._edit_state else None
    
    @property
    def edited_end(self) -> Optional[float]:
        """Get the current edited end time."""
        return self._edit_state.edited_end if self._edit_state else None
    
    @property
    def edited_labels(self) -> Optional[List[str]]:
        """Get the current edited labels."""
        return self._edit_state.edited_labels.copy() if self._edit_state else None
    
    def set_on_edit_mode_changed(self, callback: Callable[[bool], None]) -> None:
        """Set callback for edit mode state changes."""
        self._on_edit_mode_changed = callback
    
    def set_on_start_time_changed(self, callback: Callable[[float], None]) -> None:
        """Set callback for start time changes."""
        callback_name = getattr(callback, '__name__', f'{type(callback).__name__}') if callback else 'None'
        logger.info(f"[CONTROLLER] set_on_start_time_changed called with callback={callback is not None}, callback_name={callback_name}")
        self._on_start_time_changed = callback
        logger.info(f"[CONTROLLER] self._on_start_time_changed is now={self._on_start_time_changed is not None}, id={id(self)}")
        logger.info(f"[CONTROLLER] Verification: self._on_start_time_changed type={type(self._on_start_time_changed)}")
    
    def set_on_end_time_changed(self, callback: Callable[[float], None]) -> None:
        """Set callback for end time changes."""
        logger.info(f"[CONTROLLER] set_on_end_time_changed called with callback={callback is not None}")
        self._on_end_time_changed = callback
        logger.info(f"[CONTROLLER] self._on_end_time_changed is now={self._on_end_time_changed is not None}")
    
    def set_on_labels_changed(self, callback: Callable[[List[str]], None]) -> None:
        """Set callback for labels changes."""
        self._on_labels_changed = callback
    
    def set_on_segment_updated(self, callback: Callable[[str], None]) -> None:
        """Set callback for when a segment is updated/created."""
        self._on_segment_updated = callback
    
    def enter_edit_mode(self, segment: Segment) -> None:
        """Enter edit mode for a segment.
        
        Args:
            segment: The segment to edit
        """
        if self._edit_state is not None:
            logger.warning("Already in edit mode, exiting previous edit first")
            self.cancel()
        
        self._edit_state = EditState(
            segment_id=segment.id,
            original_start=segment.start_time,
            original_end=segment.end_time,
            original_labels=segment.labels.copy(),
            edited_start=segment.start_time,
            edited_end=segment.end_time,
            edited_labels=segment.labels.copy()
        )
        
        logger.info(f"Entered edit mode for segment {segment.id}")
        
        if self._on_edit_mode_changed:
            self._on_edit_mode_changed(True)
    
    def cancel(self) -> None:
        """Cancel edit mode, discarding changes."""
        if self._edit_state is None:
            return
        
        segment_id = self._edit_state.segment_id
        self._edit_state = None
        
        logger.info(f"Cancelled edit mode for segment {segment_id}")
        
        if self._on_edit_mode_changed:
            self._on_edit_mode_changed(False)
    
    def apply(self) -> bool:
        """Apply changes and exit edit mode.
        
        Returns:
            True if changes were applied successfully, False otherwise
        """
        if self._edit_state is None:
            return False
        
        try:
            self._segment_manager.update_segment(
                segment_id=self._edit_state.segment_id,
                new_start_time=self._edit_state.edited_start,
                new_end_time=self._edit_state.edited_end,
                new_labels=self._edit_state.edited_labels
            )
            
            segment_id = self._edit_state.segment_id
            self._edit_state = None
            
            logger.info(f"Applied changes to segment {segment_id}")
            
            if self._on_edit_mode_changed:
                self._on_edit_mode_changed(False)
            
            if self._on_segment_updated:
                self._on_segment_updated(segment_id)
            
            return True
            
        except ValueError as e:
            logger.error(f"Failed to apply segment changes: {e}")
            return False
    
    def update_start(self, new_start: float) -> bool:
        """Update the edited start time.
        
        Args:
            new_start: New start time in seconds
            
        Returns:
            True if the update was valid and applied
        """
        logger.info(f"[CONTROLLER] update_start({new_start}) called, id={id(self)}")
        
        if self._edit_state is None:
            logger.warning(f"[CONTROLLER] update_start: No edit state")
            return False
        
        snapped_start = self._snap_to_increment(new_start)
        logger.info(f"[CONTROLLER] Snapped {new_start} -> {snapped_start}")
        
        if snapped_start < 0:
            logger.warning(f"[CONTROLLER] update_start: snapped_start < 0")
            return False
        
        if snapped_start >= self._edit_state.edited_end - self.MINIMUM_SEGMENT_DURATION:
            logger.warning(f"[CONTROLLER] update_start: snapped_start ({snapped_start}) >= edited_end ({self._edit_state.edited_end}) - min_duration ({self.MINIMUM_SEGMENT_DURATION})")
            return False
        
        self._edit_state.edited_start = snapped_start
        logger.info(f"[CONTROLLER] Updated edited_start to {snapped_start}, has callback: {self._on_start_time_changed is not None}")
        
        if self._on_start_time_changed:
            logger.info(f"[CONTROLLER] Calling _on_start_time_changed callback, callback_type={type(self._on_start_time_changed)}")
            self._on_start_time_changed(snapped_start)
        else:
            logger.warning(f"[CONTROLLER] No _on_start_time_changed callback registered! _on_start_time_changed={self._on_start_time_changed}")
        
        return True
    
    def update_end(self, new_end: float) -> bool:
        """Update the edited end time.
        
        Args:
            new_end: New end time in seconds
            
        Returns:
            True if the update was valid and applied
        """
        logger.info(f"[CONTROLLER] update_end({new_end}) called")
        
        if self._edit_state is None:
            logger.warning(f"[CONTROLLER] update_end: No edit state")
            return False
        
        snapped_end = self._snap_to_increment(new_end)
        logger.info(f"[CONTROLLER] Snapped {new_end} -> {snapped_end}")
        
        if snapped_end <= self._edit_state.edited_start + self.MINIMUM_SEGMENT_DURATION:
            logger.warning(f"[CONTROLLER] update_end: snapped_end ({snapped_end}) <= edited_start ({self._edit_state.edited_start}) + min_duration ({self.MINIMUM_SEGMENT_DURATION})")
            return False
        
        self._edit_state.edited_end = snapped_end
        logger.info(f"[CONTROLLER] Updated edited_end to {snapped_end}, has callback: {self._on_end_time_changed is not None}")
        
        if self._on_end_time_changed:
            logger.info(f"[CONTROLLER] Calling _on_end_time_changed callback")
            self._on_end_time_changed(snapped_end)
        else:
            logger.warning(f"[CONTROLLER] No _on_end_time_changed callback registered!")
        
        return True
    
    def add_label(self, label: str) -> bool:
        """Add a label to the segment.
        
        Args:
            label: Label to add
            
        Returns:
            True if the label was added
        """
        if self._edit_state is None:
            return False
        
        if label in self._edit_state.edited_labels:
            return False
        
        self._edit_state.edited_labels.append(label)
        
        if self._on_labels_changed:
            self._on_labels_changed(self._edit_state.edited_labels.copy())
        
        return True
    
    def remove_label(self, label: str) -> bool:
        """Remove a label from the segment.
        
        Args:
            label: Label to remove
            
        Returns:
            True if the label was removed
        """
        if self._edit_state is None:
            return False
        
        if label not in self._edit_state.edited_labels:
            return False
        
        self._edit_state.edited_labels.remove(label)
        
        if self._on_labels_changed:
            self._on_labels_changed(self._edit_state.edited_labels.copy())
        
        return True
    
    def has_changes(self) -> bool:
        """Check if there are unsaved changes.
        
        Returns:
            True if the edited values differ from the original
        """
        if self._edit_state is None:
            return False
        
        return (
            self._edit_state.edited_start != self._edit_state.original_start or
            self._edit_state.edited_end != self._edit_state.original_end or
            self._edit_state.edited_labels != self._edit_state.original_labels
        )
    
    def _snap_to_increment(self, value: float) -> float:
        """Snap a value to the nearest increment.
        
        Args:
            value: Value to snap
            
        Returns:
            Snapped value
        """
        return round(value / self.SNAP_INCREMENT) * self.SNAP_INCREMENT
    
    def get_zoom_range(self, video_duration: float, buffer: float = 30.0) -> tuple[float, float]:
        """Get the recommended zoom range for the timeline.
        
        Args:
            video_duration: Total video duration in seconds
            buffer: Buffer time around segment (default 30s)
            
        Returns:
            Tuple of (start_time, end_time) for the visible range
        """
        if self._edit_state is None:
            logger.info(f"[CONTROLLER] get_zoom_range: No edit state, returning full duration")
            return (0.0, video_duration)
        
        zoom_start = max(0.0, self._edit_state.edited_start - buffer)
        zoom_end = min(video_duration, self._edit_state.edited_end + buffer)
        
        logger.info(f"[CONTROLLER] get_zoom_range: segment={self._edit_state.edited_start}-{self._edit_state.edited_end}, buffer={buffer}, result={zoom_start}-{zoom_end}")
        return (zoom_start, zoom_end)
