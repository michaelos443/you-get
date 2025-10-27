#!/usr/bin/env python3

import sys
import os
import tempfile
import unittest
import hashlib
import sqlite3

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.common import DownloadHistory

class TestDownloadHistory(unittest.TestCase):
    """Test cases for the Download History feature."""
    
    def setUp(self):
        """Set up test database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.history = DownloadHistory(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database after each test."""
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)
    
    def test_add_download(self):
        """Test adding a new download."""
        url = "https://example.com/video.mp4"
        title = "Test Video"
        filename = "video.mp4"
        file_path = "/tmp/video.mp4"
        total_size = 1024000
        
        download_id = self.history.add_download(url, title, filename, file_path, total_size)
        
        self.assertIsNotNone(download_id)
        self.assertGreater(download_id, 0)
    
    def test_add_duplicate_download(self):
        """Test adding duplicate download returns existing ID."""
        url = "https://example.com/video.mp4"
        
        id1 = self.history.add_download(url)
        id2 = self.history.add_download(url)
        
        self.assertEqual(id1, id2)
    
    def test_update_progress(self):
        """Test updating download progress."""
        url = "https://example.com/video.mp4"
        self.history.add_download(url)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Update progress
        self.history.update_download_progress(url_hash, 512000)
        
        # Verify progress was updated
        result = self.history.get_resumable_download(url)
        self.assertIsNotNone(result)
        filename, file_path, downloaded_size, total_size, status = result
        self.assertEqual(downloaded_size, 512000)
    
    def test_update_status(self):
        """Test updating download status."""
        url = "https://example.com/video.mp4"
        self.history.add_download(url)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Update status
        self.history.update_download_status(url_hash, 'failed', 'Network error')
        
        # Verify status was updated
        history = self.history.get_download_history()
        self.assertEqual(len(history), 1)
        url_record, title, filename, status, created_at, downloaded_size, total_size = history[0]
        self.assertEqual(status, 'failed')
    
    def test_get_download_history(self):
        """Test retrieving download history."""
        # Add multiple downloads
        urls = [
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4",
            "https://example.com/video3.mp4"
        ]
        
        for url in urls:
            self.history.add_download(url)
        
        # Get history
        history = self.history.get_download_history()
        
        self.assertEqual(len(history), 3)
    
    def test_get_failed_downloads(self):
        """Test retrieving failed downloads."""
        # Add downloads with different statuses
        url1 = "https://example.com/video1.mp4"
        url2 = "https://example.com/video2.mp4"
        
        self.history.add_download(url1)
        self.history.add_download(url2)
        
        url_hash1 = hashlib.md5(url1.encode()).hexdigest()
        url_hash2 = hashlib.md5(url2.encode()).hexdigest()
        
        # Mark one as failed
        self.history.update_download_status(url_hash1, 'failed', 'Network error')
        self.history.update_download_status(url_hash2, 'completed')
        
        # Get failed downloads
        failed = self.history.get_failed_downloads()
        
        self.assertEqual(len(failed), 1)
        url, title, filename, downloaded_size, total_size, retry_count = failed[0]
        self.assertEqual(url, url1)
    
    def test_get_resumable_download(self):
        """Test retrieving resumable downloads."""
        url = "https://example.com/video.mp4"
        self.history.add_download(url, total_size=1024000)
        
        url_hash = hashlib.md5(url.encode()).hexdigest()
        self.history.update_download_progress(url_hash, 512000)
        self.history.update_download_status(url_hash, 'interrupted')
        
        # Get resumable download
        resumable = self.history.get_resumable_download(url)
        
        self.assertIsNotNone(resumable)
        filename, file_path, downloaded_size, total_size, status = resumable
        self.assertEqual(downloaded_size, 512000)
        self.assertEqual(status, 'interrupted')
    
    def test_increment_retry_count(self):
        """Test incrementing retry count."""
        url = "https://example.com/video.mp4"
        self.history.add_download(url)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Increment retry count
        self.history.increment_retry_count(url_hash)
        
        # Verify retry count was incremented
        conn = sqlite3.connect(self.history.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT retry_count FROM downloads WHERE url_hash = ?', (url_hash,))
        retry_count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(retry_count, 1)

if __name__ == '__main__':
    unittest.main()
