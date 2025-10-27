#!/usr/bin/env python3

"""
Middleware system for You-Get
Provides hooks and event system for extending functionality
"""

import time
from enum import Enum
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

__all__ = ['DownloadEvent', 'EventData', 'register_hook', 'trigger_event', 'middleware_enabled']

class DownloadEvent(Enum):
    """Download event types"""
    DOWNLOAD_START = "download_start"
    DOWNLOAD_PROGRESS = "download_progress"
    DOWNLOAD_COMPLETE = "download_complete"
    DOWNLOAD_ERROR = "download_error"
    EXTRACTION_START = "extraction_start"
    EXTRACTION_COMPLETE = "extraction_complete"
    VERIFICATION_START = "verification_start"
    VERIFICATION_COMPLETE = "verification_complete"

@dataclass
class EventData:
    """Event data container"""
    event_type: DownloadEvent
    timestamp: float
    data: Dict[str, Any]
    
    def __init__(self, event_type: DownloadEvent, data: Dict[str, Any] = None):
        self.event_type = event_type
        self.timestamp = time.time()
        self.data = data or {}

# Global hooks registry
_hooks: Dict[DownloadEvent, List[Callable]] = {event: [] for event in DownloadEvent}
_middleware_enabled = True

def middleware_enabled() -> bool:
    """Check if middleware system is enabled"""
    return _middleware_enabled

def enable_middleware():
    """Enable middleware system"""
    global _middleware_enabled
    _middleware_enabled = True

def disable_middleware():
    """Disable middleware system"""
    global _middleware_enabled
    _middleware_enabled = False

def register_hook(event_type: DownloadEvent):
    """
    Decorator to register a hook for a specific event type
    
    Args:
        event_type: The event type to listen for
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[[EventData], None]):
        if event_type in _hooks:
            _hooks[event_type].append(func)
        return func
    return decorator

def add_hook(event_type: DownloadEvent, func: Callable[[EventData], None]):
    """
    Add a hook function for a specific event type
    
    Args:
        event_type: The event type to listen for
        func: The function to call when the event is triggered
    """
    if event_type in _hooks:
        _hooks[event_type].append(func)

def remove_hook(event_type: DownloadEvent, func: Callable[[EventData], None]):
    """
    Remove a hook function for a specific event type
    
    Args:
        event_type: The event type
        func: The function to remove
    """
    if event_type in _hooks and func in _hooks[event_type]:
        _hooks[event_type].remove(func)

def trigger_event(event_type: DownloadEvent, data: Dict[str, Any] = None):
    """
    Trigger an event and call all registered hooks
    
    Args:
        event_type: The event type to trigger
        data: Event data to pass to hooks
    """
    if not _middleware_enabled:
        return
        
    event_data = EventData(event_type, data)
    
    # Call all registered hooks for this event type
    for hook in _hooks.get(event_type, []):
        try:
            hook(event_data)
        except Exception as e:
            # Silently ignore hook errors to prevent breaking downloads
            pass

def clear_hooks(event_type: DownloadEvent = None):
    """
    Clear hooks for a specific event type or all events
    
    Args:
        event_type: The event type to clear, or None to clear all
    """
    if event_type is None:
        for event in _hooks:
            _hooks[event].clear()
    elif event_type in _hooks:
        _hooks[event_type].clear()

def get_hooks(event_type: DownloadEvent) -> List[Callable]:
    """
    Get all hooks registered for an event type
    
    Args:
        event_type: The event type
        
    Returns:
        List of hook functions
    """
    return _hooks.get(event_type, []).copy()

def get_all_hooks() -> Dict[DownloadEvent, List[Callable]]:
    """
    Get all registered hooks
    
    Returns:
        Dictionary mapping event types to hook lists
    """
    return {event: hooks.copy() for event, hooks in _hooks.items()}

# Convenience functions for common events
def on_download_start(func: Callable[[EventData], None]):
    """Register a hook for download start events"""
    return register_hook(DownloadEvent.DOWNLOAD_START)(func)

def on_download_complete(func: Callable[[EventData], None]):
    """Register a hook for download complete events"""
    return register_hook(DownloadEvent.DOWNLOAD_COMPLETE)(func)

def on_download_error(func: Callable[[EventData], None]):
    """Register a hook for download error events"""
    return register_hook(DownloadEvent.DOWNLOAD_ERROR)(func)

def on_extraction_start(func: Callable[[EventData], None]):
    """Register a hook for extraction start events"""
    return register_hook(DownloadEvent.EXTRACTION_START)(func)

def on_extraction_complete(func: Callable[[EventData], None]):
    """Register a hook for extraction complete events"""
    return register_hook(DownloadEvent.EXTRACTION_COMPLETE)(func)
