"""Preview editor application for reviewing and editing detection segments."""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Set
import os
import json
import logging
from pathlib import Path
import time
import signal
import atexit

from video_censor_personal.ui.segment_manager import SegmentManager
from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl
from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutManager
from video_censor_personal.ui.performance_profiler import PerformanceProfiler
from video_censor_personal.ui.edit_mode_controller import EditModeController


# Setup logging
def _setup_ui_logging() -> None:
    """Configure logging for the UI.
    
    Log Level Strategy:
    -------------------
    - INFO: General application flow (file loaded, operations started)
    - DEBUG (Default): Phase-level and operation-level timing measurements
      Example: "[PROFILE] Segment list: 20 widgets created in 0.05s"
    - TRACE (Level 5): Frame-by-frame and widget-by-widget details
      Enabled with: export VIDEO_CENSOR_LOG_LEVEL=TRACE
    
    Default is DEBUG which provides useful profiling without excessive verbosity.
    Use TRACE only for deep troubleshooting of performance issues.
    """
    # Get the workspace root (parent of video_censor_personal package)
    workspace_root = Path(__file__).parent.parent.parent
    log_dir = workspace_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "ui.log"
    
    logger = logging.getLogger("video_censor_personal.ui")
    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Support log level configuration via environment variable
        log_level_env = os.getenv("VIDEO_CENSOR_LOG_LEVEL", "DEBUG").upper()
        if log_level_env == "TRACE":
            # TRACE is level 5 (below DEBUG which is 10)
            logging.addLevelName(5, "TRACE")
            logger.setLevel(5)
        else:
            log_level = getattr(logging, log_level_env, logging.DEBUG)
            logger.setLevel(log_level)
    
    return logger


logger = _setup_ui_logging()


