#!/usr/bin/env python3

"""
Smart Download Queue Manager for You-Get

This module provides a queue-based download system that allows users to:
- Queue multiple downloads with priorities
- Manage bandwidth allocation
- Schedule downloads for specific times
- Pause/resume entire queue
- Retry failed downloads with exponential backoff
- Monitor queue status and progress

Example usage:
    from you_get.queue_manager import DownloadQueue, QueueItem, Priority
    
    queue = DownloadQueue()
    
    # Add items to queue
    queue.add_item("https://youtube.com/watch?v=example", priority=Priority.HIGH)
    queue.add_item("https://vimeo.com/example", priority=Priority.NORMAL, 
                   scheduled_time=datetime.now() + timedelta(hours=1))
    
    # Start processing queue
    queue.start()
"""

import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
import logging
from queue import PriorityQueue
import uuid

from .util import log
from .common import any_download


class Priority(Enum):
    """Download priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


class QueueStatus(Enum):
    """Queue processing status"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class ItemStatus(Enum):
    """Individual queue item status"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    SCHEDULED = "scheduled"


@dataclass
class QueueItem:
    """Represents a single download item in the queue"""
    id: str
    url: str
    priority: Priority = Priority.NORMAL
    status: ItemStatus = ItemStatus.PENDING
    created_at: datetime = None
    scheduled_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    output_dir: Optional[str] = None
    output_filename: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    download_kwargs: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.download_kwargs is None:
            self.download_kwargs = {}
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def __lt__(self, other):
        """For priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at


