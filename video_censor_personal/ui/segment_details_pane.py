import customtkinter as ctk
from typing import Optional, Callable
from video_censor_personal.ui.segment_manager import Segment


class SegmentDetailsPaneImpl(ctk.CTkFrame):
    """Enhanced segment details pane with full functionality."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.current_segment: Optional[Segment] = None
        self.allow_toggle_callback: Optional[Callable[[str, bool], None]] = None
        self.reviewed_toggle_callback: Optional[Callable[[str, bool], None]] = None
        
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
