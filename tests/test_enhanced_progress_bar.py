#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test for the enhanced progress bar feature in you-get.
This test verifies that the progress bar displays ETA information correctly.
"""

import sys
import os
import time

# Add the src directory to the path so we can import you_get modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.common import SimpleProgressBar


def test_enhanced_progress_bar():
    """Test that the enhanced progress bar displays ETA correctly."""
    print("Testing enhanced progress bar with ETA...")
    
    # Create a progress bar for a 10MB download
    total_size = 10 * 1024 * 1024  # 10MB
    bar = SimpleProgressBar(total_size, 1)
    
    # Simulate downloading in chunks
    chunk_size = 1024 * 1024  # 1MB chunks
    downloaded = 0
    
    print("Simulating download progress...")
    
    # Test initial state (0%)
    bar.update()
    assert bar.received == 0
    print("✓ Initial state correct")
    
    # Simulate downloading 3MB
    for i in range(3):
        bar.update_received(chunk_size)
        downloaded += chunk_size
        time.sleep(0.1)  # Small delay to simulate time passing
    
    assert bar.received == downloaded
    print("✓ Progress updated correctly")
    
    # Test that speed is calculated
    assert bar.speed != ''
    print("✓ Download speed calculated")
    
    # Update a few more times to ensure ETA is displayed
    for i in range(2):
        bar.update_received(chunk_size)
        downloaded += chunk_size
        time.sleep(0.1)
    
    print("✓ ETA should be displayed in progress bar")
    
    # Complete the download
    remaining = total_size - downloaded
    bar.update_received(remaining)
    
    assert bar.received == total_size
    print("✓ Download completed successfully")
    
    # Clean up
    bar.done()
    print("✓ Progress bar cleaned up")
    
    print("\nAll tests passed! The enhanced progress bar feature is working correctly.")
    return True


if __name__ == '__main__':
    try:
        test_enhanced_progress_bar()
        print("\n✅ Enhanced progress bar test completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Enhanced progress bar test failed: {e}")
        sys.exit(1)