class PreviewEditorApp:
    """Preview editor application for reviewing detection segments."""
    
    MAX_RECENT_FILES = 10
    RECENT_FILES_KEY = "recent_json_files"
    
    def __init__(self, title: str = "Video Censor Personal - Preview Editor", json_file: Optional[str] = None):
        """Initialize preview editor application.
        
        Args:
            title: Window title
            json_file: Optional path to JSON file to load on startup
        """
        # Initialize performance profiler
        self.profiler = PerformanceProfiler()
        self.profiler.start_phase("App Initialization")
        
        logger.info(f"Initializing PreviewEditorApp with json_file={json_file}")
        
        self.root = ctk.CTk()
        self.root.title(title)
        
        self.segment_manager = SegmentManager()
        self.keyboard_manager = KeyboardShortcutManager()
        self.edit_mode_controller = EditModeController(self.segment_manager)
        
        self.current_json_path: Optional[str] = None
        self.current_video_path: Optional[str] = None
        self.recent_files: List[str] = self._load_recent_files()
        self.auto_load_json: Optional[str] = json_file
        
        # Auto-review tracking
        self._selected_segment_id: Optional[str] = None
        self._selection_time: Optional[float] = None
        self._AUTO_REVIEW_THRESHOLD = 1.0  # seconds
        
        # Playback-based auto-review tracking
        self._playback_covered_times: Set[float] = set()  # Track covered time positions
        self._last_playback_time: Optional[float] = None
        
        # Sync status polling (thread-safe flag for background thread communication)
        self._pending_sync_status: Optional[bool] = None
        
        # Signal handling for graceful shutdown
        self._setup_signal_handlers()
        
        self._setup_window()
        self._create_menu()
        self._create_layout()
        self._connect_signals()
        self._setup_keyboard_shortcuts()
        
        self.profiler.end_phase("App Initialization")
        
        # Auto-load JSON file if provided
        if self.auto_load_json:
            logger.info(f"Scheduling auto-load of JSON file: {self.auto_load_json}")
            self.root.after(100, self._auto_load_json)
        else:
            logger.info("No JSON file specified for auto-load")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received signal %s, flushing pending changes", signum)
            try:
                self.segment_manager.flush_sync()
            except Exception as e:
                logger.error("Error flushing on signal: %s", e)
            # Re-raise to allow default behavior
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)
        
        # Handle SIGINT (Ctrl+C) and SIGTERM
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except (ValueError, OSError) as e:
            # Signal handling may fail in non-main thread or on some platforms
            logger.warning("Could not set signal handlers: %s", e)
        
        # Also register atexit handler as fallback
        atexit.register(self._atexit_flush)
    
    def _atexit_flush(self) -> None:
        """Flush pending changes at exit (atexit handler)."""
        try:
            self.segment_manager.flush_sync()
        except Exception as e:
            logger.error("Error flushing on atexit: %s", e)
    
    def _setup_window(self) -> None:
        """Configure window geometry and layout."""
        window_width = 1400
        window_height = 900
        self.root.geometry(f"{window_width}x{window_height}")
        
        self._center_window()
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create status bar at the bottom
        self._create_status_bar()
    
    def _center_window(self) -> None:
        """Center the window on the primary display."""
        self.root.update_idletasks()
        
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
    
    def _create_status_bar(self) -> None:
        """Create status bar at the bottom of the window."""
        status_frame = ctk.CTkFrame(self.root, fg_color=("gray80", "gray20"))
        status_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=0)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="No file loaded",
            text_color=("gray20", "gray80"),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Sync status indicator (right side)
        self.sync_status_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        self.sync_status_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)
        
        self.sync_indicator = ctk.CTkLabel(
            self.sync_status_frame,
            text="●",
            font=("Arial", 16),
            text_color="green"
        )
        self.sync_indicator.grid(row=0, column=0, padx=(0, 5))
        
        self.sync_label = ctk.CTkLabel(
            self.sync_status_frame,
            text="Synchronized",
            text_color=("gray20", "gray80")
        )
        self.sync_label.grid(row=0, column=1)
    
    def _update_status_bar(self, json_path: Optional[str] = None, video_path: Optional[str] = None, output_video_path: Optional[str] = None) -> None:
        """Update status bar with current file paths."""
        parts = []
        
        if json_path:
            json_name = os.path.basename(json_path)
            parts.append(f"JSON: {json_name}")
        
        if video_path:
            video_name = os.path.basename(video_path)
            parts.append(f"Video: {video_name}")
        elif json_path:
            parts.append("Video: (not loaded)")
        
        if output_video_path:
            output_name = os.path.basename(output_video_path)
            parts.append(f"Output: {output_name}")
        
        if not parts:
            status_text = "No file loaded"
        else:
            status_text = "  |  ".join(parts)
        
        self.status_label.configure(text=status_text)
    
    def _update_sync_status(self, is_dirty: bool) -> None:
        """Update sync status indicator.
        
        This is called from background threads (Timer), so we use a polling
        mechanism instead of root.after() which can be unreliable from threads.
        
        Args:
            is_dirty: True if there are pending changes, False if synchronized
        """
        logger.info("_update_sync_status called with is_dirty=%s", is_dirty)
        self._pending_sync_status = is_dirty
    
    def _poll_sync_status(self) -> None:
        """Poll for sync status updates from background thread.
        
        Called periodically from the main thread to check if the sync status
        needs updating. Also checks for auto-review of current segment.
        """
        if self._pending_sync_status is not None:
            is_dirty = self._pending_sync_status
            self._pending_sync_status = None
            
            try:
                logger.debug("Applying sync status update, is_dirty=%s", is_dirty)
                if is_dirty:
                    self.sync_indicator.configure(text_color="orange")
                    self.sync_label.configure(text="Pending Changes")
                    logger.info("Sync status UI updated to 'Pending Changes' (orange)")
                else:
                    self.sync_indicator.configure(text_color="green")
                    self.sync_label.configure(text="Synchronized")
                    logger.info("Sync status UI updated to 'Synchronized' (green)")
            except Exception as e:
                logger.error("Error updating sync status UI: %s", e, exc_info=True)
        
        # Check for auto-review of current segment (while still viewing it)
        self._check_auto_review_current_segment()
        
        # Schedule next poll
        self.root.after(100, self._poll_sync_status)
    
    def _check_auto_review_current_segment(self) -> None:
        """Auto-mark current segment as reviewed if viewed for >1 second."""
        if self._selected_segment_id is None or self._selection_time is None:
            return
        
        elapsed = time.time() - self._selection_time
        if elapsed >= self._AUTO_REVIEW_THRESHOLD:
            segment = self.segment_manager.get_segment_by_id(self._selected_segment_id)
            if segment and not segment.reviewed:
                try:
                    self.segment_manager.set_reviewed(self._selected_segment_id, True)
                    self.segment_manager.save_to_json()
                    # Update UI checkbox since segment is currently displayed
                    self.segment_details_pane.update_reviewed_status(True)
                    logger.info("Auto-reviewed segment %s after %.1fs", self._selected_segment_id, elapsed)
                except Exception as e:
                    logger.error("Failed to auto-review segment: %s", e)
    
    def _track_playback_coverage(self, current_time: float) -> None:
        """Track video playback coverage and auto-mark reviewed when segment is fully covered.
        
        Args:
            current_time: Current video playback time in seconds
        """
        if self._selected_segment_id is None:
            return
        
        segment = self.segment_manager.get_segment_by_id(self._selected_segment_id)
        if segment is None or segment.reviewed:
            return
        
        # Only track times within the segment's timespan
        if segment.start_time <= current_time <= segment.end_time:
            # Round to 0.1s granularity to avoid excessive set entries
            rounded_time = round(current_time, 1)
            self._playback_covered_times.add(rounded_time)
            
            # Track continuous playback (detect seeks by large jumps)
            if self._last_playback_time is not None:
                time_diff = abs(current_time - self._last_playback_time)
                # If there's a large jump (> 1 second), user seeked - don't count as continuous
                if time_diff <= 1.0:
                    # Fill in small gaps for continuous playback
                    if self._last_playback_time < current_time:
                        t = self._last_playback_time
                        while t <= current_time:
                            if segment.start_time <= t <= segment.end_time:
                                self._playback_covered_times.add(round(t, 1))
                            t += 0.1
            
            self._last_playback_time = current_time
            
            # Check if entire segment timespan has been covered
            self._check_full_segment_coverage(segment)
    
    def _check_full_segment_coverage(self, segment) -> None:
        """Check if entire segment has been covered by playback and mark as reviewed.
        
        Args:
            segment: The segment to check coverage for
        """
        segment_duration = segment.end_time - segment.start_time
        if segment_duration <= 0:
            return
        
        # Generate expected time points (0.1s granularity)
        expected_times = set()
        t = segment.start_time
        while t <= segment.end_time:
            expected_times.add(round(t, 1))
            t += 0.1
        
        # Check if at least 90% of expected times are covered
        # (allowing for slight timing variations)
        coverage_ratio = len(self._playback_covered_times & expected_times) / len(expected_times) if expected_times else 0
        
        if coverage_ratio >= 0.9:
            try:
                self.segment_manager.set_reviewed(self._selected_segment_id, True)
                self.segment_manager.save_to_json()
                self.segment_details_pane.update_reviewed_status(True)
                logger.info("Auto-reviewed segment %s after full playback coverage (%.1f%%)", 
                           self._selected_segment_id, coverage_ratio * 100)
            except Exception as e:
                logger.error("Failed to auto-review segment on playback coverage: %s", e)
    
    def _create_menu(self) -> None:
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Video + JSON...", command=self._open_file)
        file_menu.add_separator()
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self._quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts_help)
    
    def _create_layout(self) -> None:
        """Create three-pane layout."""
        main_container = ctk.CTkFrame(self.root)
        main_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5, rowspan=1)
        
        main_container.grid_rowconfigure(0, weight=7)
        main_container.grid_rowconfigure(1, weight=3)
        main_container.grid_columnconfigure(0, weight=2)
        main_container.grid_columnconfigure(1, weight=6)
        
        self.segment_list_pane = SegmentListPaneImpl(main_container)
        self.segment_list_pane.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=2, pady=2)
        
        self.video_player_pane = VideoPlayerPaneImpl(main_container)
        self.video_player_pane.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        
        self.segment_details_pane = SegmentDetailsPaneImpl(main_container)
        self.segment_details_pane.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        
        # Connect video player to segment details pane so scrubber changes update text fields
        self.video_player_pane.set_segment_details_pane(self.segment_details_pane)
    
    def _connect_signals(self) -> None:
        """Connect signals between components."""
        self.segment_list_pane.set_segment_click_callback(self._on_segment_selected)
        self.segment_list_pane.set_bulk_reviewed_callback(self._on_bulk_reviewed)
        
        self.segment_details_pane.set_allow_toggle_callback(self._on_allow_toggled)
        self.segment_details_pane.set_reviewed_toggle_callback(self._on_reviewed_toggled)
        self.segment_details_pane.set_edit_mode_controller(self.edit_mode_controller)
        self.segment_details_pane.set_segment_manager(self.segment_manager)
        self.segment_details_pane.set_edit_segment_callback(self._on_edit_segment)
        self.segment_details_pane.set_duplicate_segment_callback(self._on_duplicate_segment)
        self.segment_details_pane.set_delete_segment_callback(self._on_delete_segment)
        
        self.video_player_pane.set_time_update_callback(self._on_time_update)
        
        self.edit_mode_controller.set_on_edit_mode_changed(self._on_edit_mode_changed)
        self.edit_mode_controller.set_on_segment_updated(self._on_segment_updated)
    
    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        self.keyboard_manager.initialize(self.root)
        
        self.keyboard_manager.set_play_pause_callback(self._on_keyboard_play_pause)
        self.keyboard_manager.set_seek_back_callback(self._on_keyboard_seek_back)
        self.keyboard_manager.set_seek_forward_callback(self._on_keyboard_seek_forward)
        self.keyboard_manager.set_previous_segment_callback(self._on_keyboard_previous_segment)
        self.keyboard_manager.set_next_segment_callback(self._on_keyboard_next_segment)
        self.keyboard_manager.set_toggle_allow_callback(self._on_keyboard_toggle_allow)
        self.keyboard_manager.set_jump_to_segment_callback(self._on_keyboard_jump_to_segment)
        self.keyboard_manager.set_page_up_callback(self._on_keyboard_page_up)
        self.keyboard_manager.set_page_down_callback(self._on_keyboard_page_down)
    
    def _auto_load_json(self) -> None:
        """Auto-load JSON file on startup."""
        logger.info("_auto_load_json called")
        
        if not self.auto_load_json:
            logger.info("No auto_load_json set, returning")
            return
        
        logger.info(f"Attempting to auto-load JSON: {self.auto_load_json}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Resolve relative paths from current working directory
        json_path = os.path.abspath(self.auto_load_json)
        logger.info(f"Resolved to absolute path: {json_path}")
        logger.info(f"Path exists: {os.path.exists(json_path)}")
        
        # If not found and path is relative, also try relative to the workspace root
        # (in case CWD was changed during launch)
        if not os.path.exists(json_path) and not os.path.isabs(self.auto_load_json):
            logger.info("Path not found, trying alternative locations")
            workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            logger.info(f"Workspace root: {workspace_root}")
            
            for base_dir in [os.getcwd(), workspace_root]:
                alt_path = os.path.join(base_dir, self.auto_load_json)
                logger.info(f"Trying: {alt_path} (exists: {os.path.exists(alt_path)})")
                if os.path.exists(alt_path):
                    json_path = os.path.abspath(alt_path)
                    logger.info(f"Found at: {json_path}")
                    break
        
        if os.path.exists(json_path):
            logger.info(f"Loading JSON file: {json_path}")
            self._load_json_file(json_path)
        else:
            logger.error(f"JSON file not found: {json_path}")
            messagebox.showerror(
                "Error",
                f"JSON file not found: {json_path}\n\nCurrent directory: {os.getcwd()}"
            )
    
    def _load_recent_files(self) -> List[str]:
        """Load recent files list from config file."""
        config_path = self._get_config_path()
        if not os.path.exists(config_path):
            return []
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                recent = config.get(self.RECENT_FILES_KEY, [])
                # Filter out files that no longer exist
                return [f for f in recent if os.path.exists(f)]
        except Exception:
            return []
    
    def _save_recent_files(self) -> None:
        """Save recent files list to config file."""
        config_path = self._get_config_path()
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        try:
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            config[self.RECENT_FILES_KEY] = self.recent_files[:self.MAX_RECENT_FILES]
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
    
    def _get_config_path(self) -> str:
        """Get path to config file."""
        config_dir = os.path.expanduser("~/.config/video-censor-personal")
        return os.path.join(config_dir, "ui_config.json")
    
    def _add_recent_file(self, json_path: str) -> None:
        """Add file to recent files list."""
        # Remove if already in list
        if json_path in self.recent_files:
            self.recent_files.remove(json_path)
        
        # Add to front
        self.recent_files.insert(0, json_path)
        
        # Trim to max
        self.recent_files = self.recent_files[:self.MAX_RECENT_FILES]
        
        self._save_recent_files()
        self._update_recent_menu()
    
    def _update_recent_menu(self) -> None:
        """Update recent files menu."""
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_files:
            self.recent_menu.add_command(label="(No recent files)", state=tk.DISABLED)
            return
        
        for json_path in self.recent_files:
            filename = os.path.basename(json_path)
            self.recent_menu.add_command(
                label=filename,
                command=lambda path=json_path: self._load_json_file(path)
            )
    
    def _open_file(self) -> None:
        """Open video and JSON file."""
        json_path = filedialog.askopenfilename(
            title="Select Detection JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not json_path:
            return
        
        self._load_json_file(json_path)
    
    def _load_json_file(self, json_path: str) -> None:
        """Load JSON file and associated video."""
        try:
            self.profiler.start_phase("JSON File Loading")
            
            # Time JSON loading
            self.profiler.start_operation("JSON parsing and segment manager load")
            self.segment_manager.load_from_json(json_path)
            self.profiler.end_operation("JSON parsing and segment manager load")
            
            # Setup sync status callback
            self.segment_manager.set_sync_status_callback(self._update_sync_status)
            
            self.current_json_path = json_path
            
            if not self.segment_manager.video_file:
                messagebox.showerror(
                    "Error",
                    "JSON file does not specify video file path."
                )
                self._update_status_bar(
                    json_path=json_path,
                    output_video_path=self.segment_manager.output_video_file
                )
                self.profiler.end_phase("JSON File Loading")
                return
            
            video_path = self.segment_manager.video_file
            if not os.path.isabs(video_path):
                json_dir = os.path.dirname(json_path)
                video_path = os.path.join(json_dir, video_path)
            
            if not os.path.exists(video_path):
                # Video file not found, allow user to browse for it
                result = messagebox.askyesno(
                    "Video Not Found",
                    f"Video file not found at: {video_path}\n\nWould you like to browse for the video file?"
                )
                
                if result:
                    # Allow user to browse for video
                    video_path = filedialog.askopenfilename(
                        title="Select Video File",
                        filetypes=[
                            ("Video files", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.webm"),
                            ("All files", "*.*")
                        ]
                    )
                    
                    if not video_path:
                        self._update_status_bar(
                            json_path=json_path,
                            output_video_path=self.segment_manager.output_video_file
                        )
                        self.profiler.end_phase("JSON File Loading")
                        return
                else:
                    messagebox.showinfo(
                        "Review-Only Mode",
                        "You can still review segments, but video playback is unavailable."
                    )
                    self._update_status_bar(
                        json_path=json_path,
                        output_video_path=self.segment_manager.output_video_file
                    )
                    segments = self.segment_manager.get_all_segments()
                    
                    # Time segment list population
                    self.profiler.start_operation("Segment list population (no video)")
                    self.segment_list_pane.load_segments(segments)
                    self.profiler.end_operation("Segment list population (no video)")
                    
                    if segments:
                        self.segment_list_pane._on_segment_clicked(segments[0].id)
                    self._add_recent_file(json_path)
                    self.profiler.end_phase("JSON File Loading")
                    return
            
            # Load video
            self.profiler.start_operation("Video player initialization")
            segments = self.segment_manager.get_all_segments()
            self.video_player_pane.load_video(video_path, segments)
            self.profiler.end_operation("Video player initialization")
            
            self.current_video_path = video_path
            
            # Time segment list population
            self.profiler.start_operation("Segment list population")
            segments = self.segment_manager.get_all_segments()
            num_segments = len(segments)
            logger.info(f"Loading {num_segments} segments")
            
            self.segment_list_pane.load_segments(segments)
            self.profiler.end_operation("Segment list population")
            
            if segments:
                self.segment_list_pane._on_segment_clicked(segments[0].id)
            
            self._update_status_bar(
                json_path=json_path,
                video_path=video_path,
                output_video_path=self.segment_manager.output_video_file
            )
            self._add_recent_file(json_path)
            
            self.profiler.end_phase("JSON File Loading")
            
            # Log performance summary
            logger.info(f"Segment count: {num_segments}")
            self.profiler.print_summary()
            
        except Exception as e:
            self.profiler.end_phase("JSON File Loading")
            messagebox.showerror(
                "Error",
                f"Failed to load file: {str(e)}"
            )
    
    def _on_segment_selected(self, segment_id: str) -> None:
        """Handle segment selection."""
        # Check if previous segment should be marked as reviewed (>1 second selection)
        # This is handled by _check_auto_review_current_segment polling, but we also
        # check here for immediate feedback when navigating away
        self._check_auto_review_current_segment()
        
        # Track new segment selection time
        self._selected_segment_id = segment_id
        self._selection_time = time.time()
        
        # Reset playback coverage tracking for new segment
        self._playback_covered_times.clear()
        self._last_playback_time = None
        
        segment = self.segment_manager.get_segment_by_id(segment_id)
        if segment:
            self.segment_details_pane.display_segment(segment)
            self.video_player_pane.seek_to_time(segment.start_time)
    
    
    def _on_allow_toggled(self, segment_id: str, allow: bool) -> None:
        """Handle allow toggle."""
        try:
            self.segment_manager.set_allow(segment_id, allow)
            self.segment_manager.save_to_json()
            
            self.segment_list_pane.update_segment_allow(segment_id, allow)
            
            segments = self.segment_manager.get_all_segments()
            self.video_player_pane.update_timeline_segments(segments)
            
        except Exception as e:
            raise IOError(f"Failed to save changes: {str(e)}")
    
    def _on_reviewed_toggled(self, segment_id: str, reviewed: bool) -> None:
        """Handle reviewed toggle."""
        try:
            self.segment_manager.set_reviewed(segment_id, reviewed)
            self.segment_manager.save_to_json()
        except Exception as e:
            raise IOError(f"Failed to save changes: {str(e)}")
    
    def _on_bulk_reviewed(self, segment_ids: List[str], reviewed: bool) -> None:
        """Handle bulk reviewed status change."""
        try:
            self.segment_manager.batch_set_reviewed(segment_ids, reviewed)
            self.segment_manager.save_to_json()
        except Exception as e:
            raise IOError(f"Failed to save changes: {str(e)}")
    
    def _on_time_update(self, current_time: float) -> None:
        """Handle video time update."""
        self.segment_list_pane.highlight_segment_at_time(current_time)
        
        # Track playback coverage for auto-review
        self._track_playback_coverage(current_time)
    
    def _on_edit_mode_changed(self, is_editing: bool) -> None:
        """Handle edit mode state changes."""
        logger.info(f"Edit mode changed: is_editing={is_editing}")
        
        if hasattr(self.segment_details_pane, 'set_edit_mode'):
            self.segment_details_pane.set_edit_mode(is_editing)
        
        if hasattr(self.video_player_pane, 'set_edit_mode'):
            self.video_player_pane.set_edit_mode(is_editing, self.edit_mode_controller)
    
    def _on_segment_updated(self, segment_id: str) -> None:
        """Handle segment update after edit mode apply."""
        segment = self.segment_manager.get_segment_by_id(segment_id)
        if segment:
            self.segment_details_pane.display_segment(segment)
            
            # Refresh segment list while preserving filters and page position
            segments = self.segment_manager.get_all_segments()
            self.segment_list_pane.refresh_segments_with_filters(segments)
            self.video_player_pane.update_timeline_segments(segments)
            
            # Exit edit mode UI (model already exited in EditModeController.apply())
            self._on_edit_mode_changed(False)
    
    def _on_edit_segment(self, segment: "Segment") -> None:
        """Handle edit segment request."""
        from video_censor_personal.ui.segment_manager import Segment
        self.edit_mode_controller.enter_edit_mode(segment)
    
    def _on_duplicate_segment(self, segment_id: str) -> None:
        """Handle duplicate segment request."""
        try:
            new_segment = self.segment_manager.duplicate_segment(segment_id)
            
            segments = self.segment_manager.get_all_segments()
            self.segment_list_pane.load_segments(segments)
            self.video_player_pane.update_timeline_segments(segments)
            
            self._on_segment_selected(new_segment.id)
            self.edit_mode_controller.enter_edit_mode(new_segment)
            
        except ValueError as e:
            logger.error(f"Failed to duplicate segment: {e}")
    
    def _on_delete_segment(self, segment_id: str) -> None:
        """Handle delete segment request."""
        try:
            next_id = self.segment_manager.delete_segment(segment_id)
            
            segments = self.segment_manager.get_all_segments()
            self.segment_list_pane.load_segments(segments)
            self.video_player_pane.update_timeline_segments(segments)
            
            if next_id:
                self._on_segment_selected(next_id)
            else:
                self.segment_details_pane.clear()
                
        except ValueError as e:
            logger.error(f"Failed to delete segment: {e}")
    
    def _on_keyboard_play_pause(self) -> None:
        """Handle play/pause keyboard shortcut."""
        self.video_player_pane.toggle_play_pause()
    
    def _on_keyboard_seek_back(self) -> None:
        """Handle seek back keyboard shortcut."""
        self.video_player_pane._skip(-5)
    
    def _on_keyboard_seek_forward(self) -> None:
        """Handle seek forward keyboard shortcut."""
        self.video_player_pane._skip(5)
    
    def _on_keyboard_previous_segment(self) -> None:
        """Handle previous segment keyboard shortcut."""
        segment_id = self.segment_list_pane.select_previous_segment()
        if segment_id:
            self._on_segment_selected(segment_id)
    
    def _on_keyboard_next_segment(self) -> None:
        """Handle next segment keyboard shortcut."""
        segment_id = self.segment_list_pane.select_next_segment()
        if segment_id:
            self._on_segment_selected(segment_id)
    
    def _on_keyboard_toggle_allow(self) -> None:
        """Handle toggle allow keyboard shortcut."""
        segment_id = self.segment_list_pane.get_selected_segment_id()
        if not segment_id:
            return
        
        segment = self.segment_manager.get_segment_by_id(segment_id)
        if segment:
            new_allow = not segment.allow
            self._on_allow_toggled(segment_id, new_allow)
            self.segment_details_pane.update_allow_status(new_allow)
    
    def _on_keyboard_jump_to_segment(self) -> None:
        """Handle jump to segment keyboard shortcut."""
        segment_id = self.segment_list_pane.get_selected_segment_id()
        if segment_id:
            self._on_segment_selected(segment_id)
    
    def _on_keyboard_page_up(self) -> None:
        """Handle page up keyboard shortcut."""
        self.segment_list_pane.handle_page_up()
    
    def _on_keyboard_page_down(self) -> None:
        """Handle page down keyboard shortcut."""
        self.segment_list_pane.handle_page_down()
    
    def _show_shortcuts_help(self) -> None:
        """Show keyboard shortcuts help dialog."""
        from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutHandler
        
        help_text = KeyboardShortcutHandler.get_help_text()
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Keyboard Shortcuts")
        dialog.geometry("400x350")
        
        text_widget = ctk.CTkTextbox(dialog, width=380, height=300)
        text_widget.pack(padx=10, pady=10)
        text_widget.insert("1.0", help_text)
        text_widget.configure(state="disabled")
        
        close_button = ctk.CTkButton(dialog, text="Close", command=dialog.destroy)
        close_button.pack(pady=(0, 10))
    
    def _quit(self) -> None:
        """Quit application."""
        self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up application resources."""
        try:
            # Flush pending changes before exit
            self.segment_manager.flush_sync()
            self.segment_manager.cleanup()
            
            self.video_player_pane.cleanup()
            if self.root.winfo_exists():
                self.root.destroy()
        except Exception:
            pass
    
    def run(self) -> None:
        """Start the application event loop."""
        # Start sync status polling
        self._poll_sync_status()
        self.root.mainloop()


def launch_preview_editor(json_file: Optional[str] = None) -> None:
    """Entry point for launching the preview editor.
    
    Args:
        json_file: Optional path to JSON file to load on startup
    """
    app = PreviewEditorApp(json_file=json_file)
    app.run()


if __name__ == "__main__":
    import sys
    json_file = sys.argv[1] if len(sys.argv) > 1 else None
    launch_preview_editor(json_file=json_file)
