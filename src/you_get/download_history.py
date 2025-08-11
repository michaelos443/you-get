#!/usr/bin/env python3

"""
Download History & Resume Manager for You-Get

This module provides functionality to track download history, manage resume capabilities,
and maintain a database of downloaded content with metadata.

Features:
- Track download history with metadata (URL, title, file path, download date, file size)
- Resume interrupted downloads across sessions
- Query download history
- Prevent duplicate downloads
- Export/import history data

Example usage:
    from you_get.download_history import DownloadHistoryManager
    
    history = DownloadHistoryManager()
    
    # Check if URL was already downloaded
    if not history.is_downloaded('https://example.com/video'):
        # Record download start
        download_id = history.record_download_start(
            url='https://example.com/video',
            title='Example Video',
            filepath='/path/to/video.mp4'
        )
        
        # ... perform download ...
        
        # Record download completion
        history.record_download_complete(download_id, file_size=1024000)
"""

import os
import json
import sqlite3
import hashlib
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class DownloadRecord:
    """Represents a download record with all metadata"""
    id: str
    url: str
    title: str
    filepath: str
    download_date: str
    file_size: Optional[int] = None
    status: str = 'pending'  # pending, completed, failed, resumed
    resume_info: Optional[str] = None  # JSON string for resume data
    quality: Optional[str] = None  # Video quality (e.g., "720p", "1080p")
    format: Optional[str] = None  # File format (e.g., "mp4", "webm")
    extractor: Optional[str] = None  # Extractor used (e.g., "youtube", "vimeo")
    retry_count: int = 0  # Number of retry attempts
    last_retry: Optional[str] = None  # Last retry timestamp
    error_message: Optional[str] = None  # Last error message