class DownloadQueue:
    """Smart download queue manager"""
    
    def __init__(self, db_path: Optional[str] = None, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.status = QueueStatus.STOPPED
        self._queue = PriorityQueue()
        self._active_downloads: Dict[str, threading.Thread] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Database setup
        self.db_path = db_path or str(Path.home() / ".you-get" / "queue.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # Load existing queue items from database
        self._load_queue_from_db()
        
        # Event callbacks
        self.on_item_complete: Optional[Callable[[QueueItem], None]] = None
        self.on_item_failed: Optional[Callable[[QueueItem], None]] = None
        self.on_queue_empty: Optional[Callable[[], None]] = None
        
        self.logger = logging.getLogger(__name__)
    
    def _init_database(self):
        """Initialize SQLite database for queue persistence"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS queue_items (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    scheduled_time TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    output_dir TEXT,
                    output_filename TEXT,
                    progress REAL DEFAULT 0.0,
                    error_message TEXT,
                    download_kwargs TEXT
                )
            """)
            conn.commit()
    
    def _load_queue_from_db(self):
        """Load pending queue items from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM queue_items 
                WHERE status IN ('pending', 'scheduled', 'paused')
                ORDER BY priority, created_at
            """)
            
            for row in cursor.fetchall():
                item = self._row_to_queue_item(row)
                self._queue.put(item)
    
    def _row_to_queue_item(self, row) -> QueueItem:
        """Convert database row to QueueItem"""
        return QueueItem(
            id=row[0],
            url=row[1],
            priority=Priority(row[2]),
            status=ItemStatus(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            scheduled_time=datetime.fromisoformat(row[5]) if row[5] else None,
            retry_count=row[6],
            max_retries=row[7],
            output_dir=row[8],
            output_filename=row[9],
            progress=row[10],
            error_message=row[11],
            download_kwargs=json.loads(row[12]) if row[12] else {}
        )
    
    def _save_item_to_db(self, item: QueueItem):
        """Save queue item to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO queue_items 
                (id, url, priority, status, created_at, scheduled_time, retry_count, 
                 max_retries, output_dir, output_filename, progress, error_message, download_kwargs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id, item.url, item.priority.value, item.status.value,
                item.created_at.isoformat(),
                item.scheduled_time.isoformat() if item.scheduled_time else None,
                item.retry_count, item.max_retries, item.output_dir, item.output_filename,
                item.progress, item.error_message, json.dumps(item.download_kwargs)
            ))
            conn.commit()
    
    def add_item(self, url: str, priority: Priority = Priority.NORMAL,
                 scheduled_time: Optional[datetime] = None, output_dir: Optional[str] = None,
                 output_filename: Optional[str] = None, max_retries: int = 3,
                 **download_kwargs) -> str:
        """Add a new item to the download queue"""
        item = QueueItem(
            id=str(uuid.uuid4()),
            url=url,
            priority=priority,
            scheduled_time=scheduled_time,
            output_dir=output_dir,
            output_filename=output_filename,
            max_retries=max_retries,
            download_kwargs=download_kwargs,
            status=ItemStatus.SCHEDULED if scheduled_time else ItemStatus.PENDING
        )
        
        with self._lock:
            self._queue.put(item)
            self._save_item_to_db(item)
        
        log.i(f"Added item to queue: {url} (Priority: {priority.name}, ID: {item.id})")
        return item.id
    
    def remove_item(self, item_id: str) -> bool:
        """Remove an item from the queue"""
        with self._lock:
            # Remove from active downloads if running
            if item_id in self._active_downloads:
                # Note: This is a simplified approach. In production, you'd want
                # to properly signal the download thread to stop
                self._active_downloads[item_id].join(timeout=1)
                del self._active_downloads[item_id]
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM queue_items WHERE id = ?", (item_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
            
            if deleted:
                log.i(f"Removed item from queue: {item_id}")
            return deleted
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM queue_items 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
        
        return {
            "queue_status": self.status.value,
            "active_downloads": len(self._active_downloads),
            "max_concurrent": self.max_concurrent,
            "item_counts": status_counts,
            "total_items": sum(status_counts.values())
        }
    
    def list_items(self, status_filter: Optional[ItemStatus] = None) -> List[Dict[str, Any]]:
        """List queue items with optional status filter"""
        with sqlite3.connect(self.db_path) as conn:
            if status_filter:
                cursor = conn.execute(
                    "SELECT * FROM queue_items WHERE status = ? ORDER BY priority, created_at",
                    (status_filter.value,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM queue_items ORDER BY priority, created_at"
                )
            
            items = []
            for row in cursor.fetchall():
                item = self._row_to_queue_item(row)
                items.append(asdict(item))
            
            return items

    def start(self):
        """Start processing the download queue"""
        if self.status == QueueStatus.RUNNING:
            log.w("Queue is already running")
            return

        self.status = QueueStatus.RUNNING
        self._stop_event.clear()
        self._pause_event.clear()

        # Start the main queue processing thread
        self._queue_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._queue_thread.start()

        log.i("Download queue started")

    def stop(self):
        """Stop processing the download queue"""
        if self.status == QueueStatus.STOPPED:
            return

        self.status = QueueStatus.STOPPED
        self._stop_event.set()

        # Wait for active downloads to complete (with timeout)
        with self._lock:
            for thread in list(self._active_downloads.values()):
                thread.join(timeout=5)

        log.i("Download queue stopped")

    def pause(self):
        """Pause the download queue"""
        if self.status != QueueStatus.RUNNING:
            return

        self.status = QueueStatus.PAUSED
        self._pause_event.set()
        log.i("Download queue paused")

    def resume(self):
        """Resume the download queue"""
        if self.status != QueueStatus.PAUSED:
            return

        self.status = QueueStatus.RUNNING
        self._pause_event.clear()
        log.i("Download queue resumed")

    def _process_queue(self):
        """Main queue processing loop"""
        while not self._stop_event.is_set():
            try:
                # Wait if paused
                if self._pause_event.is_set():
                    time.sleep(1)
                    continue

                # Check if we can start more downloads
                with self._lock:
                    if len(self._active_downloads) >= self.max_concurrent:
                        time.sleep(1)
                        continue

                # Get next item from queue
                try:
                    item = self._queue.get(timeout=1)
                except:
                    continue

                # Check if item is scheduled for later
                if item.scheduled_time and datetime.now() < item.scheduled_time:
                    # Put it back in queue and wait
                    self._queue.put(item)
                    time.sleep(10)
                    continue

                # Start download in separate thread
                download_thread = threading.Thread(
                    target=self._download_item,
                    args=(item,),
                    daemon=True
                )

                with self._lock:
                    self._active_downloads[item.id] = download_thread

                download_thread.start()

            except Exception as e:
                self.logger.error(f"Error in queue processing: {e}")
                time.sleep(1)

    def _download_item(self, item: QueueItem):
        """Download a single queue item"""
        try:
            # Update status to downloading
            item.status = ItemStatus.DOWNLOADING
            self._save_item_to_db(item)

            log.i(f"Starting download: {item.url}")

            # Prepare download arguments
            download_args = item.download_kwargs.copy()
            if item.output_dir:
                download_args['output_dir'] = item.output_dir
            if item.output_filename:
                download_args['output_filename'] = item.output_filename

            # Perform the actual download
            any_download(item.url, **download_args)

            # Mark as completed
            item.status = ItemStatus.COMPLETED
            item.progress = 100.0
            self._save_item_to_db(item)

            log.i(f"Download completed: {item.url}")

            # Call completion callback
            if self.on_item_complete:
                self.on_item_complete(item)

        except Exception as e:
            # Handle download failure
            item.retry_count += 1
            item.error_message = str(e)

            if item.retry_count < item.max_retries:
                # Schedule retry with exponential backoff
                retry_delay = min(300, 30 * (2 ** item.retry_count))  # Max 5 minutes
                item.scheduled_time = datetime.now() + timedelta(seconds=retry_delay)
                item.status = ItemStatus.SCHEDULED

                log.w(f"Download failed, retrying in {retry_delay}s: {item.url} (attempt {item.retry_count}/{item.max_retries})")

                # Put back in queue for retry
                self._queue.put(item)
            else:
                # Mark as permanently failed
                item.status = ItemStatus.FAILED
                log.e(f"Download permanently failed: {item.url} - {e}")

                # Call failure callback
                if self.on_item_failed:
                    self.on_item_failed(item)

            self._save_item_to_db(item)

        finally:
            # Remove from active downloads
            with self._lock:
                if item.id in self._active_downloads:
                    del self._active_downloads[item.id]

            # Check if queue is empty
            if self._queue.empty() and not self._active_downloads:
                if self.on_queue_empty:
                    self.on_queue_empty()

    def clear_completed(self):
        """Remove completed items from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM queue_items WHERE status = 'completed'")
            deleted_count = cursor.rowcount
            conn.commit()

        log.i(f"Cleared {deleted_count} completed items from queue")
        return deleted_count

    def clear_failed(self):
        """Remove failed items from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM queue_items WHERE status = 'failed'")
            deleted_count = cursor.rowcount
            conn.commit()

        log.i(f"Cleared {deleted_count} failed items from queue")
        return deleted_count

    def retry_failed(self):
        """Retry all failed items"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE queue_items
                SET status = 'pending', retry_count = 0, error_message = NULL
                WHERE status = 'failed'
            """)
            updated_count = cursor.rowcount
            conn.commit()

            # Reload queue from database
            self._load_queue_from_db()

        log.i(f"Reset {updated_count} failed items for retry")
        return updated_count


# Global queue instance for CLI usage
_global_queue = None

def get_global_queue() -> DownloadQueue:
    """Get or create the global download queue instance"""
    global _global_queue
    if _global_queue is None:
        _global_queue = DownloadQueue()
    return _global_queue
