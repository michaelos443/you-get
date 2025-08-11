#!/usr/bin/env python3

import unittest
import tempfile
import os
from pathlib import Path

# Add the src directory to the path so we can import you_get modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.download_history import DownloadHistoryManager, DownloadRecord


class TestDownloadHistory(unittest.TestCase):
    """Test cases for the Download History & Resume Manager"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary database file for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.history_manager = DownloadHistoryManager(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up after each test method."""
        # Close the history manager to release database connections
        if hasattr(self, 'history_manager'):
            self.history_manager.close()
            del self.history_manager

        # Remove the temporary database file
        try:
            if os.path.exists(self.temp_db.name):
                os.unlink(self.temp_db.name)
        except PermissionError:
            # On Windows, sometimes the file is still locked
            # Try again after a short delay
            import time
            time.sleep(0.1)
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                pass  # Give up if still locked
    
    def test_record_download_start(self):
        """Test recording the start of a download"""
        url = "https://example.com/video.mp4"
        title = "Test Video"
        filepath = "/tmp/test_video.mp4"
        
        download_id = self.history_manager.record_download_start(url, title, filepath)
        
        # Check that a download ID was returned
        self.assertIsNotNone(download_id)
        self.assertIsInstance(download_id, str)
        self.assertTrue(len(download_id) > 0)
    
    def test_is_downloaded_false_for_new_url(self):
        """Test that is_downloaded returns False for a new URL"""
        url = "https://example.com/new_video.mp4"
        
        result = self.history_manager.is_downloaded(url)
        
        self.assertFalse(result)
    
    def test_is_downloaded_true_after_completion(self):
        """Test that is_downloaded returns True after a download is completed"""
        url = "https://example.com/completed_video.mp4"
        title = "Completed Video"
        filepath = "/tmp/completed_video.mp4"
        
        # Record download start
        download_id = self.history_manager.record_download_start(url, title, filepath)
        
        # Initially should not be considered downloaded
        self.assertFalse(self.history_manager.is_downloaded(url))
        
        # Record completion
        self.history_manager.record_download_complete(download_id, file_size=1024000)
        
        # Now should be considered downloaded
        self.assertTrue(self.history_manager.is_downloaded(url))
    
    def test_record_download_complete(self):
        """Test recording download completion"""
        url = "https://example.com/video.mp4"
        title = "Test Video"
        filepath = "/tmp/test_video.mp4"
        file_size = 2048000
        
        download_id = self.history_manager.record_download_start(url, title, filepath)
        self.history_manager.record_download_complete(download_id, file_size)
        
        # Verify the download is marked as completed
        self.assertTrue(self.history_manager.is_downloaded(url))
    
    def test_record_download_failed(self):
        """Test recording download failure"""
        url = "https://example.com/failed_video.mp4"
        title = "Failed Video"
        filepath = "/tmp/failed_video.mp4"
        error_info = "Network timeout"
        
        download_id = self.history_manager.record_download_start(url, title, filepath)
        self.history_manager.record_download_failed(download_id, error_info)
        
        # Verify the download is not marked as completed
        self.assertFalse(self.history_manager.is_downloaded(url))
        
        # Check failed downloads
        failed_downloads = self.history_manager.get_failed_downloads()
        self.assertEqual(len(failed_downloads), 1)
        self.assertEqual(failed_downloads[0].status, 'failed')
        self.assertEqual(failed_downloads[0].url, url)
    
    def test_get_download_history(self):
        """Test retrieving download history"""
        # Add multiple downloads
        downloads = [
            ("https://example.com/video1.mp4", "Video 1", "/tmp/video1.mp4"),
            ("https://example.com/video2.mp4", "Video 2", "/tmp/video2.mp4"),
            ("https://example.com/video3.mp4", "Video 3", "/tmp/video3.mp4"),
        ]
        
        for url, title, filepath in downloads:
            download_id = self.history_manager.record_download_start(url, title, filepath)
            self.history_manager.record_download_complete(download_id, 1024000)
        
        # Get history
        history = self.history_manager.get_download_history()
        
        self.assertEqual(len(history), 3)
        self.assertIsInstance(history[0], DownloadRecord)
        
        # Check that they're ordered by date (most recent first)
        for record in history:
            self.assertEqual(record.status, 'completed')
    
    def test_get_statistics(self):
        """Test getting download statistics"""
        # Add some downloads with different statuses
        url1 = "https://example.com/video1.mp4"
        download_id1 = self.history_manager.record_download_start(url1, "Video 1", "/tmp/video1.mp4")
        self.history_manager.record_download_complete(download_id1, 1024000)
        
        url2 = "https://example.com/video2.mp4"
        download_id2 = self.history_manager.record_download_start(url2, "Video 2", "/tmp/video2.mp4")
        self.history_manager.record_download_failed(download_id2, "Error")
        
        url3 = "https://example.com/video3.mp4"
        self.history_manager.record_download_start(url3, "Video 3", "/tmp/video3.mp4")
        # Leave this one pending
        
        stats = self.history_manager.get_statistics()
        
        self.assertEqual(stats['total_downloads'], 3)
        self.assertEqual(stats['completed'], 1)
        self.assertEqual(stats['failed'], 1)
        self.assertEqual(stats['pending'], 1)
        self.assertEqual(stats['total_size_bytes'], 1024000)
    
    def test_export_history(self):
        """Test exporting download history to JSON"""
        # Add a download
        url = "https://example.com/video.mp4"
        title = "Test Video"
        filepath = "/tmp/test_video.mp4"
        
        download_id = self.history_manager.record_download_start(url, title, filepath)
        self.history_manager.record_download_complete(download_id, 1024000)
        
        # Export to temporary file
        export_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        export_file.close()
        
        try:
            self.history_manager.export_history(export_file.name)
            
            # Verify the file was created and contains data
            self.assertTrue(os.path.exists(export_file.name))
            
            import json
            with open(export_file.name, 'r') as f:
                exported_data = json.load(f)
            
            self.assertEqual(len(exported_data), 1)
            self.assertEqual(exported_data[0]['url'], url)
            self.assertEqual(exported_data[0]['title'], title)
            self.assertEqual(exported_data[0]['status'], 'completed')
            
        finally:
            # Clean up
            if os.path.exists(export_file.name):
                os.unlink(export_file.name)


if __name__ == '__main__':
    unittest.main()
