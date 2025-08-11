#!/usr/bin/env python3

"""
Download Progress Middleware System for You-Get

This module provides a hook-based middleware system that allows users to register
custom callbacks during the download process. It enables extensibility without
modifying core download logic.

Example usage:
    from you_get.middleware import register_hook, DownloadEvent
    
    @register_hook(DownloadEvent.PROGRESS_UPDATE)
    def my_progress_callback(event_data):
        print(f"Downloaded: {event_data['received']}/{event_data['total']} bytes")
    
    @register_hook(DownloadEvent.DOWNLOAD_COMPLETE)
    def my_completion_callback(event_data):
        print(f"Download completed: {event_data['filepath']}")
"""

from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class DownloadEvent(Enum):
    """Download event types that can trigger middleware hooks"""
    DOWNLOAD_START = "download_start"
    PROGRESS_UPDATE = "progress_update"
    DOWNLOAD_COMPLETE = "download_complete"
    DOWNLOAD_ERROR = "download_error"
    MERGE_START = "merge_start"
    MERGE_COMPLETE = "merge_complete"


@dataclass
class EventData:
    """Container for event data passed to hooks"""
    event_type: DownloadEvent
    url: Optional[str] = None
    title: Optional[str] = None
    filepath: Optional[str] = None
    total_size: Optional[int] = None
    received: Optional[int] = None
    progress_percent: Optional[float] = None
    speed: Optional[str] = None
    error_message: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class MiddlewareRegistry:
    """Registry for managing download middleware hooks"""
    
    def __init__(self):
        self._hooks: Dict[DownloadEvent, List[Callable]] = {
            event: [] for event in DownloadEvent
        }
        self._enabled = True
    
    def register_hook(self, event_type: DownloadEvent, callback: Callable[[EventData], None]):
        """Register a callback for a specific download event"""
        if not callable(callback):
            raise ValueError("Hook callback must be callable")
        
        self._hooks[event_type].append(callback)
        logger.debug(f"Registered hook for {event_type.value}: {callback.__name__}")
    
    def unregister_hook(self, event_type: DownloadEvent, callback: Callable):
        """Unregister a specific callback"""
        if callback in self._hooks[event_type]:
            self._hooks[event_type].remove(callback)
            logger.debug(f"Unregistered hook for {event_type.value}: {callback.__name__}")
    
    def emit_event(self, event_data: EventData):
        """Emit an event to all registered hooks"""
        if not self._enabled:
            return
        
        event_type = event_data.event_type
        hooks = self._hooks.get(event_type, [])
        
        for hook in hooks:
            try:
                hook(event_data)
            except Exception as e:
                logger.error(f"Error in hook {hook.__name__} for {event_type.value}: {e}")
    
    def enable(self):
        """Enable middleware system"""
        self._enabled = True
    
    def disable(self):
        """Disable middleware system"""
        self._enabled = False
    
    def clear_hooks(self, event_type: Optional[DownloadEvent] = None):
        """Clear hooks for a specific event type or all events"""
        if event_type:
            self._hooks[event_type].clear()
        else:
            for hooks in self._hooks.values():
                hooks.clear()
    
    def get_hook_count(self, event_type: DownloadEvent) -> int:
        """Get number of registered hooks for an event type"""
        return len(self._hooks[event_type])


# Global registry instance
_registry = MiddlewareRegistry()


def register_hook(event_type: DownloadEvent):
    """Decorator for registering download hooks"""
    def decorator(func: Callable[[EventData], None]):
        _registry.register_hook(event_type, func)
        return func
    return decorator


def emit_event(event_type: DownloadEvent, **kwargs):
    """Convenience function to emit events"""
    event_data = EventData(event_type=event_type, **kwargs)
    _registry.emit_event(event_data)


def get_registry() -> MiddlewareRegistry:
    """Get the global middleware registry"""
    return _registry


# Convenience functions for common operations
def enable_middleware():
    """Enable the middleware system"""
    _registry.enable()


def disable_middleware():
    """Disable the middleware system"""
    _registry.disable()


def clear_all_hooks():
    """Clear all registered hooks"""
    _registry.clear_hooks()
