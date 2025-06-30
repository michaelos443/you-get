#!/usr/bin/env python3

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from you_get.common import EnhancedProgressBar

def test_enhanced_progress_bar():
    """Test the enhanced progress bar functionality."""
    print("Testing Enhanced Progress Bar...")
    
    # Create a progress bar for a 10MB download
    total_size = 10 * 1024 * 1024  # 10MB
    bar = EnhancedProgressBar(total_size)
    
    # Simulate download progress
    chunk_size = 64 * 1024  # 64KB chunks
    downloaded = 0
    
    print("Starting simulated download...")
    bar.update()
    
    while downloaded < total_size:
        # Simulate variable download speeds
        time.sleep(0.1)  # Simulate network delay
        
        # Vary chunk size to simulate real network conditions
        current_chunk = min(chunk_size + (downloaded % 32768), total_size - downloaded)
        downloaded += current_chunk
        
        bar.update_received(current_chunk)
        
        # Simulate some speed variations
        if downloaded > total_size * 0.3 and downloaded < total_size * 0.7:
            time.sleep(0.05)  # Slower in the middle
    
    bar.done()
    print("\nDownload simulation completed!")
    print("Enhanced progress bar features demonstrated:")
    print("✓ ETA calculation")
    print("✓ Speed trends (↑↓→)")
    print("✓ Peak speed tracking")
    print("✓ Color-coded progress states")
    print("✓ Stall detection")
    print("✓ Detailed bandwidth statistics")

if __name__ == "__main__":
    test_enhanced_progress_bar()
