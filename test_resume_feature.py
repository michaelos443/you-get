#!/usr/bin/env python3
"""
Test script for the Download Resume and Recovery System feature.

This script demonstrates the new resume functionality added to you-get.
"""

import os
import sys
import tempfile
import time
import sqlite3

# Add the src directory to the path so we can import you_get modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from you_get.common import DownloadResumeManager, get_resume_manager

def test_resume_manager():
    """Test the basic functionality of the DownloadResumeManager."""
    print("🧪 Testing Download Resume Manager...")
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Initialize the resume manager
        manager = DownloadResumeManager(db_path)

        # Test saving download state
        test_url = "https://example.com/video.mp4"
        test_filepath = "/tmp/video.mp4"
        total_size = 1024 * 1024 * 100  # 100MB
        downloaded_size = 1024 * 1024 * 50  # 50MB

        print(f"📝 Saving download state: {downloaded_size}/{total_size} bytes")
        manager.save_download_state(test_url, test_filepath, total_size, downloaded_size)

        # Test retrieving download state
        state = manager.get_download_state(test_url, test_filepath)
        print(f"📖 Retrieved state: {state}")

        assert state is not None, "Failed to retrieve download state"
        assert state['total_size'] == total_size, "Total size mismatch"
        assert state['downloaded_size'] == downloaded_size, "Downloaded size mismatch"

        # Test marking as completed
        print("✅ Marking download as completed")
        manager.mark_completed(test_url, test_filepath)

        # Verify it's no longer active
        state_after_completion = manager.get_download_state(test_url, test_filepath)
        assert state_after_completion is None, "Download should not be active after completion"

        print("✅ All tests passed!")

    finally:
        # Clean up - add delay for Windows
        try:
            time.sleep(0.1)  # Small delay to allow file handles to close
            if os.path.exists(db_path):
                os.unlink(db_path)
        except OSError:
            pass  # Ignore cleanup errors

def test_database_schema():
    """Test that the database schema is created correctly."""
    print("\n🗄️ Testing database schema...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        manager = DownloadResumeManager(db_path)
        
        # Check if the table exists and has the correct structure
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'")
            table_exists = cursor.fetchone() is not None
            assert table_exists, "Downloads table was not created"
            
            # Check table structure
            cursor = conn.execute("PRAGMA table_info(downloads)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'url': 'TEXT',
                'filepath': 'TEXT',
                'total_size': 'INTEGER',
                'downloaded_size': 'INTEGER',
                'checksum': 'TEXT',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP',
                'status': 'TEXT',
                'retry_count': 'INTEGER',
                'metadata': 'TEXT'
            }
            
            for col_name, col_type in expected_columns.items():
                assert col_name in columns, f"Column {col_name} missing"
                print(f"✓ Column {col_name}: {columns[col_name]}")
        
        print("✅ Database schema test passed!")
        
    finally:
        try:
            time.sleep(0.1)
            if os.path.exists(db_path):
                os.unlink(db_path)
        except OSError:
            pass

def test_checksum_calculation():
    """Test checksum calculation functionality."""
    print("\n🔐 Testing checksum calculation...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as test_file:
        test_file.write("Hello, World! This is a test file for checksum calculation.")
        test_filepath = test_file.name
    
    try:
        manager = DownloadResumeManager(db_path)
        
        # Calculate checksum
        checksum = manager.calculate_checksum(test_filepath)
        print(f"📊 Calculated checksum: {checksum}")
        
        assert checksum is not None, "Checksum calculation failed"
        assert len(checksum) == 32, "MD5 checksum should be 32 characters"
        
        # Verify checksum is consistent
        checksum2 = manager.calculate_checksum(test_filepath)
        assert checksum == checksum2, "Checksum calculation is not consistent"
        
        print("✅ Checksum calculation test passed!")
        
    finally:
        try:
            time.sleep(0.1)
            if os.path.exists(db_path):
                os.unlink(db_path)
            if os.path.exists(test_filepath):
                os.unlink(test_filepath)
        except OSError:
            pass

def demonstrate_usage():
    """Demonstrate how to use the resume feature."""
    print("\n📚 Usage demonstration:")
    print("To enable download resume functionality, use the --resume flag:")
    print("  you-get --resume https://example.com/video.mp4")
    print("")
    print("Features:")
    print("  ✓ Automatic resume of interrupted downloads")
    print("  ✓ Metadata storage for partial downloads")
    print("  ✓ Corruption detection and recovery")
    print("  ✓ Smart retry logic with exponential backoff")
    print("  ✓ Download state persistence across sessions")
    print("")
    print("The resume database is stored in ~/.you-get/resume.db")

if __name__ == "__main__":
    print("🚀 Testing Download Resume and Recovery System")
    print("=" * 50)
    
    try:
        test_resume_manager()
        test_database_schema()
        test_checksum_calculation()
        demonstrate_usage()
        
        print("\n🎉 All tests completed successfully!")
        print("The Download Resume and Recovery System is ready to use!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
