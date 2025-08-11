#!/usr/bin/env python3

"""
Demo script showing how to use the You-Get Download Progress Middleware System

This example demonstrates how to register custom hooks for download events
and receive real-time progress updates during downloads.
"""

import sys
import os

# Add the src directory to Python path so we can import you_get modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.middleware import register_hook, DownloadEvent, EventData


# Example 1: Simple progress callback
@register_hook(DownloadEvent.PROGRESS_UPDATE)
def simple_progress_callback(event_data: EventData):
    """Simple progress callback that prints download progress"""
    if event_data.progress_percent is not None:
        print(f"Progress: {event_data.progress_percent:.1f}% "
              f"({event_data.received}/{event_data.total_size} bytes) "
              f"Speed: {event_data.speed}")


# Example 2: Download start notification
@register_hook(DownloadEvent.DOWNLOAD_START)
def download_start_callback(event_data: EventData):
    """Callback triggered when download starts"""
    print(f"🚀 Starting download: {event_data.title}")
    print(f"   URL: {event_data.url}")
    print(f"   Output: {event_data.filepath}")
    if event_data.total_size:
        print(f"   Size: {event_data.total_size / 1048576:.2f} MB")
    print()


# Example 3: Download completion notification
@register_hook(DownloadEvent.DOWNLOAD_COMPLETE)
def download_complete_callback(event_data: EventData):
    """Callback triggered when download completes"""
    print(f"\n✅ Download completed: {event_data.title}")
    print(f"   Saved to: {event_data.filepath}")
    print()


# Example 4: Advanced progress callback with custom logic
@register_hook(DownloadEvent.PROGRESS_UPDATE)
def advanced_progress_callback(event_data: EventData):
    """Advanced progress callback with custom logic"""
    if event_data.progress_percent is not None:
        # Only print every 10% to reduce spam
        if int(event_data.progress_percent) % 10 == 0:
            mb_received = event_data.received / 1048576
            mb_total = event_data.total_size / 1048576 if event_data.total_size else 0
            print(f"📊 Milestone: {event_data.progress_percent:.0f}% complete "
                  f"({mb_received:.1f}/{mb_total:.1f} MB)")


# Example 5: Error handling callback
@register_hook(DownloadEvent.DOWNLOAD_ERROR)
def error_callback(event_data: EventData):
    """Callback triggered when download encounters an error"""
    print(f"❌ Download error: {event_data.error_message}")
    if event_data.url:
        print(f"   URL: {event_data.url}")


def main():
    """Main demo function"""
    print("You-Get Download Progress Middleware Demo")
    print("=" * 50)
    print()
    print("This demo shows how to use middleware hooks to monitor downloads.")
    print("The following hooks are registered:")
    print("- Download start notification")
    print("- Real-time progress updates")
    print("- Download completion notification")
    print("- Error handling")
    print()
    
    # Import you_get after registering hooks
    try:
        import you_get
        
        if len(sys.argv) < 2:
            print("Usage: python middleware_demo.py <URL>")
            print("Example: python middleware_demo.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
            return
        
        url = sys.argv[1]
        print(f"Downloading: {url}")
        print()
        
        # This will trigger our registered hooks
        you_get.download(url)
        
    except ImportError as e:
        print(f"Error importing you_get: {e}")
        print("Make sure you're running this from the correct directory.")
    except Exception as e:
        print(f"Error during download: {e}")


if __name__ == "__main__":
    main()
