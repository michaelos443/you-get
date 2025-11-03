#!/usr/bin/env python

"""
Tests for the Queue Manager functionality.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys
import json

# Add the src directory to the path so we can import you_get modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.queue_manager import DownloadQueue


class TestDownloadQueue(unittest.TestCase):
    """Test cases for the DownloadQueue class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for queue storage
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.queue_file = self.temp_file.name
        
        # Create queue instance
        self.queue = DownloadQueue(queue_file=self.queue_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary file
        if os.path.exists(self.queue_file):
            os.unlink(self.queue_file)
    
    def test_add_urls(self):
        """Test adding URLs to the queue."""
        urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/watch?v=jNQXAC9IVRw'
        ]
        
        self.queue.add_urls(urls, output_dir='/tmp', info_only=True)
        
        # Check that URLs were added
        self.assertEqual(len(self.queue.queue), 2)
        
        # Check first item
        item = self.queue.queue[0]
        self.assertEqual(item['url'], urls[0])
        self.assertEqual(item['status'], 'pending')
        self.assertEqual(item['options']['output_dir'], '/tmp')
        self.assertEqual(item['options']['info_only'], True)
        self.assertEqual(item['attempts'], 0)
    
    def test_duplicate_urls(self):
        """Test that duplicate URLs are not added."""
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        
        # Add URL twice
        self.queue.add_urls([url])
        self.queue.add_urls([url])
        
        # Should only have one item
        self.assertEqual(len(self.queue.queue), 1)
    
    def test_save_and_load_queue(self):
        """Test saving and loading queue from file."""
        urls = ['https://www.youtube.com/watch?v=test1', 'https://www.youtube.com/watch?v=test2']
        self.queue.add_urls(urls, output_dir='/test')
        
        # Create new queue instance with same file
        new_queue = DownloadQueue(queue_file=self.queue_file)
        
        # Should load the same data
        self.assertEqual(len(new_queue.queue), 2)
        self.assertEqual(new_queue.queue[0]['url'], urls[0])
        self.assertEqual(new_queue.queue[1]['url'], urls[1])
    
    def test_clear_queue(self):
        """Test clearing the queue."""
        urls = ['https://www.youtube.com/watch?v=test1', 'https://www.youtube.com/watch?v=test2']
        self.queue.add_urls(urls)
        
        self.assertEqual(len(self.queue.queue), 2)
        
        self.queue.clear_queue()
        
        self.assertEqual(len(self.queue.queue), 0)
    
    def test_remove_completed(self):
        """Test removing completed items."""
        urls = ['https://www.youtube.com/watch?v=test1', 'https://www.youtube.com/watch?v=test2']
        self.queue.add_urls(urls)
        
        # Mark first item as completed
        self.queue.queue[0]['status'] = 'completed'
        
        self.queue.remove_completed()
        
        # Should only have one item left
        self.assertEqual(len(self.queue.queue), 1)
        self.assertEqual(self.queue.queue[0]['url'], urls[1])
    
    @patch('you_get.queue_manager.log')
    def test_show_queue_empty(self, mock_log):
        """Test showing empty queue."""
        self.queue.show_queue()
        mock_log.i.assert_called_with("Queue is empty")
    
    @patch('you_get.queue_manager.log')
    def test_show_queue_with_items(self, mock_log):
        """Test showing queue with items."""
        urls = ['https://www.youtube.com/watch?v=test1']
        self.queue.add_urls(urls)
        
        self.queue.show_queue()
        
        # Check that log.i was called multiple times (for header, items, summary)
        self.assertTrue(mock_log.i.call_count >= 3)
    
    def test_process_queue_success(self):
        """Test processing queue with successful downloads."""
        urls = ['https://www.youtube.com/watch?v=test1', 'https://www.youtube.com/watch?v=test2']
        self.queue.add_urls(urls)
        
        # Mock download function that succeeds
        mock_download = MagicMock()
        
        self.queue.process_queue(mock_download, output_dir='/test')
        
        # Check that download function was called for each URL
        self.assertEqual(mock_download.call_count, 2)
        
        # Check that all items are marked as completed
        for item in self.queue.queue:
            self.assertEqual(item['status'], 'completed')
            self.assertEqual(item['attempts'], 1)
    
    def test_process_queue_with_failure(self):
        """Test processing queue with download failures."""
        urls = ['https://www.youtube.com/watch?v=test1']
        self.queue.add_urls(urls)
        
        # Mock download function that fails
        mock_download = MagicMock(side_effect=Exception("Download failed"))
        
        self.queue.process_queue(mock_download)
        
        # Check that item is marked as failed
        item = self.queue.queue[0]
        self.assertEqual(item['status'], 'failed')
        self.assertEqual(item['attempts'], 1)
        self.assertEqual(item['last_error'], "Download failed")
    
    def test_process_queue_keyboard_interrupt(self):
        """Test processing queue with keyboard interrupt."""
        urls = ['https://www.youtube.com/watch?v=test1']
        self.queue.add_urls(urls)
        
        # Mock download function that raises KeyboardInterrupt
        mock_download = MagicMock(side_effect=KeyboardInterrupt())
        
        self.queue.process_queue(mock_download)
        
        # Check that item is reset to pending
        item = self.queue.queue[0]
        self.assertEqual(item['status'], 'pending')


if __name__ == '__main__':
    unittest.main()
