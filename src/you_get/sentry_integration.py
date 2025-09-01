#!/usr/bin/env python3

"""
Sentry Integration for You-Get Analytics Dashboard
Provides error monitoring and logging for the analytics feature
"""

import os
import sys
import traceback
from datetime import datetime

__all__ = ['init_sentry', 'log_error', 'log_analytics_error']

# Mock Sentry integration (would use real sentry-sdk in production)
class MockSentry:
    """Mock Sentry client for demonstration purposes"""
    
    def __init__(self, dsn=None):
        self.dsn = dsn
        self.enabled = dsn is not None
        self.events = []
    
    def capture_exception(self, exception=None, **kwargs):
        """Capture an exception"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'level': 'error',
            'exception': str(exception) if exception else 'Unknown error',
            'traceback': traceback.format_exc() if exception else None,
            'tags': kwargs.get('tags', {}),
            'extra': kwargs.get('extra', {}),
            'user': kwargs.get('user', {}),
            'fingerprint': kwargs.get('fingerprint', [])
        }
        
        self.events.append(event)
        print(f"[SENTRY] Exception captured: {event['exception']}")
        return event
    
    def capture_message(self, message, level='info', **kwargs):
        """Capture a message"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'tags': kwargs.get('tags', {}),
            'extra': kwargs.get('extra', {}),
            'user': kwargs.get('user', {}),
            'fingerprint': kwargs.get('fingerprint', [])
        }
        
        self.events.append(event)
        print(f"[SENTRY] Message captured ({level}): {message}")
        return event
    
    def add_breadcrumb(self, message, category=None, level='info', data=None):
        """Add a breadcrumb"""
        if not self.enabled:
            return
        
        breadcrumb = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'category': category or 'default',
            'level': level,
            'data': data or {}
        }
        
        print(f"[SENTRY] Breadcrumb: {message}")
        return breadcrumb
    
    def set_tag(self, key, value):
        """Set a tag"""
        if not self.enabled:
            return
        print(f"[SENTRY] Tag set: {key}={value}")
    
    def set_user(self, user_data):
        """Set user context"""
        if not self.enabled:
            return
        print(f"[SENTRY] User context set: {user_data}")
    
    def get_events(self):
        """Get all captured events (for testing)"""
        return self.events

# Global Sentry client
_sentry_client = None

def init_sentry(dsn=None, environment='development', release=None):
    """
    Initialize Sentry error monitoring
    
    Args:
        dsn (str): Sentry DSN (Data Source Name)
        environment (str): Environment name (development, production, etc.)
        release (str): Release version
    
    Returns:
        bool: True if Sentry was initialized successfully
    """
    global _sentry_client
    
    try:
        # In production, you would use:
        # import sentry_sdk
        # sentry_sdk.init(dsn=dsn, environment=environment, release=release)
        
        # For demonstration, use mock client
        _sentry_client = MockSentry(dsn=dsn or "https://mock-dsn@sentry.io/project-id")
        
        # Set up tags for analytics dashboard
        _sentry_client.set_tag('component', 'analytics-dashboard')
        _sentry_client.set_tag('feature', 'you-get-analytics')
        
        if environment:
            _sentry_client.set_tag('environment', environment)
        
        if release:
            _sentry_client.set_tag('release', release)
        
        print(f"[SENTRY] Initialized successfully for environment: {environment}")
        return True
        
    except Exception as e:
        print(f"[SENTRY] Failed to initialize: {e}")
        return False

def log_error(exception, context=None, user_id=None):
    """
    Log an error to Sentry
    
    Args:
        exception (Exception): The exception to log
        context (dict): Additional context information
        user_id (str): User identifier
    """
    if not _sentry_client:
        print(f"[ERROR] Sentry not initialized: {exception}")
        return
    
    extra = context or {}
    extra['component'] = 'you-get-analytics'
    
    user_data = {}
    if user_id:
        user_data['id'] = user_id
    
    return _sentry_client.capture_exception(
        exception,
        extra=extra,
        user=user_data,
        tags={'error_type': type(exception).__name__}
    )

def log_analytics_error(error_type, message, details=None):
    """
    Log an analytics-specific error
    
    Args:
        error_type (str): Type of analytics error
        message (str): Error message
        details (dict): Additional error details
    """
    if not _sentry_client:
        print(f"[ANALYTICS ERROR] {error_type}: {message}")
        return
    
    extra = details or {}
    extra.update({
        'component': 'analytics-dashboard',
        'error_type': error_type,
        'feature': 'you-get-analytics'
    })
    
    return _sentry_client.capture_message(
        f"Analytics Error - {error_type}: {message}",
        level='error',
        extra=extra,
        tags={
            'analytics_error': error_type,
            'component': 'dashboard'
        }
    )

def log_analytics_event(event_type, message, data=None):
    """
    Log an analytics event (non-error)
    
    Args:
        event_type (str): Type of event
        message (str): Event message
        data (dict): Event data
    """
    if not _sentry_client:
        return
    
    extra = data or {}
    extra.update({
        'component': 'analytics-dashboard',
        'event_type': event_type
    })
    
    return _sentry_client.capture_message(
        f"Analytics Event - {event_type}: {message}",
        level='info',
        extra=extra,
        tags={
            'analytics_event': event_type,
            'component': 'dashboard'
        }
    )

def add_analytics_breadcrumb(message, data=None):
    """
    Add a breadcrumb for analytics operations
    
    Args:
        message (str): Breadcrumb message
        data (dict): Additional data
    """
    if not _sentry_client:
        return
    
    return _sentry_client.add_breadcrumb(
        message=message,
        category='analytics',
        level='info',
        data=data or {}
    )

def test_sentry_integration():
    """Test the Sentry integration with sample errors"""
    print("\n🔍 Testing Sentry Integration for Analytics Dashboard")
    
    # Initialize Sentry
    success = init_sentry(
        dsn="https://test-dsn@sentry.io/analytics-dashboard",
        environment="test",
        release="analytics-v1.0.0"
    )
    
    if not success:
        print("❌ Failed to initialize Sentry")
        return
    
    # Test breadcrumb
    add_analytics_breadcrumb("Dashboard server starting", {"port": 8080})
    
    # Test info event
    log_analytics_event("dashboard_start", "Analytics dashboard started successfully", {
        "port": 8080,
        "features": ["real-time-stats", "site-analytics", "file-type-tracking"]
    })
    
    # Test analytics error
    log_analytics_error("database_connection", "Failed to connect to analytics database", {
        "database_path": "~/.you-get/analytics.db",
        "error_code": "SQLITE_CANTOPEN"
    })
    
    # Test exception
    try:
        # Simulate an analytics dashboard error
        raise ValueError("Analytics dashboard port 8080 already in use")
    except Exception as e:
        log_error(e, context={
            "attempted_port": 8080,
            "feature": "analytics-dashboard",
            "operation": "server_start"
        })
    
    print("✅ Sentry integration test completed")
    
    # Show captured events
    if _sentry_client:
        events = _sentry_client.get_events()
        print(f"\n📊 Captured {len(events)} events:")
        for i, event in enumerate(events, 1):
            print(f"  {i}. [{event['level'].upper()}] {event.get('message', event.get('exception', 'Unknown'))}")

if __name__ == "__main__":
    test_sentry_integration()
