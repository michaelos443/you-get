#!/usr/bin/env python3
"""
Demo script to showcase the enhanced progress bar feature.
"""

import sys
import os
import time

# Add src directory to path so we can import you_get
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from you_get.common import EnhancedProgressBar

def demo_enhanced_progress():
    """Demonstrate the enhanced progress bar with simulated download."""
    print("Enhanced Progress Bar Demo")
    print("=" * 50)
    
    # Simulate downloading a 10MB file
    total_size = 10 * 1024 * 1024  # 10MB
    bar = EnhancedProgressBar(total_size, 1)
    
    print("Simulating download of 10MB file...")
    print()
    
    # Simulate download in chunks
    chunk_size = 256 * 1024  # 256KB chunks
    downloaded = 0
    
    while downloaded < total_size:
        # Simulate variable download speed
        time.sleep(0.1)  # Small delay to see the progress
        
        # Download a chunk
        current_chunk = min(chunk_size, total_size - downloaded)
        bar.update_received(current_chunk)
        downloaded += current_chunk
    
    bar.done()
    print("\nDownload completed!")
    print("\nFeatures demonstrated:")
    print("- Real-time progress percentage")
    print("- Download speed calculation")
    print("- ETA (Estimated Time of Arrival)")
    print("- Elapsed time tracking")
    print("- Human-readable file sizes")
    print("- Adaptive progress bar width")

if __name__ == "__main__":
    demo_enhanced_progress()
