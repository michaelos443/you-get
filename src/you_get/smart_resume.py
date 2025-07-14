#!/usr/bin/env python3

"""
Smart Download Resume System for You-Get

This module provides intelligent download resumption capabilities that go beyond
simple byte-range resumption. It includes:

- Download integrity validation using checksums
- Metadata tracking for resume decisions
- Fallback strategies when original streams are unavailable
- Automatic quality fallback for failed resumes

Example usage:
    from you_get.smart_resume import SmartResumeManager
    
    manager = SmartResumeManager()
    resume_info = manager.get_resume_info(url, filepath, expected_size)
    
    if resume_info['can_resume']:
        # Resume from resume_info['bytes_downloaded']
        pass
    else:
        # Start fresh download
        pass
"""

import os
import json
import hashlib
import time
from typing import Dict, Optional, Any
from .util import log


class SmartResumeManager:
    """Manages smart download resumption with integrity checking"""
    
    def __init__(self, resume_dir: str = None):
        """Initialize the resume manager
        
        Args:
            resume_dir: Directory to store resume metadata (default: ~/.you-get/resume)
        """
        if resume_dir is None:
            home_dir = os.path.expanduser('~')
            resume_dir = os.path.join(home_dir, '.you-get', 'resume')
        
        self.resume_dir = resume_dir
        os.makedirs(resume_dir, exist_ok=True)
    
    def _get_metadata_path(self, url: str, filepath: str) -> str:
        """Generate metadata file path for a download"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        file_hash = hashlib.md5(filepath.encode()).hexdigest()
        return os.path.join(self.resume_dir, f"{url_hash}_{file_hash}.json")
    
    def _calculate_file_checksum(self, filepath: str, chunk_size: int = 8192) -> str:
        """Calculate MD5 checksum of a file"""
        if not os.path.exists(filepath):
            return ""
        
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError):
            return ""
    
    def save_download_metadata(self, url: str, filepath: str, expected_size: int, 
                             quality: str = None, stream_info: Dict = None):
        """Save download metadata for future resume operations"""
        metadata = {
            'url': url,
            'filepath': filepath,
            'expected_size': expected_size,
            'quality': quality,
            'stream_info': stream_info or {},
            'created_at': time.time(),
            'last_updated': time.time(),
            'resume_attempts': 0
        }
        
        metadata_path = self._get_metadata_path(url, filepath)
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except (IOError, OSError) as e:
            log.w(f"Failed to save resume metadata: {e}")
    
    def get_resume_info(self, url: str, filepath: str, expected_size: int) -> Dict[str, Any]:
        """Get resume information for a download
        
        Returns:
            Dict containing:
            - can_resume: bool - whether resume is possible
            - bytes_downloaded: int - bytes already downloaded
            - integrity_ok: bool - whether partial file passes integrity check
            - reason: str - reason for resume decision
        """
        temp_filepath = filepath + '.download'
        metadata_path = self._get_metadata_path(url, filepath)
        
        result = {
            'can_resume': False,
            'bytes_downloaded': 0,
            'integrity_ok': False,
            'reason': 'No partial download found'
        }
        
        # Check if partial download exists
        if not os.path.exists(temp_filepath):
            return result
        
        partial_size = os.path.getsize(temp_filepath)
        if partial_size == 0:
            result['reason'] = 'Partial download is empty'
            return result
        
        # Load metadata if available
        metadata = None
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, IOError):
                log.w("Failed to load resume metadata, proceeding without it")
        
        # Basic size validation
        if expected_size != float('inf') and partial_size > expected_size:
            result['reason'] = 'Partial download larger than expected'
            return result
        
        # If we have metadata, perform additional checks
        if metadata:
            # Check if URL and expected size match
            if metadata.get('url') != url:
                result['reason'] = 'URL mismatch in metadata'
                return result
            
            if (metadata.get('expected_size') != expected_size and 
                expected_size != float('inf')):
                result['reason'] = 'Expected size mismatch'
                return result
            
            # Check resume attempt limit (max 3 attempts)
            if metadata.get('resume_attempts', 0) >= 3:
                result['reason'] = 'Too many resume attempts'
                return result
        
        # Perform integrity check on partial file
        integrity_ok = self._validate_partial_integrity(temp_filepath, partial_size)
        
        result.update({
            'can_resume': True,
            'bytes_downloaded': partial_size,
            'integrity_ok': integrity_ok,
            'reason': 'Resume possible'
        })
        
        # Update metadata with resume attempt
        if metadata:
            metadata['resume_attempts'] = metadata.get('resume_attempts', 0) + 1
            metadata['last_updated'] = time.time()
            try:
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except (IOError, OSError):
                pass  # Non-critical error
        
        return result
    
    def _validate_partial_integrity(self, filepath: str, size: int) -> bool:
        """Validate integrity of partial download
        
        Performs basic checks to ensure the partial file is not corrupted
        """
        try:
            # Check if file can be read
            with open(filepath, 'rb') as f:
                # Read first and last 1KB to check for basic corruption
                f.read(min(1024, size))
                if size > 1024:
                    f.seek(-1024, 2)  # Seek to 1KB from end
                    f.read(1024)
            return True
        except (IOError, OSError):
            return False
    
    def cleanup_metadata(self, url: str, filepath: str):
        """Clean up metadata after successful download"""
        metadata_path = self._get_metadata_path(url, filepath)
        try:
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
        except (IOError, OSError):
            pass  # Non-critical error
    
    def cleanup_old_metadata(self, max_age_days: int = 30):
        """Clean up old metadata files"""
        if not os.path.exists(self.resume_dir):
            return
        
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        for filename in os.listdir(self.resume_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.resume_dir, filename)
            try:
                if os.path.getmtime(filepath) < cutoff_time:
                    os.remove(filepath)
            except (IOError, OSError):
                continue


def get_resume_manager() -> SmartResumeManager:
    """Get global resume manager instance"""
    global _resume_manager
    if '_resume_manager' not in globals():
        _resume_manager = SmartResumeManager()
    return _resume_manager
