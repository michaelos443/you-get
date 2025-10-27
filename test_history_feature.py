#!/usr/bin/env python3

import sys
import os
import tempfile
import sqlite3

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from you_get.common import DownloadHistory, show_download_history, resume_download, retry_failed_downloads, clear_download_history

def test_download_history():
    """Test the download history functionality."""
    print("🧪 Testing Download History Feature...")

    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        # Import and set up the global download history
        from you_get.common import download_history
        # Override the global instance with our test database
        import you_get.common
        you_get.common.download_history = DownloadHistory(db_path)
        history = you_get.common.download_history
        
        # Test adding downloads
        print("\n1. Testing add_download...")
        url1 = "https://example.com/video1.mp4"
        url2 = "https://example.com/video2.mp4"
        
        id1 = history.add_download(url1, "Video 1", "video1.mp4", "/tmp/video1.mp4", 1024000)
        id2 = history.add_download(url2, "Video 2", "video2.mp4", "/tmp/video2.mp4", 2048000)
        
        print(f"   Added download 1: ID {id1}")
        print(f"   Added download 2: ID {id2}")
        
        # Test updating progress
        print("\n2. Testing update_download_progress...")
        import hashlib
        url_hash1 = hashlib.md5(url1.encode()).hexdigest()
        history.update_download_progress(url_hash1, 512000)
        print(f"   Updated progress for URL 1: 512000 bytes")
        
        # Test updating status
        print("\n3. Testing update_download_status...")
        history.update_download_status(url_hash1, 'completed')
        print(f"   Updated status for URL 1: completed")
        
        history.update_download_status(url_hash1, 'failed', 'Network error')
        print(f"   Updated status for URL 1: failed (Network error)")
        
        # Test getting history
        print("\n4. Testing get_download_history...")
        history_records = history.get_download_history()
        print(f"   Retrieved {len(history_records)} history records")
        for i, record in enumerate(history_records):
            url, title, filename, status, created_at, downloaded_size, total_size = record
            print(f"   Record {i+1}: {title} ({status}) - {downloaded_size}/{total_size} bytes")
        
        # Test failed downloads
        print("\n5. Testing get_failed_downloads...")
        failed_records = history.get_failed_downloads()
        print(f"   Found {len(failed_records)} failed downloads")
        
        # Test resumable downloads
        print("\n6. Testing get_resumable_download...")
        resumable = history.get_resumable_download(url1)
        if resumable:
            filename, file_path, downloaded_size, total_size, status = resumable
            print(f"   Found resumable download: {filename} ({status}) - {downloaded_size}/{total_size} bytes")
        else:
            print("   No resumable download found")
        
        # Test retry count
        print("\n7. Testing increment_retry_count...")
        history.increment_retry_count(url_hash1)
        print(f"   Incremented retry count for URL 1")
        
        # Test the CLI functions
        print("\n8. Testing show_download_history...")
        show_download_history()
        
        print("\n9. Testing resume_download...")
        resume_download(url1)
        
        print("\n10. Testing retry_failed_downloads...")
        retry_failed_downloads()
        
        print("\n✅ All tests completed successfully!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"\n🧹 Cleaned up temporary database: {db_path}")
        # Reset the global instance
        import you_get.common
        you_get.common.download_history = None

if __name__ == "__main__":
    test_download_history()
