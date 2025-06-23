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
from datetime import datetime
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
    
    def record_download_start(self, url: str, title: str, filepath: str) -> str:
        """Record the start of a download
        
        Args:
            url: The URL being downloaded
            title: The title/name of the content
            filepath: The target file path
            
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
                    (id, url, title, filepath, download_date, status, url_hash)
                    VALUES (?, ?, ?, ?, ?, 'pending', ?)
                ''', (download_id, url, title, filepath, download_date, url_hash))
                conn.commit()
            except sqlite3.IntegrityError:
                # URL already exists, update the record
                conn.execute('''
                    UPDATE downloads 
                    SET id = ?, title = ?, filepath = ?, download_date = ?, status = 'pending'
                    WHERE url_hash = ?
                ''', (download_id, title, filepath, download_date, url_hash))
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
                SET status = 'failed', resume_info = ?
                WHERE id = ?
            ''', (error_info, download_id))
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
                    resume_info=row['resume_info']
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
                    resume_info=row['resume_info']
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


# Global instance for easy access
_history_manager = None

def get_history_manager() -> DownloadHistoryManager:
    """Get the global download history manager instance"""
    global _history_manager
    if _history_manager is None:
        _history_manager = DownloadHistoryManager()
    return _history_manager
