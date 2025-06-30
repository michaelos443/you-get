#!/usr/bin/env python3

import unittest
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.queue_manager import DownloadQueue, QueueItem, Priority, ItemStatus


class TestQueueManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.queue = DownloadQueue(db_path=self.temp_db.name, max_concurrent=2)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.queue.stop()
        # Close any database connections
        import sqlite3
        try:
            # Force close any remaining connections
            import gc
            gc.collect()
            time.sleep(0.1)  # Give time for cleanup
            if os.path.exists(self.temp_db.name):
                os.unlink(self.temp_db.name)
        except (PermissionError, OSError):
            pass  # Ignore cleanup errors in tests
    
    def test_queue_item_creation(self):
        """Test QueueItem creation and defaults"""
        item = QueueItem(id="test-1", url="https://example.com/video")
        
        self.assertEqual(item.url, "https://example.com/video")
        self.assertEqual(item.priority, Priority.NORMAL)
        self.assertEqual(item.status, ItemStatus.PENDING)
        self.assertIsNotNone(item.created_at)
        self.assertEqual(item.retry_count, 0)
        self.assertEqual(item.max_retries, 3)
    
    def test_add_item_to_queue(self):
        """Test adding items to the queue"""
        item_id = self.queue.add_item("https://example.com/video1", priority=Priority.HIGH)
        
        self.assertIsNotNone(item_id)
        
        # Check queue status
        status = self.queue.get_queue_status()
        self.assertEqual(status['total_items'], 1)
        self.assertIn('pending', status['item_counts'])
        self.assertEqual(status['item_counts']['pending'], 1)
    
    def test_queue_priority_ordering(self):
        """Test that items are processed in priority order"""
        # Add items with different priorities
        low_id = self.queue.add_item("https://example.com/low", priority=Priority.LOW)
        high_id = self.queue.add_item("https://example.com/high", priority=Priority.HIGH)
        normal_id = self.queue.add_item("https://example.com/normal", priority=Priority.NORMAL)
        
        # List items should show them in priority order
        items = self.queue.list_items()
        self.assertEqual(len(items), 3)
        
        # High priority should come first
        priorities = [item['priority'] for item in items]
        # Handle both enum and value cases
        first_priority = priorities[0]
        if hasattr(first_priority, 'value'):
            self.assertEqual(first_priority.value, Priority.HIGH.value)
        else:
            self.assertEqual(first_priority, Priority.HIGH.value)
    
    def test_scheduled_downloads(self):
        """Test scheduling downloads for later"""
        future_time = datetime.now() + timedelta(hours=1)
        item_id = self.queue.add_item(
            "https://example.com/scheduled",
            scheduled_time=future_time
        )
        
        items = self.queue.list_items()
        self.assertEqual(len(items), 1)
        # Handle both enum and string cases
        status = items[0]['status']
        if hasattr(status, 'value'):
            self.assertEqual(status.value, 'scheduled')
        else:
            self.assertEqual(status, 'scheduled')
        self.assertIsNotNone(items[0]['scheduled_time'])
    
    def test_remove_item(self):
        """Test removing items from queue"""
        item_id = self.queue.add_item("https://example.com/remove-me")
        
        # Verify item exists
        status = self.queue.get_queue_status()
        self.assertEqual(status['total_items'], 1)
        
        # Remove item
        removed = self.queue.remove_item(item_id)
        self.assertTrue(removed)
        
        # Verify item is gone
        status = self.queue.get_queue_status()
        self.assertEqual(status['total_items'], 0)
    
    def test_clear_completed_items(self):
        """Test clearing completed items"""
        # Add an item and manually mark as completed
        item_id = self.queue.add_item("https://example.com/completed")
        
        # Manually update status in database
        import sqlite3
        with sqlite3.connect(self.queue.db_path) as conn:
            conn.execute(
                "UPDATE queue_items SET status = 'completed' WHERE id = ?",
                (item_id,)
            )
            conn.commit()
        
        # Clear completed items
        cleared_count = self.queue.clear_completed()
        self.assertEqual(cleared_count, 1)
        
        # Verify item is gone
        status = self.queue.get_queue_status()
        self.assertEqual(status['total_items'], 0)
    
    def test_retry_failed_items(self):
        """Test retrying failed items"""
        # Add an item and manually mark as failed
        item_id = self.queue.add_item("https://example.com/failed")
        
        # Manually update status in database
        import sqlite3
        with sqlite3.connect(self.queue.db_path) as conn:
            conn.execute(
                "UPDATE queue_items SET status = 'failed', retry_count = 2 WHERE id = ?",
                (item_id,)
            )
            conn.commit()
        
        # Retry failed items
        retried_count = self.queue.retry_failed()
        self.assertEqual(retried_count, 1)
        
        # Check that item is back to pending status
        items = self.queue.list_items()
        self.assertEqual(len(items), 1)
        # Handle both enum and string cases
        status = items[0]['status']
        if hasattr(status, 'value'):
            self.assertEqual(status.value, 'pending')
        else:
            self.assertEqual(status, 'pending')
        self.assertEqual(items[0]['retry_count'], 0)
    
    @patch('you_get.queue_manager.any_download')
    def test_download_success(self, mock_download):
        """Test successful download processing"""
        # Mock successful download
        mock_download.return_value = None
        
        # Add item and start queue
        item_id = self.queue.add_item("https://example.com/success")
        
        # Set up completion callback
        completed_items = []
        def on_complete(item):
            completed_items.append(item)
        
        self.queue.on_item_complete = on_complete
        
        # Start queue and wait briefly
        self.queue.start()
        time.sleep(0.5)  # Give it time to process
        self.queue.stop()
        
        # Verify download was called
        mock_download.assert_called_once()
        
        # Check that callback was called
        self.assertEqual(len(completed_items), 1)
        self.assertEqual(completed_items[0].status, ItemStatus.COMPLETED)
    
    @patch('you_get.queue_manager.any_download')
    def test_download_failure_with_retry(self, mock_download):
        """Test download failure and retry logic"""
        # Mock download failure
        mock_download.side_effect = Exception("Download failed")
        
        # Add item with max_retries=1 for faster testing
        item_id = self.queue.add_item("https://example.com/fail", max_retries=1)
        
        # Set up failure callback
        failed_items = []
        def on_failed(item):
            failed_items.append(item)
        
        self.queue.on_item_failed = on_failed
        
        # Start queue and wait for processing
        self.queue.start()
        time.sleep(1)  # Give it time to process and retry
        self.queue.stop()
        
        # Verify download was attempted multiple times
        self.assertGreater(mock_download.call_count, 1)
        
        # Check that failure callback was called
        self.assertEqual(len(failed_items), 1)
        self.assertEqual(failed_items[0].status, ItemStatus.FAILED)
        self.assertEqual(failed_items[0].retry_count, 1)


if __name__ == '__main__':
    unittest.main()
