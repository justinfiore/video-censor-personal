import pytest
from unittest.mock import Mock, MagicMock, patch
import tkinter as tk


def test_keyboard_shortcut_handler_initialization():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutHandler
    
    mock_widget = Mock(spec=tk.Widget)
    handler = KeyboardShortcutHandler(mock_widget)
    
    assert handler.root_widget == mock_widget
    assert len(handler.actions) == 0
    assert mock_widget.bind.called


def test_keyboard_shortcut_handler_register_action():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutHandler
    
    mock_widget = Mock(spec=tk.Widget)
    handler = KeyboardShortcutHandler(mock_widget)
    
    callback = Mock()
    handler.register_action('play_pause', callback)
    
    assert 'play_pause' in handler.actions
    assert handler.actions['play_pause'] == callback


def test_keyboard_shortcut_handler_unregister_action():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutHandler
    
    mock_widget = Mock(spec=tk.Widget)
    handler = KeyboardShortcutHandler(mock_widget)
    
    callback = Mock()
    handler.register_action('play_pause', callback)
    handler.unregister_action('play_pause')
    
    assert 'play_pause' not in handler.actions


def test_keyboard_shortcut_handler_handle_key():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutHandler
    
    mock_widget = Mock(spec=tk.Widget)
    handler = KeyboardShortcutHandler(mock_widget)
    
    callback = Mock()
    handler.register_action('play_pause', callback)
    
    event = Mock()
    result = handler._handle_key(event, 'play_pause')
    
    callback.assert_called_once()
    assert result == "break"


def test_keyboard_shortcut_handler_handle_unregistered_action():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutHandler
    
    mock_widget = Mock(spec=tk.Widget)
    handler = KeyboardShortcutHandler(mock_widget)
    
    event = Mock()
    result = handler._handle_key(event, 'nonexistent_action')
    
    assert result == "break"


def test_keyboard_shortcut_handler_get_help_text():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutHandler
    
    help_text = KeyboardShortcutHandler.get_help_text()
    
    assert "Space" in help_text
    assert "Play/Pause" in help_text
    assert "←" in help_text or "Left" in help_text
    assert "→" in help_text or "Right" in help_text
    assert "↑" in help_text or "Up" in help_text
    assert "↓" in help_text or "Down" in help_text
    assert "A" in help_text
    assert "Enter" in help_text


def test_keyboard_shortcut_manager_initialization():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutManager
    
    manager = KeyboardShortcutManager()
    
    assert manager.handler is None
    assert manager.play_pause_callback is None


def test_keyboard_shortcut_manager_initialize():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutManager
    
    mock_widget = Mock(spec=tk.Widget)
    manager = KeyboardShortcutManager()
    
    manager.initialize(mock_widget)
    
    assert manager.handler is not None
    assert manager.handler.root_widget == mock_widget


def test_keyboard_shortcut_manager_set_callbacks():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutManager
    
    manager = KeyboardShortcutManager()
    
    play_pause_cb = Mock()
    seek_back_cb = Mock()
    seek_forward_cb = Mock()
    prev_seg_cb = Mock()
    next_seg_cb = Mock()
    toggle_allow_cb = Mock()
    jump_to_seg_cb = Mock()
    
    manager.set_play_pause_callback(play_pause_cb)
    manager.set_seek_back_callback(seek_back_cb)
    manager.set_seek_forward_callback(seek_forward_cb)
    manager.set_previous_segment_callback(prev_seg_cb)
    manager.set_next_segment_callback(next_seg_cb)
    manager.set_toggle_allow_callback(toggle_allow_cb)
    manager.set_jump_to_segment_callback(jump_to_seg_cb)
    
    assert manager.play_pause_callback == play_pause_cb
    assert manager.seek_back_callback == seek_back_cb
    assert manager.seek_forward_callback == seek_forward_cb
    assert manager.previous_segment_callback == prev_seg_cb
    assert manager.next_segment_callback == next_seg_cb
    assert manager.toggle_allow_callback == toggle_allow_cb
    assert manager.jump_to_segment_callback == jump_to_seg_cb


def test_keyboard_shortcut_manager_actions():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutManager
    
    manager = KeyboardShortcutManager()
    
    play_pause_cb = Mock()
    seek_back_cb = Mock()
    seek_forward_cb = Mock()
    prev_seg_cb = Mock()
    next_seg_cb = Mock()
    toggle_allow_cb = Mock()
    jump_to_seg_cb = Mock()
    
    manager.set_play_pause_callback(play_pause_cb)
    manager.set_seek_back_callback(seek_back_cb)
    manager.set_seek_forward_callback(seek_forward_cb)
    manager.set_previous_segment_callback(prev_seg_cb)
    manager.set_next_segment_callback(next_seg_cb)
    manager.set_toggle_allow_callback(toggle_allow_cb)
    manager.set_jump_to_segment_callback(jump_to_seg_cb)
    
    manager._on_play_pause()
    play_pause_cb.assert_called_once()
    
    manager._on_seek_back()
    seek_back_cb.assert_called_once()
    
    manager._on_seek_forward()
    seek_forward_cb.assert_called_once()
    
    manager._on_previous_segment()
    prev_seg_cb.assert_called_once()
    
    manager._on_next_segment()
    next_seg_cb.assert_called_once()
    
    manager._on_toggle_allow()
    toggle_allow_cb.assert_called_once()
    
    manager._on_jump_to_segment()
    jump_to_seg_cb.assert_called_once()


def test_keyboard_shortcut_manager_actions_without_callbacks():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutManager
    
    manager = KeyboardShortcutManager()
    
    manager._on_play_pause()
    manager._on_seek_back()
    manager._on_seek_forward()
    manager._on_previous_segment()
    manager._on_next_segment()
    manager._on_toggle_allow()
    manager._on_jump_to_segment()


def test_keyboard_shortcut_handler_shortcuts_mapping():
    from video_censor_personal.ui.keyboard_shortcuts import KeyboardShortcutHandler
    
    shortcuts = KeyboardShortcutHandler.SHORTCUTS
    
    assert '<space>' in shortcuts
    assert shortcuts['<space>'] == 'play_pause'
    
    assert '<Left>' in shortcuts
    assert shortcuts['<Left>'] == 'seek_back'
    
    assert '<Right>' in shortcuts
    assert shortcuts['<Right>'] == 'seek_forward'
    
    assert '<Up>' in shortcuts
    assert shortcuts['<Up>'] == 'previous_segment'
    
    assert '<Down>' in shortcuts
    assert shortcuts['<Down>'] == 'next_segment'
    
    assert 'a' in shortcuts or 'A' in shortcuts
    assert '<Return>' in shortcuts
