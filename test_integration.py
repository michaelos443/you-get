#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'src')

from you_get.middleware import register_hook, DownloadEvent, emit_event

@register_hook(DownloadEvent.DOWNLOAD_START)
def test_hook(event_data):
    print("✅ Middleware hook triggered successfully!")
    print(f"   Event: {event_data.event_type.value}")
    print(f"   Title: {event_data.title}")

print("Testing middleware integration...")
emit_event(DownloadEvent.DOWNLOAD_START, title="Test Download")
print("Integration test completed!")
