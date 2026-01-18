from typing import Callable, Dict, Optional
import tkinter as tk


class KeyboardShortcutHandler:
    """Handles keyboard shortcuts for the preview editor."""
    
    SHORTCUTS = {
        '<space>': 'play_pause',
        '<Left>': 'seek_back',
        '<Right>': 'seek_forward',
        '<Up>': 'previous_segment',
        '<Down>': 'next_segment',
        'a': 'toggle_allow',
        'A': 'toggle_allow',
        '<Return>': 'jump_to_segment',
        '<KP_Enter>': 'jump_to_segment',
        '<Prior>': 'page_up',
        '<Next>': 'page_down',
    }
    
    def __init__(self, root_widget: tk.Widget):
        """Initialize keyboard shortcut handler.
        
        Args:
            root_widget: Root widget to bind shortcuts to
        """
        self.root_widget = root_widget
        self.actions: Dict[str, Callable[[], None]] = {}
        self._setup_bindings()
    
    def _setup_bindings(self) -> None:
        """Setup keyboard bindings."""
        for key, action in self.SHORTCUTS.items():
            self.root_widget.bind(key, lambda event, a=action: self._handle_key(event, a))
    
    def _handle_key(self, event, action: str) -> str:
        """Handle keyboard event.
        
        Args:
            event: Keyboard event
            action: Action name
            
        Returns:
            "break" to prevent event propagation
        """
        if action in self.actions:
            self.actions[action]()
        return "break"
    
    def register_action(self, action: str, callback: Callable[[], None]) -> None:
        """Register a callback for an action.
        
        Args:
            action: Action name (e.g., 'play_pause', 'seek_back')
            callback: Callback function with no arguments
        """
        self.actions[action] = callback
    
    def unregister_action(self, action: str) -> None:
        """Unregister a callback for an action.
        
        Args:
            action: Action name
        """
        if action in self.actions:
            del self.actions[action]
    
    @staticmethod
    def get_help_text() -> str:
        """Get help text describing all keyboard shortcuts."""
        return """Keyboard Shortcuts:
        
Space       - Play/Pause video
← (Left)    - Seek back 5 seconds
→ (Right)   - Seek forward 5 seconds
↑ (Up)      - Previous segment
↓ (Down)    - Next segment
A           - Toggle allow status on selected segment
Enter       - Jump to selected segment start time
Page Up     - Previous page of segments
Page Down   - Next page of segments
"""


class KeyboardShortcutManager:
    """Manages keyboard shortcuts with action delegation."""
    
    def __init__(self):
        self.handler: Optional[KeyboardShortcutHandler] = None
        self.play_pause_callback: Optional[Callable[[], None]] = None
        self.seek_back_callback: Optional[Callable[[], None]] = None
        self.seek_forward_callback: Optional[Callable[[], None]] = None
        self.previous_segment_callback: Optional[Callable[[], None]] = None
        self.next_segment_callback: Optional[Callable[[], None]] = None
        self.toggle_allow_callback: Optional[Callable[[], None]] = None
        self.jump_to_segment_callback: Optional[Callable[[], None]] = None
        self.page_up_callback: Optional[Callable[[], None]] = None
        self.page_down_callback: Optional[Callable[[], None]] = None
    
    def initialize(self, root_widget: tk.Widget) -> None:
        """Initialize keyboard shortcuts.
        
        Args:
            root_widget: Root widget to bind shortcuts to
        """
        self.handler = KeyboardShortcutHandler(root_widget)
        self._register_all_actions()
    
    def _register_all_actions(self) -> None:
        """Register all action callbacks."""
        if self.handler is None:
            return
        
        self.handler.register_action('play_pause', self._on_play_pause)
        self.handler.register_action('seek_back', self._on_seek_back)
        self.handler.register_action('seek_forward', self._on_seek_forward)
        self.handler.register_action('previous_segment', self._on_previous_segment)
        self.handler.register_action('next_segment', self._on_next_segment)
        self.handler.register_action('toggle_allow', self._on_toggle_allow)
        self.handler.register_action('jump_to_segment', self._on_jump_to_segment)
        self.handler.register_action('page_up', self._on_page_up)
        self.handler.register_action('page_down', self._on_page_down)
    
    def _on_play_pause(self) -> None:
        """Handle play/pause action."""
        if self.play_pause_callback:
            self.play_pause_callback()
    
    def _on_seek_back(self) -> None:
        """Handle seek back action."""
        if self.seek_back_callback:
            self.seek_back_callback()
    
    def _on_seek_forward(self) -> None:
        """Handle seek forward action."""
        if self.seek_forward_callback:
            self.seek_forward_callback()
    
    def _on_previous_segment(self) -> None:
        """Handle previous segment action."""
        if self.previous_segment_callback:
            self.previous_segment_callback()
    
    def _on_next_segment(self) -> None:
        """Handle next segment action."""
        if self.next_segment_callback:
            self.next_segment_callback()
    
    def _on_toggle_allow(self) -> None:
        """Handle toggle allow action."""
        if self.toggle_allow_callback:
            self.toggle_allow_callback()
    
    def _on_jump_to_segment(self) -> None:
        """Handle jump to segment action."""
        if self.jump_to_segment_callback:
            self.jump_to_segment_callback()
    
    def _on_page_up(self) -> None:
        """Handle page up action."""
        if self.page_up_callback:
            self.page_up_callback()
    
    def _on_page_down(self) -> None:
        """Handle page down action."""
        if self.page_down_callback:
            self.page_down_callback()
    
    def set_play_pause_callback(self, callback: Callable[[], None]) -> None:
        """Set play/pause callback."""
        self.play_pause_callback = callback
    
    def set_seek_back_callback(self, callback: Callable[[], None]) -> None:
        """Set seek back callback."""
        self.seek_back_callback = callback
    
    def set_seek_forward_callback(self, callback: Callable[[], None]) -> None:
        """Set seek forward callback."""
        self.seek_forward_callback = callback
    
    def set_previous_segment_callback(self, callback: Callable[[], None]) -> None:
        """Set previous segment callback."""
        self.previous_segment_callback = callback
    
    def set_next_segment_callback(self, callback: Callable[[], None]) -> None:
        """Set next segment callback."""
        self.next_segment_callback = callback
    
    def set_toggle_allow_callback(self, callback: Callable[[], None]) -> None:
        """Set toggle allow callback."""
        self.toggle_allow_callback = callback
    
    def set_jump_to_segment_callback(self, callback: Callable[[], None]) -> None:
        """Set jump to segment callback."""
        self.jump_to_segment_callback = callback
    
    def set_page_up_callback(self, callback: Callable[[], None]) -> None:
        """Set page up callback."""
        self.page_up_callback = callback
    
    def set_page_down_callback(self, callback: Callable[[], None]) -> None:
        """Set page down callback."""
        self.page_down_callback = callback
