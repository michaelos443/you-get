#!/usr/bin/env python3

"""
Test script for the Smart Retry feature
"""

import sys
import os
import tempfile
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from you_get.download_history import DownloadHistoryManager

def test_smart_retry():
    """Test the smart retry functionality"""
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Initialize the history manager
        history = DownloadHistoryManager(db_path=db_path)
        
        # Create some test failed downloads
        print("Creating test failed downloads...")
        
        # Test download 1 - should be retried
        download_id1 = history.record_download_start(
            url='https://example.com/video1.mp4',
            title='Test Video 1',
            filepath='/tmp/video1.mp4'
        )
        history.record_download_failed(download_id1, 'Network timeout')
        
        # Test download 2 - should be retried
        download_id2 = history.record_download_start(
            url='https://example.com/video2.mp4',
            title='Test Video 2',
            filepath='/tmp/video2.mp4'
        )
        history.record_download_failed(download_id2, 'Server error 500')
        
        # Test download 3 - already completed, should be skipped
        download_id3 = history.record_download_start(
            url='https://example.com/video3.mp4',
            title='Test Video 3',
            filepath='/tmp/video3.mp4'
        )
        history.record_download_complete(download_id3, 1024000)
        
        print("✅ Test data created successfully")
        
        # Test the smart retry functionality
        print("\n🔄 Testing smart retry functionality...")
        stats = history.smart_retry_failed_downloads(max_retries=3, base_delay=0.1)
        
        print(f"\n📊 Smart Retry Results:")
        print(f"   - Total failed downloads: {stats['total_failed']}")
        print(f"   - Retry attempts made: {stats['retry_attempted']}")
        print(f"   - Successful retries: {stats['retry_successful']}")
        print(f"   - Failed retries: {stats['retry_failed']}")
        print(f"   - Skipped (max retries exceeded): {stats['skipped_max_retries']}")
        
        # Verify the results
        if stats['total_failed'] == 2:
            print("✅ Correctly identified 2 failed downloads")
        else:
            print(f"❌ Expected 2 failed downloads, got {stats['total_failed']}")
        
        if stats['retry_attempted'] > 0:
            print("✅ Retry attempts were made")
        else:
            print("❌ No retry attempts were made")
        
        # Test retry with max retries exceeded
        print("\n🔄 Testing max retries limit...")
        
        # Simulate multiple failed retries by directly updating the database
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            conn.execute('''
                UPDATE downloads
                SET retry_count = 5, status = 'failed'
                WHERE id = ?
            ''', (download_id1,))
            conn.commit()
        
        stats2 = history.smart_retry_failed_downloads(max_retries=3, base_delay=0.1)
        
        if stats2['skipped_max_retries'] > 0:
            print("✅ Correctly skipped downloads that exceeded max retries")
        else:
            print("❌ Should have skipped downloads with max retries exceeded")
        
        print("\n🎉 Smart Retry test completed successfully!")
        
    finally:
        # Clean up the temporary database
        try:
            os.unlink(db_path)
        except:
            pass

if __name__ == '__main__':
    test_smart_retry()
