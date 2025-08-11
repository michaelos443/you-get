#!/usr/bin/env python3

"""
Download Scheduling & Time-Based Automation System for You-Get

This module provides intelligent scheduling capabilities that allow users to:
- Schedule downloads for specific times
- Set up recurring download schedules
- Automatically download during off-peak hours
- Optimize downloads based on network conditions
- Create time-based download rules and policies

Example usage:
    from you_get.download_scheduler import DownloadScheduler, ScheduleRule
    
    scheduler = DownloadScheduler()
    
    # Schedule a download for 2 AM
    scheduler.schedule_download(
        url='https://youtube.com/watch?v=example',
        scheduled_time='02:00',
        rule_type='daily'
    )
    
    # Start the scheduler daemon
    scheduler.start_daemon()
"""

import os
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
# Removed schedule dependency - using built-in datetime instead

from .util import log
from .common import any_download


class ScheduleType(Enum):
    """Types of scheduling rules"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    OFF_PEAK = "off_peak"
    BANDWIDTH_OPTIMIZED = "bandwidth_optimized"


class ScheduleStatus(Enum):
    """Status of scheduled downloads"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledDownload:
    """Represents a scheduled download task"""
    id: str
    url: str
    scheduled_time: str  # Format: "HH:MM" or ISO datetime
    schedule_type: ScheduleType
    status: ScheduleStatus
    output_dir: str = "."
    output_filename: Optional[str] = None
    created_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class NetworkConditionMonitor:
    """Monitors network conditions for optimal download timing"""
    
    def __init__(self):
        self.peak_hours = [(8, 12), (18, 23)]  # 8-12 AM and 6-11 PM
        self.off_peak_hours = [(0, 6), (14, 17)]  # 12-6 AM and 2-5 PM
    
    def is_off_peak_time(self) -> bool:
        """Check if current time is during off-peak hours"""
        current_hour = datetime.now().hour
        for start, end in self.off_peak_hours:
            if start <= current_hour < end:
                return True
        return False
    
    def get_optimal_download_time(self) -> datetime:
        """Get the next optimal time for downloading"""
        now = datetime.now()
        
        # Find next off-peak period
        for start, end in self.off_peak_hours:
            next_time = now.replace(hour=start, minute=0, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            return next_time
        
        # Default to 2 AM next day
        return (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)


class DownloadScheduler:
    """Main download scheduling and automation system"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the download scheduler"""
        if db_path is None:
            db_dir = Path.home() / '.you-get'
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / 'scheduler.db'
        
        self.db_path = db_path
        self.network_monitor = NetworkConditionMonitor()
        self.running = False
        self.daemon_thread = None
        
        # Initialize database
        self._init_database()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _init_database(self):
        """Initialize SQLite database for scheduled downloads"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_downloads (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    schedule_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output_dir TEXT DEFAULT '.',
                    output_filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    metadata TEXT
                )
            ''')
            conn.commit()
    
    def schedule_download(self, url: str, scheduled_time: str, 
                         schedule_type: ScheduleType = ScheduleType.ONCE,
                         output_dir: str = ".", output_filename: Optional[str] = None,
                         **kwargs) -> str:
        """Schedule a download for a specific time"""
        import uuid
        
        download_id = str(uuid.uuid4())
        
        # Calculate next run time
        next_run = self._calculate_next_run(scheduled_time, schedule_type)
        
        scheduled_download = ScheduledDownload(
            id=download_id,
            url=url,
            scheduled_time=scheduled_time,
            schedule_type=schedule_type,
            status=ScheduleStatus.PENDING,
            output_dir=output_dir,
            output_filename=output_filename,
            next_run=next_run,
            metadata=kwargs
        )
        
        # Save to database
        self._save_scheduled_download(scheduled_download)
        
        log.i(f"📅 Scheduled download: {url}")
        log.i(f"⏰ Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        log.i(f"🔄 Schedule type: {schedule_type.value}")
        
        return download_id
    
    def _calculate_next_run(self, scheduled_time: str, schedule_type: ScheduleType) -> datetime:
        """Calculate the next run time based on schedule type"""
        now = datetime.now()
        
        if schedule_type == ScheduleType.OFF_PEAK:
            return self.network_monitor.get_optimal_download_time()
        
        if schedule_type == ScheduleType.BANDWIDTH_OPTIMIZED:
            # Schedule for 3 AM (typically lowest usage)
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        # Parse time format (HH:MM)
        try:
            hour, minute = map(int, scheduled_time.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if schedule_type == ScheduleType.ONCE:
                if next_run <= now:
                    next_run += timedelta(days=1)
            elif schedule_type == ScheduleType.DAILY:
                if next_run <= now:
                    next_run += timedelta(days=1)
            elif schedule_type == ScheduleType.WEEKLY:
                if next_run <= now:
                    next_run += timedelta(weeks=1)
            elif schedule_type == ScheduleType.MONTHLY:
                if next_run <= now:
                    # Add one month (approximate)
                    next_run += timedelta(days=30)
            
            return next_run
            
        except ValueError:
            # Fallback to 2 AM tomorrow
            return (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
    
    def _save_scheduled_download(self, download: ScheduledDownload):
        """Save scheduled download to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO scheduled_downloads 
                (id, url, scheduled_time, schedule_type, status, output_dir, 
                 output_filename, created_at, last_run, next_run, retry_count, 
                 max_retries, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                download.id, download.url, download.scheduled_time,
                download.schedule_type.value, download.status.value,
                download.output_dir, download.output_filename,
                download.created_at.isoformat() if download.created_at else None,
                download.last_run.isoformat() if download.last_run else None,
                download.next_run.isoformat() if download.next_run else None,
                download.retry_count, download.max_retries,
                json.dumps(download.metadata)
            ))
            conn.commit()
    
    def get_pending_downloads(self) -> List[ScheduledDownload]:
        """Get all pending scheduled downloads"""
        downloads = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM scheduled_downloads 
                WHERE status = ? AND next_run <= ?
                ORDER BY next_run ASC
            ''', (ScheduleStatus.PENDING.value, datetime.now().isoformat()))
            
            for row in cursor.fetchall():
                download = ScheduledDownload(
                    id=row['id'],
                    url=row['url'],
                    scheduled_time=row['scheduled_time'],
                    schedule_type=ScheduleType(row['schedule_type']),
                    status=ScheduleStatus(row['status']),
                    output_dir=row['output_dir'],
                    output_filename=row['output_filename'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_run=datetime.fromisoformat(row['last_run']) if row['last_run'] else None,
                    next_run=datetime.fromisoformat(row['next_run']) if row['next_run'] else None,
                    retry_count=row['retry_count'],
                    max_retries=row['max_retries'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                downloads.append(download)
        
        return downloads

    def execute_download(self, download: ScheduledDownload) -> bool:
        """Execute a scheduled download"""
        try:
            log.i(f"🚀 Starting scheduled download: {download.url}")

            # Update status to running
            download.status = ScheduleStatus.RUNNING
            download.last_run = datetime.now()
            self._save_scheduled_download(download)

            # Execute the download
            any_download(
                download.url,
                output_dir=download.output_dir,
                output_filename=download.output_filename,
                **download.metadata
            )

            # Update status to completed
            download.status = ScheduleStatus.COMPLETED

            # Schedule next run if recurring
            if download.schedule_type != ScheduleType.ONCE:
                download.next_run = self._calculate_next_run(
                    download.scheduled_time, download.schedule_type
                )
                download.status = ScheduleStatus.PENDING

            self._save_scheduled_download(download)
            log.i(f"✅ Completed scheduled download: {download.url}")
            return True

        except Exception as e:
            log.e(f"❌ Failed scheduled download: {download.url} - {e}")

            # Handle retry logic
            download.retry_count += 1
            if download.retry_count < download.max_retries:
                download.status = ScheduleStatus.PENDING
                download.next_run = datetime.now() + timedelta(minutes=30)  # Retry in 30 minutes
                log.i(f"🔄 Retrying in 30 minutes (attempt {download.retry_count + 1}/{download.max_retries})")
            else:
                download.status = ScheduleStatus.FAILED
                log.e(f"💀 Max retries exceeded for: {download.url}")

            self._save_scheduled_download(download)
            return False

    def start_daemon(self):
        """Start the scheduler daemon"""
        if self.running:
            log.w("Scheduler daemon is already running")
            return

        self.running = True
        self.daemon_thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self.daemon_thread.start()
        log.i("📅 Download scheduler daemon started")

    def stop_daemon(self):
        """Stop the scheduler daemon"""
        self.running = False
        if self.daemon_thread:
            self.daemon_thread.join(timeout=5)
        log.i("⏹️ Download scheduler daemon stopped")

    def _daemon_loop(self):
        """Main daemon loop that checks for pending downloads"""
        while self.running:
            try:
                pending_downloads = self.get_pending_downloads()

                for download in pending_downloads:
                    if not self.running:
                        break

                    self.execute_download(download)

                # Sleep for 60 seconds before next check
                time.sleep(60)

            except Exception as e:
                log.e(f"Scheduler daemon error: {e}")
                time.sleep(60)

    def list_scheduled_downloads(self) -> List[Dict]:
        """List all scheduled downloads"""
        downloads = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM scheduled_downloads
                ORDER BY created_at DESC
            ''')

            for row in cursor.fetchall():
                downloads.append({
                    'id': row['id'],
                    'url': row['url'],
                    'scheduled_time': row['scheduled_time'],
                    'schedule_type': row['schedule_type'],
                    'status': row['status'],
                    'next_run': row['next_run'],
                    'retry_count': row['retry_count'],
                    'created_at': row['created_at']
                })

        return downloads

    def cancel_download(self, download_id: str) -> bool:
        """Cancel a scheduled download"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE scheduled_downloads
                SET status = ?
                WHERE id = ? AND status = ?
            ''', (ScheduleStatus.CANCELLED.value, download_id, ScheduleStatus.PENDING.value))

            if cursor.rowcount > 0:
                conn.commit()
                log.i(f"❌ Cancelled scheduled download: {download_id}")
                return True
            else:
                log.w(f"Could not cancel download: {download_id} (not found or not pending)")
                return False


# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> DownloadScheduler:
    """Get global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DownloadScheduler()
    return _scheduler_instance
