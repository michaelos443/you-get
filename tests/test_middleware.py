#!/usr/bin/env python3

"""
Unit tests for the You-Get Download Progress Middleware System
"""

import unittest
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.middleware import (
    MiddlewareRegistry, DownloadEvent, EventData, 
    register_hook, emit_event, get_registry, 
    enable_middleware, disable_middleware, clear_all_hooks
)


class TestMiddlewareSystem(unittest.TestCase):
    """Test cases for the middleware system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.registry = MiddlewareRegistry()
        self.callback_calls = []
    
    def tearDown(self):
        """Clean up after tests"""
        clear_all_hooks()
        self.callback_calls.clear()
    
    def test_hook_registration(self):
        """Test hook registration and unregistration"""
        def test_callback(event_data):
            self.callback_calls.append(event_data)
        
        # Test registration
        self.registry.register_hook(DownloadEvent.DOWNLOAD_START, test_callback)
        self.assertEqual(self.registry.get_hook_count(DownloadEvent.DOWNLOAD_START), 1)
        
        # Test unregistration
        self.registry.unregister_hook(DownloadEvent.DOWNLOAD_START, test_callback)
        self.assertEqual(self.registry.get_hook_count(DownloadEvent.DOWNLOAD_START), 0)
    
    def test_event_emission(self):
        """Test event emission to registered hooks"""
        def test_callback(event_data):
            self.callback_calls.append(event_data)
        
        self.registry.register_hook(DownloadEvent.PROGRESS_UPDATE, test_callback)
        
        # Emit an event
        event_data = EventData(
            event_type=DownloadEvent.PROGRESS_UPDATE,
            received=1024,
            total_size=2048,
            progress_percent=50.0
        )
        self.registry.emit_event(event_data)
        
        # Check that callback was called
        self.assertEqual(len(self.callback_calls), 1)
        self.assertEqual(self.callback_calls[0].received, 1024)
        self.assertEqual(self.callback_calls[0].progress_percent, 50.0)
    
    def test_multiple_hooks(self):
        """Test multiple hooks for the same event"""
        def callback1(event_data):
            self.callback_calls.append("callback1")
        
        def callback2(event_data):
            self.callback_calls.append("callback2")
        
        self.registry.register_hook(DownloadEvent.DOWNLOAD_START, callback1)
        self.registry.register_hook(DownloadEvent.DOWNLOAD_START, callback2)
        
        event_data = EventData(event_type=DownloadEvent.DOWNLOAD_START)
        self.registry.emit_event(event_data)
        
        # Both callbacks should be called
        self.assertEqual(len(self.callback_calls), 2)
        self.assertIn("callback1", self.callback_calls)
        self.assertIn("callback2", self.callback_calls)
    
    def test_enable_disable(self):
        """Test enabling and disabling the middleware system"""
        def test_callback(event_data):
            self.callback_calls.append(event_data)
        
        self.registry.register_hook(DownloadEvent.DOWNLOAD_START, test_callback)
        
        # Test disabled state
        self.registry.disable()
        event_data = EventData(event_type=DownloadEvent.DOWNLOAD_START)
        self.registry.emit_event(event_data)
        self.assertEqual(len(self.callback_calls), 0)
        
        # Test enabled state
        self.registry.enable()
        self.registry.emit_event(event_data)
        self.assertEqual(len(self.callback_calls), 1)
    
    def test_decorator_registration(self):
        """Test decorator-based hook registration"""
        @register_hook(DownloadEvent.DOWNLOAD_COMPLETE)
        def decorated_callback(event_data):
            self.callback_calls.append("decorated")
        
        # Check that hook was registered
        registry = get_registry()
        self.assertEqual(registry.get_hook_count(DownloadEvent.DOWNLOAD_COMPLETE), 1)
        
        # Test emission
        emit_event(DownloadEvent.DOWNLOAD_COMPLETE, title="test")
        self.assertEqual(len(self.callback_calls), 1)
        self.assertEqual(self.callback_calls[0], "decorated")
    
    def test_error_handling(self):
        """Test error handling in hooks"""
        def failing_callback(event_data):
            raise Exception("Test error")
        
        def working_callback(event_data):
            self.callback_calls.append("working")
        
        self.registry.register_hook(DownloadEvent.DOWNLOAD_START, failing_callback)
        self.registry.register_hook(DownloadEvent.DOWNLOAD_START, working_callback)
        
        # Even if one callback fails, others should still work
        event_data = EventData(event_type=DownloadEvent.DOWNLOAD_START)
        self.registry.emit_event(event_data)
        
        # Working callback should still be called
        self.assertEqual(len(self.callback_calls), 1)
        self.assertEqual(self.callback_calls[0], "working")
    
    def test_clear_hooks(self):
        """Test clearing hooks"""
        def test_callback(event_data):
            self.callback_calls.append(event_data)
        
        self.registry.register_hook(DownloadEvent.DOWNLOAD_START, test_callback)
        self.registry.register_hook(DownloadEvent.PROGRESS_UPDATE, test_callback)
        
        # Clear specific event hooks
        self.registry.clear_hooks(DownloadEvent.DOWNLOAD_START)
        self.assertEqual(self.registry.get_hook_count(DownloadEvent.DOWNLOAD_START), 0)
        self.assertEqual(self.registry.get_hook_count(DownloadEvent.PROGRESS_UPDATE), 1)
        
        # Clear all hooks
        self.registry.clear_hooks()
        self.assertEqual(self.registry.get_hook_count(DownloadEvent.PROGRESS_UPDATE), 0)


if __name__ == '__main__':
    unittest.main()
