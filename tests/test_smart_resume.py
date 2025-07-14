#!/usr/bin/env python3

import unittest
import tempfile
import os
import json
import time
from unittest.mock import patch, MagicMock

# Add src to path for testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.smart_resume import SmartResumeManager


class TestSmartResumeManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.resume_manager = SmartResumeManager(resume_dir=self.temp_dir)
        self.test_url = "https://example.com/video.mp4"
        self.test_filepath = "/tmp/test_video.mp4"
        self.test_size = 1000000  # 1MB
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_metadata_path_generation(self):
        """Test metadata file path generation"""
        path = self.resume_manager._get_metadata_path(self.test_url, self.test_filepath)
        self.assertTrue(path.startswith(self.temp_dir))
        self.assertTrue(path.endswith('.json'))
    
    def test_save_and_load_metadata(self):
        """Test saving and loading download metadata"""
        # Save metadata
        self.resume_manager.save_download_metadata(
            self.test_url, self.test_filepath, self.test_size, 
            quality="720p", stream_info={"format": "mp4"}
        )
        
        # Check if metadata file was created
        metadata_path = self.resume_manager._get_metadata_path(self.test_url, self.test_filepath)
        self.assertTrue(os.path.exists(metadata_path))
        
        # Load and verify metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.assertEqual(metadata['url'], self.test_url)
        self.assertEqual(metadata['filepath'], self.test_filepath)
        self.assertEqual(metadata['expected_size'], self.test_size)
        self.assertEqual(metadata['quality'], "720p")
        self.assertEqual(metadata['stream_info']['format'], "mp4")
    
    def test_resume_info_no_partial_file(self):
        """Test resume info when no partial file exists"""
        resume_info = self.resume_manager.get_resume_info(
            self.test_url, self.test_filepath, self.test_size
        )
        
        self.assertFalse(resume_info['can_resume'])
        self.assertEqual(resume_info['bytes_downloaded'], 0)
        self.assertEqual(resume_info['reason'], 'No partial download found')
    
    def test_resume_info_with_partial_file(self):
        """Test resume info with existing partial file"""
        # Create a partial download file
        temp_filepath = self.test_filepath + '.download'
        os.makedirs(os.path.dirname(temp_filepath), exist_ok=True)
        
        partial_data = b"test data" * 1000  # 9KB
        with open(temp_filepath, 'wb') as f:
            f.write(partial_data)
        
        # Save metadata
        self.resume_manager.save_download_metadata(
            self.test_url, self.test_filepath, self.test_size
        )
        
        resume_info = self.resume_manager.get_resume_info(
            self.test_url, self.test_filepath, self.test_size
        )
        
        self.assertTrue(resume_info['can_resume'])
        self.assertEqual(resume_info['bytes_downloaded'], len(partial_data))
        self.assertTrue(resume_info['integrity_ok'])
        
        # Clean up
        os.remove(temp_filepath)
    
    def test_resume_info_oversized_partial_file(self):
        """Test resume info when partial file is larger than expected"""
        # Create a partial download file larger than expected
        temp_filepath = self.test_filepath + '.download'
        os.makedirs(os.path.dirname(temp_filepath), exist_ok=True)
        
        oversized_data = b"x" * (self.test_size + 1000)  # Larger than expected
        with open(temp_filepath, 'wb') as f:
            f.write(oversized_data)
        
        resume_info = self.resume_manager.get_resume_info(
            self.test_url, self.test_filepath, self.test_size
        )
        
        self.assertFalse(resume_info['can_resume'])
        self.assertEqual(resume_info['reason'], 'Partial download larger than expected')
        
        # Clean up
        os.remove(temp_filepath)
    
    def test_resume_attempts_limit(self):
        """Test that resume attempts are limited"""
        # Create a partial download file
        temp_filepath = self.test_filepath + '.download'
        os.makedirs(os.path.dirname(temp_filepath), exist_ok=True)
        
        with open(temp_filepath, 'wb') as f:
            f.write(b"test data")
        
        # Save metadata with high resume attempts
        metadata_path = self.resume_manager._get_metadata_path(self.test_url, self.test_filepath)
        metadata = {
            'url': self.test_url,
            'filepath': self.test_filepath,
            'expected_size': self.test_size,
            'resume_attempts': 3,  # At limit
            'created_at': time.time(),
            'last_updated': time.time()
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        resume_info = self.resume_manager.get_resume_info(
            self.test_url, self.test_filepath, self.test_size
        )
        
        self.assertFalse(resume_info['can_resume'])
        self.assertEqual(resume_info['reason'], 'Too many resume attempts')
        
        # Clean up
        os.remove(temp_filepath)
    
    def test_cleanup_metadata(self):
        """Test metadata cleanup after successful download"""
        # Save metadata
        self.resume_manager.save_download_metadata(
            self.test_url, self.test_filepath, self.test_size
        )
        
        metadata_path = self.resume_manager._get_metadata_path(self.test_url, self.test_filepath)
        self.assertTrue(os.path.exists(metadata_path))
        
        # Clean up metadata
        self.resume_manager.cleanup_metadata(self.test_url, self.test_filepath)
        self.assertFalse(os.path.exists(metadata_path))
    
    def test_cleanup_old_metadata(self):
        """Test cleanup of old metadata files"""
        # Create old metadata file
        old_metadata_path = os.path.join(self.temp_dir, "old_metadata.json")
        with open(old_metadata_path, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Set modification time to 31 days ago
        old_time = time.time() - (31 * 24 * 3600)
        os.utime(old_metadata_path, (old_time, old_time))
        
        # Create recent metadata file
        recent_metadata_path = os.path.join(self.temp_dir, "recent_metadata.json")
        with open(recent_metadata_path, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Run cleanup
        self.resume_manager.cleanup_old_metadata(max_age_days=30)
        
        # Check results
        self.assertFalse(os.path.exists(old_metadata_path))
        self.assertTrue(os.path.exists(recent_metadata_path))


if __name__ == '__main__':
    unittest.main()
