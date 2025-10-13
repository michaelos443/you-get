#!/usr/bin/env python

"""
Download History Manager for You-Get
Tracks all downloads and allows resuming incomplete downloads.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from .util import log


class DownloadRecord:
    """Represents a download record."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.url = kwargs.get('url')
        self.title = kwargs.get('title')
        self.site = kwargs.get('site')
        self.filepath = kwargs.get('output_path')
        self.file_size = kwargs.get('file_size')
        self.downloaded_size = kwargs.get('downloaded_size', 0)
        self.status = kwargs.get('status', 'pending')
        self.download_date = kwargs.get('created_at', datetime.now().isoformat())
        self.completed_at = kwargs.get('completed_at')
        self.metadata = kwargs.get('metadata')


class DownloadHistory:
    """Manages download history using SQLite database."""

    def __init__(self, db_path=None):
        """Initialize the download history database."""
        if db_path is None:
            # Use .you-get directory in user's home
            home = Path.home()
            you_get_dir = home / '.you-get'
            you_get_dir.mkdir(exist_ok=True)
            db_path = you_get_dir / 'history.db'

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    site TEXT,
                    output_path TEXT,
                    file_size INTEGER,
                    downloaded_size INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata TEXT
                )
            ''')
            conn.commit()

    def add_download(self, url, title=None, site=None, output_path=None,
                     file_size=None, metadata=None):
        """Add a new download record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO downloads
                (url, title, site, output_path, file_size, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, title, site, output_path, file_size,
                  json.dumps(metadata) if metadata else None))
            conn.commit()
            log.i(f'[history] Added download record for: {title or url}')

    def update_status(self, download_id, status, downloaded_size=None):
        """Update download status."""
        with sqlite3.connect(self.db_path) as conn:
            if status == 'completed':
                conn.execute('''
                    UPDATE downloads
                    SET status = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, download_id))
            else:
                conn.execute('''
                    UPDATE downloads
                    SET status = ?, downloaded_size = ?
                    WHERE id = ?
                ''', (status, downloaded_size or 0, download_id))
            conn.commit()

    def get_download(self, download_id):
        """Get a specific download record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM downloads WHERE id = ?',
                (download_id,)
            )
            row = cursor.fetchone()
            return DownloadRecord(**dict(row)) if row else None

    def get_download_history(self, limit=50):
        """Get download history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM downloads ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            return [DownloadRecord(**dict(row)) for row in cursor.fetchall()]

    def get_failed_downloads(self):
        """Get all failed/pending downloads."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM downloads WHERE status IN (?, ?) ORDER BY created_at DESC',
                ('pending', 'failed')
            )
            return [DownloadRecord(**dict(row)) for row in cursor.fetchall()]

    def get_statistics(self):
        """Get download statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM downloads')
            total = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM downloads WHERE status = ?', ('completed',))
            completed = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM downloads WHERE status = ?', ('failed',))
            failed = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM downloads WHERE status = ?', ('pending',))
            pending = cursor.fetchone()[0]

            cursor = conn.execute('SELECT SUM(file_size) FROM downloads WHERE status = ?', ('completed',))
            total_size = cursor.fetchone()[0] or 0

            return {
                'total_downloads': total,
                'completed': completed,
                'failed': failed,
                'pending': pending,
                'total_size_bytes': total_size
            }

    def export_history(self, filepath):
        """Export history to JSON file."""
        records = self.get_download_history(limit=1000)
        data = [
            {
                'id': r.id,
                'url': r.url,
                'title': r.title,
                'site': r.site,
                'status': r.status,
                'date': r.download_date,
                'size': r.file_size
            }
            for r in records
        ]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Global history instance
_history_instance = None


def get_history(db_path=None):
    """Get or create the global history instance."""
    global _history_instance
    if _history_instance is None:
        _history_instance = DownloadHistory(db_path)
    return _history_instance


def get_history_manager(db_path=None):
    """Alias for get_history for compatibility."""
    return get_history(db_path)

