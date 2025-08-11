#!/usr/bin/env python3

"""
Smart Download Resume Demo

This script demonstrates the smart resume functionality of you-get.
It shows how the system can intelligently resume interrupted downloads
with integrity checking and metadata tracking.
"""

import os
import sys
import time
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.smart_resume import SmartResumeManager


def demo_smart_resume():
    """Demonstrate smart resume functionality"""
    print("🚀 You-Get Smart Download Resume Demo")
    print("=" * 50)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Demo directory: {temp_dir}")
    
    # Initialize resume manager
    resume_manager = SmartResumeManager(resume_dir=os.path.join(temp_dir, 'resume'))
    
    # Demo parameters
    demo_url = "https://example.com/large_video.mp4"
    demo_filepath = os.path.join(temp_dir, "demo_video.mp4")
    demo_size = 50000000  # 50MB
    
    print(f"\n📺 Simulating download of: {demo_url}")
    print(f"💾 Target file: {demo_filepath}")
    print(f"📏 Expected size: {demo_size:,} bytes")
    
    # Step 1: Save initial metadata
    print("\n1️⃣ Saving download metadata...")
    resume_manager.save_download_metadata(
        url=demo_url,
        filepath=demo_filepath,
        expected_size=demo_size,
        quality="1080p",
        stream_info={"format": "mp4", "codec": "h264"}
    )
    print("   ✅ Metadata saved")
    
    # Step 2: Simulate partial download
    print("\n2️⃣ Simulating partial download (30% complete)...")
    partial_filepath = demo_filepath + '.download'
    os.makedirs(os.path.dirname(partial_filepath), exist_ok=True)
    
    partial_size = int(demo_size * 0.3)  # 30% downloaded
    with open(partial_filepath, 'wb') as f:
        f.write(b'x' * partial_size)
    
    print(f"   📥 Partial file created: {partial_size:,} bytes ({partial_size/demo_size*100:.1f}%)")
    
    # Step 3: Check resume capability
    print("\n3️⃣ Checking resume capability...")
    resume_info = resume_manager.get_resume_info(demo_url, demo_filepath, demo_size)
    
    print(f"   🔍 Can resume: {resume_info['can_resume']}")
    print(f"   📊 Bytes downloaded: {resume_info['bytes_downloaded']:,}")
    print(f"   ✅ Integrity OK: {resume_info['integrity_ok']}")
    print(f"   💬 Reason: {resume_info['reason']}")
    
    if resume_info['can_resume']:
        progress = resume_info['bytes_downloaded'] / demo_size * 100
        print(f"   📈 Resume from: {progress:.1f}% complete")
    
    # Step 4: Simulate multiple resume attempts
    print("\n4️⃣ Simulating multiple resume attempts...")
    for attempt in range(1, 4):
        print(f"   🔄 Resume attempt #{attempt}")
        resume_info = resume_manager.get_resume_info(demo_url, demo_filepath, demo_size)
        if resume_info['can_resume']:
            print(f"      ✅ Resume allowed (attempt {attempt}/3)")
        else:
            print(f"      ❌ Resume blocked: {resume_info['reason']}")
            break
        time.sleep(0.1)  # Small delay for demo
    
    # Step 5: Simulate successful completion
    print("\n5️⃣ Simulating successful download completion...")
    # Rename partial file to final file
    final_filepath = demo_filepath
    os.rename(partial_filepath, final_filepath)
    print(f"   ✅ Download completed: {final_filepath}")
    
    # Clean up metadata
    resume_manager.cleanup_metadata(demo_url, demo_filepath)
    print("   🧹 Resume metadata cleaned up")
    
    # Step 6: Demonstrate cleanup of old metadata
    print("\n6️⃣ Demonstrating old metadata cleanup...")
    
    # Create some old metadata files
    old_metadata_path = os.path.join(resume_manager.resume_dir, "old_download.json")
    with open(old_metadata_path, 'w') as f:
        f.write('{"url": "https://old.example.com/video.mp4", "created_at": 1000000000}')
    
    # Set old timestamp
    old_time = time.time() - (31 * 24 * 3600)  # 31 days ago
    os.utime(old_metadata_path, (old_time, old_time))
    
    print(f"   📄 Created old metadata file: {old_metadata_path}")
    print("   🧹 Running cleanup (max age: 30 days)...")
    
    resume_manager.cleanup_old_metadata(max_age_days=30)
    
    if not os.path.exists(old_metadata_path):
        print("   ✅ Old metadata cleaned up successfully")
    else:
        print("   ❌ Old metadata cleanup failed")
    
    print(f"\n🎉 Demo completed successfully!")
    print(f"📁 Demo files created in: {temp_dir}")
    print("\n💡 Key Features Demonstrated:")
    print("   • Intelligent resume detection")
    print("   • Metadata tracking and validation")
    print("   • Resume attempt limiting")
    print("   • Integrity checking")
    print("   • Automatic cleanup")
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up demo directory: {temp_dir}")
    except:
        print(f"\n⚠️  Please manually clean up: {temp_dir}")


if __name__ == "__main__":
    demo_smart_resume()
