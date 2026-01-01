"""Preview editor application for reviewing and editing detection segments."""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List
import os
import json
import logging
from pathlib import Path

from video_censor_personal.ui.segment_manager import SegmentManager
from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl
from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutManager


# Setup logging
def _setup_ui_logging() -> None:
    """Configure logging for the UI."""
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
        logger.setLevel(logging.DEBUG)
    
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
        logger.info(f"Initializing PreviewEditorApp with json_file={json_file}")
        
        self.root = ctk.CTk()
        self.root.title(title)
        
        self.segment_manager = SegmentManager()
        self.keyboard_manager = KeyboardShortcutManager()
        
        self.current_json_path: Optional[str] = None
        self.current_video_path: Optional[str] = None
        self.recent_files: List[str] = self._load_recent_files()
        self.auto_load_json: Optional[str] = json_file
        
        self._setup_window()
        self._create_menu()
        self._create_layout()
        self._connect_signals()
        self._setup_keyboard_shortcuts()
        
        # Auto-load JSON file if provided
        if self.auto_load_json:
            logger.info(f"Scheduling auto-load of JSON file: {self.auto_load_json}")
            self.root.after(100, self._auto_load_json)
        else:
            logger.info("No JSON file specified for auto-load")
    
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
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="No file loaded",
            text_color=("gray20", "gray80"),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
    
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
    
    def _connect_signals(self) -> None:
        """Connect signals between components."""
        self.segment_list_pane.set_segment_click_callback(self._on_segment_selected)
        
        self.segment_details_pane.set_allow_toggle_callback(self._on_allow_toggled)
        
        self.video_player_pane.set_time_update_callback(self._on_time_update)
    
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
            self.segment_manager.load_from_json(json_path)
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
                    self.segment_list_pane.load_segments(segments)
                    if segments:
                        self.segment_list_pane._on_segment_clicked(segments[0].id)
                    self._add_recent_file(json_path)
                    return
            
            # Load video
            segments = self.segment_manager.get_all_segments()
            self.video_player_pane.load_video(video_path, segments)
            self.current_video_path = video_path
            
            segments = self.segment_manager.get_all_segments()
            self.segment_list_pane.load_segments(segments)
            
            if segments:
                self.segment_list_pane._on_segment_clicked(segments[0].id)
            
            self._update_status_bar(
                json_path=json_path,
                video_path=video_path,
                output_video_path=self.segment_manager.output_video_file
            )
            self._add_recent_file(json_path)
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load file: {str(e)}"
            )
    
    def _on_segment_selected(self, segment_id: str) -> None:
        """Handle segment selection."""
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
    
    def _on_time_update(self, current_time: float) -> None:
        """Handle video time update."""
        self.segment_list_pane.highlight_segment_at_time(current_time)
    
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
            self.video_player_pane.cleanup()
            if self.root.winfo_exists():
                self.root.destroy()
        except Exception:
            pass
    
    def run(self) -> None:
        """Start the application event loop."""
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
