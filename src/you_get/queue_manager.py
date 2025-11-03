#!/usr/bin/env python

"""
Queue Manager for You-Get

A batch download queue manager that allows users to queue multiple URLs
for sequential downloading with pause/resume functionality.
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from .util import log


class DownloadQueue:
    """
    Manages a queue of URLs for batch downloading.
    
    Features:
    - Add URLs to queue
    - Process queue sequentially
    - Save/load queue state to/from file
    - Track download status and progress
    """
    
    def __init__(self, queue_file: str = "you_get_queue.json"):
        """
        Initialize the download queue.
        
        Args:
            queue_file (str): Path to the queue persistence file
        """
        self.queue_file = queue_file
        self.queue: List[Dict[str, Any]] = []
        self.load_queue()
    
    def add_urls(self, urls: List[str], **kwargs) -> None:
        """
        Add URLs to the download queue.
        
        Args:
            urls (List[str]): List of URLs to add to queue
            **kwargs: Additional download options to store with URLs
        """
        for url in urls:
            if not url.strip():
                continue
                
            # Check if URL already exists in queue
            if any(item['url'] == url for item in self.queue):
                log.w(f"URL already in queue: {url}")
                continue
            
            queue_item = {
                'url': url,
                'status': 'pending',
                'added_at': datetime.now().isoformat(),
                'options': kwargs,
                'attempts': 0,
                'last_error': None
            }
            self.queue.append(queue_item)
            log.i(f"Added to queue: {url}")
        
        self.save_queue()
        log.i(f"Queue now contains {len(self.queue)} items")
    
    def show_queue(self) -> None:
        """Display the current queue status."""
        if not self.queue:
            log.i("Queue is empty")
            return
        
        log.i(f"Download Queue ({len(self.queue)} items):")
        log.i("-" * 60)
        
        for i, item in enumerate(self.queue, 1):
            status_icon = {
                'pending': '⏳',
                'downloading': '⬇️',
                'completed': '✅',
                'failed': '❌',
                'skipped': '⏭️'
            }.get(item['status'], '❓')
            
            log.i(f"{i:2d}. {status_icon} {item['status'].upper():<12} {item['url']}")
            
            if item['status'] == 'failed' and item.get('last_error'):
                log.i(f"     Error: {item['last_error']}")
            
            if item.get('attempts', 0) > 0:
                log.i(f"     Attempts: {item['attempts']}")
        
        # Show summary
        status_counts = {}
        for item in self.queue:
            status = item['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        log.i("-" * 60)
        summary_parts = []
        for status, count in status_counts.items():
            summary_parts.append(f"{status}: {count}")
        log.i(f"Summary: {', '.join(summary_parts)}")
    
    def clear_queue(self) -> None:
        """Clear all items from the queue."""
        self.queue.clear()
        self.save_queue()
        log.i("Queue cleared")
    
    def remove_completed(self) -> None:
        """Remove completed items from the queue."""
        original_count = len(self.queue)
        self.queue = [item for item in self.queue if item['status'] != 'completed']
        removed_count = original_count - len(self.queue)
        self.save_queue()
        log.i(f"Removed {removed_count} completed items from queue")
    
    def process_queue(self, download_func, **global_options) -> None:
        """
        Process all pending items in the queue.
        
        Args:
            download_func: The download function to call for each URL
            **global_options: Global download options
        """
        if not self.queue:
            log.i("Queue is empty, nothing to process")
            return
        
        pending_items = [item for item in self.queue if item['status'] == 'pending']
        if not pending_items:
            log.i("No pending items in queue")
            return
        
        log.i(f"Processing {len(pending_items)} items from queue...")
        
        for i, item in enumerate(pending_items, 1):
            url = item['url']
            log.i(f"\n[{i}/{len(pending_items)}] Processing: {url}")
            
            # Update status to downloading
            item['status'] = 'downloading'
            item['attempts'] += 1
            self.save_queue()
            
            try:
                # Merge item options with global options
                download_options = {**global_options, **item.get('options', {})}
                
                # Call the download function
                download_func(url, **download_options)
                
                # Mark as completed
                item['status'] = 'completed'
                item['completed_at'] = datetime.now().isoformat()
                log.i(f"✅ Completed: {url}")
                
            except KeyboardInterrupt:
                log.i("\n⏸️  Queue processing interrupted by user")
                item['status'] = 'pending'  # Reset to pending for retry
                self.save_queue()
                break
                
            except Exception as e:
                # Mark as failed
                item['status'] = 'failed'
                item['last_error'] = str(e)
                log.e(f"❌ Failed: {url} - {str(e)}")
            
            finally:
                self.save_queue()
        
        # Show final summary
        log.i("\n" + "="*60)
        self.show_queue()
    
    def save_queue(self) -> None:
        """Save the queue to file."""
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.queue, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.e(f"Failed to save queue: {e}")
    
    def load_queue(self) -> None:
        """Load the queue from file."""
        if not os.path.exists(self.queue_file):
            return
        
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                self.queue = json.load(f)
            log.d(f"Loaded {len(self.queue)} items from queue file")
        except Exception as e:
            log.e(f"Failed to load queue: {e}")
            self.queue = []


# Global queue instance
_queue_manager = None

def get_queue_manager() -> DownloadQueue:
    """Get the global queue manager instance."""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = DownloadQueue()
    return _queue_manager