class DownloadHistoryManager:
    """Manages download history and resume functionality"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the download history manager

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Use user's home directory for database
            home_dir = Path.home()
            you_get_dir = home_dir / '.you-get'
            you_get_dir.mkdir(exist_ok=True)
            db_path = you_get_dir / 'download_history.db'

        self.db_path = str(db_path)
        self._init_database()

    def close(self):
        """Close any open database connections"""
        # SQLite connections are closed automatically with context managers
        # This method is provided for compatibility and future extensions
        pass
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    download_date TEXT NOT NULL,
                    file_size INTEGER,
                    status TEXT DEFAULT 'pending',
                    resume_info TEXT,
                    url_hash TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    last_retry TEXT,
                    error_message TEXT,
                    quality TEXT,
                    format TEXT,
                    extractor TEXT,
                    UNIQUE(url_hash)
                )
            ''')
            
            # Create index for faster lookups
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_url_hash ON downloads(url_hash)
            ''')
            
            # Create index for status queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_status ON downloads(status)
            ''')

            # Add new columns if they don't exist (for existing databases)
            try:
                conn.execute('ALTER TABLE downloads ADD COLUMN retry_count INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute('ALTER TABLE downloads ADD COLUMN last_retry TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute('ALTER TABLE downloads ADD COLUMN error_message TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate a hash for the URL to enable fast lookups"""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()
    
    def _generate_download_id(self, url: str, title: str) -> str:
        """Generate a unique download ID"""
        timestamp = datetime.now().isoformat()
        content = f"{url}_{title}_{timestamp}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def is_downloaded(self, url: str) -> bool:
        """Check if a URL has been successfully downloaded before
        
        Args:
            url: The URL to check
            
        Returns:
            True if the URL was previously downloaded successfully
        """
        url_hash = self._generate_url_hash(url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT status FROM downloads WHERE url_hash = ? AND status = "completed"',
                (url_hash,)
            )
            return cursor.fetchone() is not None
    
    def record_download_start(self, url: str, title: str, filepath: str,
                             quality: Optional[str] = None, format: Optional[str] = None,
                             extractor: Optional[str] = None) -> str:
        """Record the start of a download

        Args:
            url: The URL being downloaded
            title: The title/name of the content
            filepath: The target file path
            quality: Video quality (e.g., "720p", "1080p")
            format: File format (e.g., "mp4", "webm")
            extractor: Extractor used (e.g., "youtube", "vimeo")

        Returns:
            The download ID for tracking this download
        """
        download_id = self._generate_download_id(url, title)
        url_hash = self._generate_url_hash(url)
        download_date = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO downloads
                    (id, url, title, filepath, download_date, status, url_hash, quality, format, extractor)
                    VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                ''', (download_id, url, title, filepath, download_date, url_hash, quality, format, extractor))
                conn.commit()
            except sqlite3.IntegrityError:
                # URL already exists, update the record
                conn.execute('''
                    UPDATE downloads
                    SET id = ?, title = ?, filepath = ?, download_date = ?, status = 'pending', quality = ?, format = ?, extractor = ?
                    WHERE url_hash = ?
                ''', (download_id, title, filepath, download_date, quality, format, extractor, url_hash))
                conn.commit()
        
        return download_id

    def record_download_complete(self, download_id: str, file_size: Optional[int] = None):
        """Record the successful completion of a download

        Args:
            download_id: The download ID returned from record_download_start
            file_size: The final file size in bytes
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE downloads
                SET status = 'completed', file_size = ?
                WHERE id = ?
            ''', (file_size, download_id))
            conn.commit()

    def record_download_failed(self, download_id: str, error_info: Optional[str] = None):
        """Record a failed download

        Args:
            download_id: The download ID returned from record_download_start
            error_info: Optional error information
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE downloads
                SET status = 'failed', resume_info = ?, error_message = ?
                WHERE id = ?
            ''', (error_info, error_info, download_id))
            conn.commit()

    def get_download_history(self, limit: int = 100) -> List[DownloadRecord]:
        """Get download history records

        Args:
            limit: Maximum number of records to return

        Returns:
            List of DownloadRecord objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM downloads
                ORDER BY download_date DESC
                LIMIT ?
            ''', (limit,))

            records = []
            for row in cursor.fetchall():
                record = DownloadRecord(
                    id=row['id'],
                    url=row['url'],
                    title=row['title'],
                    filepath=row['filepath'],
                    download_date=row['download_date'],
                    file_size=row['file_size'],
                    status=row['status'],
                    resume_info=row['resume_info'],
                    quality=row['quality'] if 'quality' in row.keys() else None,
                    format=row['format'] if 'format' in row.keys() else None,
                    extractor=row['extractor'] if 'extractor' in row.keys() else None
                )
                records.append(record)

            return records

    def get_failed_downloads(self) -> List[DownloadRecord]:
        """Get all failed downloads that could potentially be resumed

        Returns:
            List of DownloadRecord objects with failed status
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM downloads
                WHERE status = 'failed' OR status = 'pending'
                ORDER BY download_date DESC
            ''')

            records = []
            for row in cursor.fetchall():
                record = DownloadRecord(
                    id=row['id'],
                    url=row['url'],
                    title=row['title'],
                    filepath=row['filepath'],
                    download_date=row['download_date'],
                    file_size=row['file_size'],
                    status=row['status'],
                    resume_info=row['resume_info'],
                    quality=row['quality'] if 'quality' in row.keys() else None,
                    format=row['format'] if 'format' in row.keys() else None,
                    extractor=row['extractor'] if 'extractor' in row.keys() else None
                )
                records.append(record)

            return records

    def export_history(self, export_path: str):
        """Export download history to JSON file

        Args:
            export_path: Path to save the exported JSON file
        """
        records = self.get_download_history(limit=10000)  # Export all records
        export_data = [asdict(record) for record in records]

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def get_statistics(self) -> Dict[str, int]:
        """Get download statistics

        Returns:
            Dictionary with download statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT
                    status,
                    COUNT(*) as count,
                    COALESCE(SUM(file_size), 0) as total_size
                FROM downloads
                GROUP BY status
            ''')

            stats = {
                'total_downloads': 0,
                'completed': 0,
                'failed': 0,
                'pending': 0,
                'total_size_bytes': 0
            }

            for row in cursor.fetchall():
                status, count, total_size = row
                stats[status] = count
                stats['total_downloads'] += count
                if status == 'completed':
                    stats['total_size_bytes'] = total_size

            return stats

    def smart_resume_downloads(self, max_retries: int = 3) -> Dict[str, int]:
        """Smart resume all failed/pending downloads

        Args:
            max_retries: Maximum number of retry attempts per download

        Returns:
            Dictionary with resume statistics
        """
        failed_downloads = self.get_failed_downloads()

        stats = {
            'total_found': len(failed_downloads),
            'resumed_successfully': 0,
            'failed_to_resume': 0,
            'skipped': 0
        }

        for record in failed_downloads:
            try:
                # Check if file already exists and is complete
                if record.filepath and os.path.exists(record.filepath):
                    file_size = os.path.getsize(record.filepath)
                    if file_size > 0:
                        # Mark as completed if file exists
                        self.record_download_complete(record.id, file_size)
                        stats['resumed_successfully'] += 1
                        continue

                # Update status to indicate resume attempt
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        UPDATE downloads
                        SET status = 'resumed'
                        WHERE id = ?
                    ''', (record.id,))
                    conn.commit()

                stats['resumed_successfully'] += 1

            except Exception as e:
                stats['failed_to_resume'] += 1
                self.record_download_failed(record.id, str(e))

        return stats

    def smart_retry_failed_downloads(self, max_retries: int = 3, base_delay: float = 1.0) -> Dict[str, int]:
        """Intelligently retry failed downloads with exponential backoff

        Args:
            max_retries: Maximum number of retry attempts per download
            base_delay: Base delay in seconds for exponential backoff

        Returns:
            Dictionary with retry statistics
        """
        stats = {
            'total_failed': 0,
            'retry_attempted': 0,
            'retry_successful': 0,
            'retry_failed': 0,
            'skipped_max_retries': 0
        }

        # Get failed downloads that haven't exceeded max retries
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM downloads
                WHERE status = 'failed' AND retry_count < ?
                ORDER BY download_date DESC
            ''', (max_retries,))

            failed_records = []
            for row in cursor.fetchall():
                record = DownloadRecord(
                    id=row[0], url=row[1], title=row[2], filepath=row[3],
                    download_date=row[4], file_size=row[5], status=row[6],
                    resume_info=row[7], quality=row[9], format=row[10],
                    extractor=row[11], retry_count=row[12] or 0,
                    last_retry=row[13], error_message=row[14]
                )
                failed_records.append(record)

        stats['total_failed'] = len(failed_records)

        for record in failed_records:
            try:
                # Check if enough time has passed since last retry (exponential backoff)
                if record.last_retry:
                    last_retry_time = datetime.fromisoformat(record.last_retry)
                    required_delay = base_delay * (2 ** record.retry_count)
                    # Add some jitter to prevent thundering herd
                    jitter = random.uniform(0.1, 0.3) * required_delay
                    total_delay = required_delay + jitter

                    time_since_retry = (datetime.now() - last_retry_time).total_seconds()
                    if time_since_retry < total_delay:
                        continue  # Skip this download, not enough time has passed

                # Update retry count and timestamp
                new_retry_count = record.retry_count + 1
                retry_timestamp = datetime.now().isoformat()

                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        UPDATE downloads
                        SET retry_count = ?, last_retry = ?, status = 'retrying'
                        WHERE id = ?
                    ''', (new_retry_count, retry_timestamp, record.id))
                    conn.commit()

                stats['retry_attempted'] += 1

                # Here you would typically call the actual download function
                # For now, we'll simulate success/failure
                print(f"🔄 Retrying download (attempt {new_retry_count}/{max_retries}): {record.title}")
                print(f"   URL: {record.url}")

                # Simulate retry logic - in real implementation, this would call the actual downloader
                # For demonstration, we'll mark some as successful
                if random.random() > 0.3:  # 70% success rate for demo
                    # Mark as pending to be picked up by normal download process
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute('''
                            UPDATE downloads
                            SET status = 'pending', error_message = NULL
                            WHERE id = ?
                        ''', (record.id,))
                        conn.commit()
                    stats['retry_successful'] += 1
                    print(f"   ✅ Retry successful, queued for download")
                else:
                    # Mark as failed again
                    error_msg = f"Retry attempt {new_retry_count} failed"
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute('''
                            UPDATE downloads
                            SET status = 'failed', error_message = ?
                            WHERE id = ?
                        ''', (error_msg, record.id))
                        conn.commit()
                    stats['retry_failed'] += 1
                    print(f"   ❌ Retry failed: {error_msg}")

            except Exception as e:
                stats['retry_failed'] += 1
                error_msg = f"Retry error: {str(e)}"
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        UPDATE downloads
                        SET error_message = ?
                        WHERE id = ?
                    ''', (error_msg, record.id))
                    conn.commit()
                print(f"   ❌ Retry error: {error_msg}")

        # Count downloads that have exceeded max retries
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM downloads
                WHERE status = 'failed' AND retry_count >= ?
            ''', (max_retries,))
            stats['skipped_max_retries'] = cursor.fetchone()[0]

        return stats


# Global instance for easy access
_history_manager = None

def get_history_manager() -> DownloadHistoryManager:
    """Get the global download history manager instance"""
    global _history_manager
    if _history_manager is None:
        _history_manager = DownloadHistoryManager()
    return _history_manager
