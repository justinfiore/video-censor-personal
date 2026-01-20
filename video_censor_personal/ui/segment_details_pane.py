import customtkinter as ctk
import re
from typing import Optional, Callable, List, Set, TYPE_CHECKING
from video_censor_personal.ui.segment_manager import Segment

if TYPE_CHECKING:
    from video_censor_personal.ui.edit_mode_controller import EditModeController
    from video_censor_personal.ui.segment_manager import SegmentManager


class SegmentDetailsPaneImpl(ctk.CTkFrame):
    """Enhanced segment details pane with full functionality."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.current_segment: Optional[Segment] = None
        self.allow_toggle_callback: Optional[Callable[[str, bool], None]] = None
        self.reviewed_toggle_callback: Optional[Callable[[str, bool], None]] = None
        self.edit_segment_callback: Optional[Callable[[Segment], None]] = None
        self.duplicate_segment_callback: Optional[Callable[[str], None]] = None
        self.delete_segment_callback: Optional[Callable[[str], None]] = None
        self.edit_mode_controller: Optional["EditModeController"] = None
        self.segment_manager: Optional["SegmentManager"] = None
        self._is_edit_mode: bool = False
        self._label_chip_buttons: List[ctk.CTkButton] = []
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="Segment Details",
            font=("Arial", 14, "bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.no_selection_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="No segment selected",
            text_color="gray",
            font=("Arial", 12)
        )
        self.no_selection_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)
        
        self.details_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.details_container.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.details_container.grid_columnconfigure(1, weight=1)
        self.details_container.grid_remove()
        
        row = 0
        
        ctk.CTkLabel(
            self.details_container,
            text="Time Range:",
            font=("Arial", 11, "bold")
        ).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.time_label = ctk.CTkLabel(
            self.details_container,
            text="",
            font=("Arial", 11)
        )
        self.time_label.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        ctk.CTkLabel(
            self.details_container,
            text="Duration:",
            font=("Arial", 11, "bold")
        ).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.duration_label = ctk.CTkLabel(
            self.details_container,
            text="",
            font=("Arial", 11)
        )
        self.duration_label.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        ctk.CTkLabel(
            self.details_container,
            text="Labels:",
            font=("Arial", 11, "bold")
        ).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.labels_label = ctk.CTkLabel(
            self.details_container,
            text="",
            font=("Arial", 11)
        )
        self.labels_label.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        ctk.CTkLabel(
            self.details_container,
            text="Confidence:",
            font=("Arial", 11, "bold")
        ).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.confidence_label = ctk.CTkLabel(
            self.details_container,
            text="",
            font=("Arial", 11)
        )
        self.confidence_label.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        ctk.CTkLabel(
            self.details_container,
            text="Description:",
            font=("Arial", 11, "bold")
        ).grid(row=row, column=0, sticky="nw", padx=10, pady=5)
        self.description_label = ctk.CTkLabel(
            self.details_container,
            text="",
            font=("Arial", 11),
            wraplength=400,
            justify="left"
        )
        self.description_label.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        checkbox_frame = ctk.CTkFrame(self.details_container, fg_color="transparent")
        checkbox_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=15)
        
        self.allow_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="Allow this segment",
            font=("Arial", 12, "bold"),
            command=self._on_allow_toggled
        )
        self.allow_checkbox.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        self.reviewed_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="Reviewed",
            font=("Arial", 12, "bold"),
            command=self._on_reviewed_toggled
        )
        self.reviewed_checkbox.grid(row=0, column=1, sticky="w")
        row += 1
        
        self.save_status_label = ctk.CTkLabel(
            self.details_container,
            text="",
            font=("Arial", 10),
            text_color="green"
        )
        self.save_status_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))
        row += 1
        
        self.action_buttons_frame = ctk.CTkFrame(self.details_container, fg_color="transparent")
        self.action_buttons_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.action_buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.edit_segment_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="✏️ Edit",
            width=80,
            command=self._on_edit_segment_clicked
        )
        self.edit_segment_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.duplicate_segment_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="📋 Duplicate",
            width=80,
            command=self._on_duplicate_segment_clicked
        )
        self.duplicate_segment_button.grid(row=0, column=1, padx=2, pady=2)
        
        self.delete_segment_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="🗑️ Delete",
            width=80,
            fg_color="#8B0000",
            hover_color="#A52A2A",
            command=self._on_delete_segment_clicked
        )
        self.delete_segment_button.grid(row=0, column=2, padx=2, pady=2)
        row += 1
        
        self._create_edit_mode_ui(row)
        row += 1
        
        self.expand_button = ctk.CTkButton(
            self.details_container,
            text="Show Detections ▼",
            command=self._toggle_detections,
            fg_color="transparent",
            border_width=1,
            hover_color="#2a2d2e"
        )
        self.expand_button.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        row += 1
        
        self.detections_frame = ctk.CTkFrame(self.details_container)
        self.detections_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.detections_frame.grid_columnconfigure(0, weight=1)
        self.detections_frame.grid_remove()
        
        self.detections_expanded = False
    
    def set_allow_toggle_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Set callback for allow toggle events."""
        self.allow_toggle_callback = callback
    
    def set_reviewed_toggle_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Set callback for reviewed toggle events."""
        self.reviewed_toggle_callback = callback
    
    def display_segment(self, segment: Segment) -> None:
        """Display segment details."""
        self.current_segment = segment
        
        self.no_selection_label.grid_remove()
        self.details_container.grid()
        
        time_str = f"{self._format_time(segment.start_time)} - {self._format_time(segment.end_time)}"
        self.time_label.configure(text=time_str)
        
        duration_str = f"{segment.duration_seconds:.2f}s"
        self.duration_label.configure(text=duration_str)
        
        labels_str = ", ".join(segment.labels) if segment.labels else "None"
        self.labels_label.configure(text=labels_str)
        
        confidence_str = f"{segment.confidence * 100:.1f}%"
        self.confidence_label.configure(text=confidence_str)
        
        self.description_label.configure(text=segment.description or "No description")
        
        if segment.allow:
            self.allow_checkbox.select()
        else:
            self.allow_checkbox.deselect()
        
        if segment.reviewed:
            self.reviewed_checkbox.select()
        else:
            self.reviewed_checkbox.deselect()
        
        self._update_detections_display()
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS.mmm."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _on_allow_toggled(self) -> None:
        """Handle allow checkbox toggle."""
        if self.current_segment is None:
            return
        
        new_allow_state = self.allow_checkbox.get() == 1
        
        self.allow_checkbox.configure(state="disabled")
        
        if self.allow_toggle_callback:
            try:
                self.allow_toggle_callback(self.current_segment.id, new_allow_state)
                
                self.save_status_label.configure(text="✓ Saved", text_color="green")
                self.after(2000, lambda: self.save_status_label.configure(text=""))
                
            except Exception as e:
                self.save_status_label.configure(
                    text=f"✗ Error: {str(e)}",
                    text_color="red"
                )
                
                if new_allow_state:
                    self.allow_checkbox.deselect()
                else:
                    self.allow_checkbox.select()
        
        self.allow_checkbox.configure(state="normal")
    
    def _on_reviewed_toggled(self) -> None:
        """Handle reviewed checkbox toggle."""
        if self.current_segment is None:
            return
        
        new_reviewed_state = self.reviewed_checkbox.get() == 1
        
        self.reviewed_checkbox.configure(state="disabled")
        
        if self.reviewed_toggle_callback:
            try:
                self.reviewed_toggle_callback(self.current_segment.id, new_reviewed_state)
            except Exception as e:
                self.save_status_label.configure(
                    text=f"✗ Error: {str(e)}",
                    text_color="red"
                )
                
                if new_reviewed_state:
                    self.reviewed_checkbox.deselect()
                else:
                    self.reviewed_checkbox.select()
        
        self.reviewed_checkbox.configure(state="normal")
    
    def _toggle_detections(self) -> None:
        """Toggle detections section visibility."""
        if self.detections_expanded:
            self.detections_frame.grid_remove()
            self.expand_button.configure(text="Show Detections ▼")
            self.detections_expanded = False
        else:
            self.detections_frame.grid()
            self.expand_button.configure(text="Hide Detections ▲")
            self.detections_expanded = True
    
    def _update_detections_display(self) -> None:
        """Update detections display."""
        for widget in self.detections_frame.winfo_children():
            widget.destroy()
        
        if self.current_segment is None or not self.current_segment.detections:
            no_detections_label = ctk.CTkLabel(
                self.detections_frame,
                text="No detections",
                text_color="gray"
            )
            no_detections_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
            return
        
        for idx, detection in enumerate(self.current_segment.detections):
            detection_frame = ctk.CTkFrame(self.detections_frame)
            detection_frame.grid(row=idx, column=0, sticky="ew", padx=5, pady=5)
            detection_frame.grid_columnconfigure(1, weight=1)
            
            label_text = f"• {detection.label}"
            ctk.CTkLabel(
                detection_frame,
                text=label_text,
                font=("Arial", 11, "bold")
            ).grid(row=0, column=0, sticky="w", padx=10, pady=(5, 2))
            
            confidence_text = f"{detection.confidence * 100:.1f}%"
            ctk.CTkLabel(
                detection_frame,
                text=confidence_text,
                font=("Arial", 10),
                text_color="gray"
            ).grid(row=0, column=1, sticky="e", padx=10, pady=(5, 2))
            
            reasoning_text = detection.reasoning or "No reasoning provided"
            ctk.CTkLabel(
                detection_frame,
                text=reasoning_text,
                font=("Arial", 10),
                wraplength=400,
                justify="left"
            ).grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(2, 5))
    
    def clear(self) -> None:
        """Clear segment details."""
        self.current_segment = None
        self.details_container.grid_remove()
        self.no_selection_label.grid()
        self.save_status_label.configure(text="")
        
        if self.detections_expanded:
            self._toggle_detections()
    
    def update_allow_status(self, allow: bool) -> None:
        """Update allow checkbox without triggering callback."""
        if allow:
            self.allow_checkbox.select()
        else:
            self.allow_checkbox.deselect()
    
    def update_reviewed_status(self, reviewed: bool) -> None:
        """Update reviewed checkbox without triggering callback."""
        if reviewed:
            self.reviewed_checkbox.select()
        else:
            self.reviewed_checkbox.deselect()
    
    def _create_edit_mode_ui(self, row: int) -> None:
        """Create the edit mode UI elements."""
        self.edit_mode_container = ctk.CTkFrame(
            self.details_container,
            fg_color=("#e8f4e8", "#1a3a1a"),
            border_width=2,
            border_color=("#4caf50", "#2d5f2d")
        )
        self.edit_mode_container.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        self.edit_mode_container.grid_columnconfigure(1, weight=1)
        self.edit_mode_container.grid_remove()
        
        ctk.CTkLabel(
            self.edit_mode_container,
            text="✏️ Editing Segment",
            font=("Arial", 12, "bold"),
            text_color=("#2d5f2d", "#4caf50")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            self.edit_mode_container,
            text="Start Time:",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.start_time_entry = ctk.CTkEntry(
            self.edit_mode_container,
            width=120,
            placeholder_text="MM:SS.mmm"
        )
        self.start_time_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        self.start_time_entry.bind("<KeyRelease>", self._on_start_time_entry_changed)
        
        ctk.CTkLabel(
            self.edit_mode_container,
            text="End Time:",
            font=("Arial", 11, "bold")
        ).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        self.end_time_entry = ctk.CTkEntry(
            self.edit_mode_container,
            width=120,
            placeholder_text="MM:SS.mmm"
        )
        self.end_time_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        self.end_time_entry.bind("<KeyRelease>", self._on_end_time_entry_changed)
        
        self.time_validation_label = ctk.CTkLabel(
            self.edit_mode_container,
            text="",
            font=("Arial", 10),
            text_color="red"
        )
        self.time_validation_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(
            self.edit_mode_container,
            text="Labels:",
            font=("Arial", 11, "bold")
        ).grid(row=4, column=0, sticky="nw", padx=10, pady=5)
        
        self.labels_edit_frame = ctk.CTkFrame(self.edit_mode_container, fg_color="transparent")
        self.labels_edit_frame.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        
        self.label_chips_frame = ctk.CTkFrame(self.labels_edit_frame, fg_color="transparent")
        self.label_chips_frame.pack(fill="x", expand=True, pady=(0, 5))
        
        self.add_label_button = ctk.CTkButton(
            self.labels_edit_frame,
            text="+ Add Label",
            width=100,
            height=28,
            fg_color="transparent",
            border_width=1,
            hover_color="#2a2d2e",
            command=self._show_add_label_menu
        )
        self.add_label_button.pack(anchor="w")
        
        edit_buttons_frame = ctk.CTkFrame(self.edit_mode_container, fg_color="transparent")
        edit_buttons_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        edit_buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.cancel_edit_button = ctk.CTkButton(
            edit_buttons_frame,
            text="Cancel",
            width=100,
            fg_color="gray",
            hover_color="#555555",
            command=self._on_cancel_edit
        )
        self.cancel_edit_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.apply_edit_button = ctk.CTkButton(
            edit_buttons_frame,
            text="Apply",
            width=100,
            fg_color="#2d5f2d",
            hover_color="#4caf50",
            command=self._on_apply_edit
        )
        self.apply_edit_button.grid(row=0, column=1, padx=5, pady=5)
    
    def set_edit_mode_controller(self, controller: "EditModeController") -> None:
        """Set the edit mode controller reference."""
        self.edit_mode_controller = controller
        
        controller.set_on_start_time_changed(self._update_start_time_display)
        controller.set_on_end_time_changed(self._update_end_time_display)
        controller.set_on_labels_changed(self._update_labels_display)
    
    def set_segment_manager(self, manager: "SegmentManager") -> None:
        """Set the segment manager reference for getting known labels."""
        self.segment_manager = manager
    
    def set_edit_segment_callback(self, callback: Callable[[Segment], None]) -> None:
        """Set callback for edit segment button."""
        self.edit_segment_callback = callback
    
    def set_duplicate_segment_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for duplicate segment button."""
        self.duplicate_segment_callback = callback
    
    def set_delete_segment_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for delete segment button."""
        self.delete_segment_callback = callback
    
    def _on_edit_segment_clicked(self) -> None:
        """Handle edit segment button click."""
        if self.current_segment and self.edit_segment_callback:
            self.edit_segment_callback(self.current_segment)
    
    def _on_duplicate_segment_clicked(self) -> None:
        """Handle duplicate segment button click."""
        if self.current_segment and self.duplicate_segment_callback:
            self.duplicate_segment_callback(self.current_segment.id)
    
    def _on_delete_segment_clicked(self) -> None:
        """Handle delete segment button click."""
        if self.current_segment is None:
            return
        
        from tkinter import messagebox
        result = messagebox.askyesno(
            "Delete Segment",
            "Delete this segment? This cannot be undone.",
            icon="warning"
        )
        
        if result and self.delete_segment_callback:
            self.delete_segment_callback(self.current_segment.id)
    
    def set_edit_mode(self, is_editing: bool) -> None:
        """Set edit mode state and update UI accordingly."""
        self._is_edit_mode = is_editing
        
        if is_editing:
            self.action_buttons_frame.grid_remove()
            self.edit_mode_container.grid()
            
            if self.edit_mode_controller:
                start = self.edit_mode_controller.edited_start
                end = self.edit_mode_controller.edited_end
                labels = self.edit_mode_controller.edited_labels
                if start is not None:
                    self._update_start_time_display(start)
                if end is not None:
                    self._update_end_time_display(end)
                if labels is not None:
                    self._update_labels_display(labels)
        else:
            self.edit_mode_container.grid_remove()
            self.action_buttons_frame.grid()
            self.time_validation_label.configure(text="")
            
            for btn in self._label_chip_buttons:
                btn.destroy()
            self._label_chip_buttons.clear()
    
    def _update_start_time_display(self, time_seconds: float) -> None:
        """Update start time entry from controller."""
        self.start_time_entry.delete(0, "end")
        self.start_time_entry.insert(0, self._format_time_short(time_seconds))
    
    def _update_end_time_display(self, time_seconds: float) -> None:
        """Update end time entry from controller."""
        self.end_time_entry.delete(0, "end")
        self.end_time_entry.insert(0, self._format_time_short(time_seconds))
    
    def _format_time_short(self, seconds: float) -> str:
        """Format seconds as MM:SS.mmm for input fields."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _parse_time_input(self, time_str: str) -> Optional[float]:
        """Parse time input string to seconds.
        
        Accepts formats: MM:SS.mmm, MM:SS, SS.mmm, SS
        """
        time_str = time_str.strip()
        
        patterns = [
            (r'^(\d+):(\d+)\.(\d+)$', lambda m: int(m.group(1)) * 60 + int(m.group(2)) + int(m.group(3)) / 1000),
            (r'^(\d+):(\d+)$', lambda m: int(m.group(1)) * 60 + int(m.group(2))),
            (r'^(\d+)\.(\d+)$', lambda m: int(m.group(1)) + int(m.group(2)) / 1000),
            (r'^(\d+)$', lambda m: float(m.group(1))),
        ]
        
        for pattern, converter in patterns:
            match = re.match(pattern, time_str)
            if match:
                try:
                    return converter(match)
                except (ValueError, ZeroDivisionError):
                    return None
        
        return None
    
    def _on_start_time_entry_changed(self, event=None) -> None:
        """Handle start time entry change."""
        if not self.edit_mode_controller or not self._is_edit_mode:
            return
        
        time_str = self.start_time_entry.get()
        parsed = self._parse_time_input(time_str)
        
        if parsed is None:
            self.start_time_entry.configure(border_color="red")
            self.time_validation_label.configure(text="Invalid start time format")
            return
        
        if self.edit_mode_controller.update_start(parsed):
            self.start_time_entry.configure(border_color="gray")
            self.time_validation_label.configure(text="")
        else:
            self.start_time_entry.configure(border_color="red")
            self.time_validation_label.configure(text="Start must be before end")
    
    def _on_end_time_entry_changed(self, event=None) -> None:
        """Handle end time entry change."""
        if not self.edit_mode_controller or not self._is_edit_mode:
            return
        
        time_str = self.end_time_entry.get()
        parsed = self._parse_time_input(time_str)
        
        if parsed is None:
            self.end_time_entry.configure(border_color="red")
            self.time_validation_label.configure(text="Invalid end time format")
            return
        
        if self.edit_mode_controller.update_end(parsed):
            self.end_time_entry.configure(border_color="gray")
            self.time_validation_label.configure(text="")
        else:
            self.end_time_entry.configure(border_color="red")
            self.time_validation_label.configure(text="End must be after start")
    
    def _on_cancel_edit(self) -> None:
        """Handle cancel edit button."""
        if self.edit_mode_controller:
            self.edit_mode_controller.cancel()
    
    def _on_apply_edit(self) -> None:
        """Handle apply edit button."""
        if self.edit_mode_controller:
            if not self.edit_mode_controller.apply():
                self.time_validation_label.configure(text="Failed to apply changes")
    
    def _update_labels_display(self, labels: List[str]) -> None:
        """Update label chips display from controller."""
        for btn in self._label_chip_buttons:
            btn.destroy()
        self._label_chip_buttons.clear()
        
        for label in labels:
            chip = self._create_label_chip(label)
            chip.pack(side="left", padx=(0, 5), pady=2)
            self._label_chip_buttons.append(chip)
    
    def _create_label_chip(self, label: str) -> ctk.CTkButton:
        """Create a removable label chip button."""
        chip = ctk.CTkButton(
            self.label_chips_frame,
            text=f"{label} ×",
            width=0,
            height=24,
            fg_color=("#3a7ebf", "#1f538d"),
            hover_color=("#8B0000", "#A52A2A"),
            corner_radius=12,
            font=("Arial", 10),
            command=lambda l=label: self._on_remove_label(l)
        )
        return chip
    
    def _on_remove_label(self, label: str) -> None:
        """Handle label chip removal."""
        if self.edit_mode_controller:
            self.edit_mode_controller.remove_label(label)
    
    def _get_known_labels(self) -> Set[str]:
        """Get all known labels from all segments."""
        known_labels: Set[str] = set()
        if self.segment_manager:
            for segment in self.segment_manager.get_all_segments():
                known_labels.update(segment.labels)
        return known_labels
    
    def _get_available_labels(self) -> List[str]:
        """Get labels that can be added (known labels not currently on segment)."""
        known = self._get_known_labels()
        current = set()
        if self.edit_mode_controller and self.edit_mode_controller.edited_labels:
            current = set(self.edit_mode_controller.edited_labels)
        
        available = sorted(known - current)
        return available
    
    def _show_add_label_menu(self) -> None:
        """Show dropdown menu for adding labels."""
        import tkinter as tk
        
        available = self._get_available_labels()
        
        menu = tk.Menu(self, tearoff=0)
        
        if available:
            for label in available:
                menu.add_command(
                    label=label,
                    command=lambda l=label: self._on_add_label(l)
                )
        else:
            menu.add_command(label="(No additional labels available)", state="disabled")
        
        menu.add_separator()
        menu.add_command(label="New label...", command=self._show_new_label_dialog)
        
        try:
            x = self.add_label_button.winfo_rootx()
            y = self.add_label_button.winfo_rooty() + self.add_label_button.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
    
    def _on_add_label(self, label: str) -> None:
        """Handle adding a label."""
        if self.edit_mode_controller:
            self.edit_mode_controller.add_label(label)
    
    def _show_new_label_dialog(self) -> None:
        """Show dialog for entering a new custom label."""
        dialog = ctk.CTkInputDialog(
            text="Enter new label name:",
            title="Add New Label"
        )
        new_label = dialog.get_input()
        
        if new_label and new_label.strip():
            self._on_add_label(new_label.strip())
