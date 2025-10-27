#!/usr/bin/env python

"""
Content Verification & Integrity Checking for You-Get
Provides checksum validation, file integrity checking, and duplicate detection.
"""

import hashlib
import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from .util import log


class VerificationResult:
    """Result of content verification process"""
    
    def __init__(self, filepath: str, is_valid: bool, checksum: str = None, 
                 error: str = None, is_duplicate: bool = False, 
                 duplicate_path: str = None):
        self.filepath = filepath
        self.is_valid = is_valid
        self.checksum = checksum
        self.error = error
        self.is_duplicate = is_duplicate
        self.duplicate_path = duplicate_path
        self.verified_at = datetime.now().isoformat()


class ContentVerifier:
    """Handles content verification and integrity checking"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser("~/.you-get/verification.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the verification database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_checksums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                md5_hash TEXT NOT NULL,
                sha256_hash TEXT NOT NULL,
                verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                source_url TEXT,
                UNIQUE(md5_hash, sha256_hash)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                verification_result TEXT NOT NULL,
                verified_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_checksums(self, filepath: str) -> Tuple[str, str]:
        """Calculate MD5 and SHA256 checksums for a file"""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        try:
            with open(filepath, 'rb') as f:
                # Read file in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            return md5_hash.hexdigest(), sha256_hash.hexdigest()
        except Exception as e:
            log.e(f"Error calculating checksums for {filepath}: {e}")
            return None, None
    
    def verify_file_integrity(self, filepath: str) -> bool:
        """Verify basic file integrity"""
        try:
            if not os.path.exists(filepath):
                return False
            
            # Check if file is readable
            with open(filepath, 'rb') as f:
                f.read(1)
            
            # Check file size is reasonable (not 0 bytes)
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                return False
            
            return True
        except Exception:
            return False
    
    def check_for_duplicates(self, md5_hash: str, sha256_hash: str, 
                           current_filepath: str) -> Tuple[bool, str]:
        """Check if file with same checksums already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT filepath FROM file_checksums 
            WHERE md5_hash = ? AND sha256_hash = ? AND filepath != ?
        ''', (md5_hash, sha256_hash, current_filepath))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and os.path.exists(result[0]):
            return True, result[0]
        return False, None
    
    def store_verification_data(self, filepath: str, md5_hash: str, 
                              sha256_hash: str, source_url: str = None):
        """Store file verification data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO file_checksums 
                (filepath, filename, file_size, md5_hash, sha256_hash, source_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filepath, filename, file_size, md5_hash, sha256_hash, source_url))
            
            conn.commit()
        except sqlite3.IntegrityError:
            # Duplicate checksums - this is expected for duplicate detection
            pass
        finally:
            conn.close()
    
    def log_verification_result(self, result: VerificationResult):
        """Log verification result to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        result_data = {
            'is_valid': result.is_valid,
            'checksum': result.checksum,
            'error': result.error,
            'is_duplicate': result.is_duplicate,
            'duplicate_path': result.duplicate_path
        }
        
        cursor.execute('''
            INSERT INTO verification_log (filepath, verification_result)
            VALUES (?, ?)
        ''', (result.filepath, json.dumps(result_data)))
        
        conn.commit()
        conn.close()
    
    def verify_content(self, filepath: str, source_url: str = None, 
                      check_duplicates: bool = True) -> VerificationResult:
        """Perform comprehensive content verification"""
        
        # Basic integrity check
        if not self.verify_file_integrity(filepath):
            result = VerificationResult(
                filepath=filepath,
                is_valid=False,
                error="File integrity check failed"
            )
            self.log_verification_result(result)
            return result
        
        # Calculate checksums
        md5_hash, sha256_hash = self.calculate_checksums(filepath)
        if not md5_hash or not sha256_hash:
            result = VerificationResult(
                filepath=filepath,
                is_valid=False,
                error="Failed to calculate checksums"
            )
            self.log_verification_result(result)
            return result
        
        # Check for duplicates if requested
        is_duplicate = False
        duplicate_path = None
        if check_duplicates:
            is_duplicate, duplicate_path = self.check_for_duplicates(
                md5_hash, sha256_hash, filepath
            )
        
        # Store verification data
        self.store_verification_data(filepath, md5_hash, sha256_hash, source_url)
        
        # Create result
        result = VerificationResult(
            filepath=filepath,
            is_valid=True,
            checksum=f"MD5: {md5_hash}, SHA256: {sha256_hash}",
            is_duplicate=is_duplicate,
            duplicate_path=duplicate_path
        )
        
        self.log_verification_result(result)
        return result
    
    def get_verification_stats(self) -> Dict:
        """Get verification statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM file_checksums')
        total_files = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM verification_log 
            WHERE json_extract(verification_result, '$.is_valid') = 1
        ''')
        valid_files = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM verification_log 
            WHERE json_extract(verification_result, '$.is_duplicate') = 1
        ''')
        duplicate_files = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_verified': total_files,
            'valid_files': valid_files,
            'duplicate_files': duplicate_files,
            'invalid_files': total_files - valid_files
        }


# Global verifier instance
_verifier_instance = None


def get_verifier(db_path: str = None) -> ContentVerifier:
    """Get or create the global verifier instance"""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = ContentVerifier(db_path)
    return _verifier_instance
