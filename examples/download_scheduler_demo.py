#!/usr/bin/env python3

"""
Download Scheduling & Time-Based Automation Demo

This demo showcases the intelligent download scheduling system that allows users to:
- Schedule downloads for specific times
- Set up recurring download schedules  
- Automatically download during off-peak hours
- Optimize downloads based on network conditions
"""

import os
import sys
import time
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.download_scheduler import (
    DownloadScheduler, ScheduleType, NetworkConditionMonitor
)


def demo_download_scheduling():
    """Demonstrate download scheduling capabilities"""
    
    print("⏰ Download Scheduling & Time-Based Automation Demo")
    print("=" * 60)
    
    # Initialize scheduler
    scheduler = DownloadScheduler()
    
    print("📅 Initializing download scheduler...")
    print()
    
    # Demo scheduling examples
    demo_schedules = [
        {
            'url': 'https://youtube.com/watch?v=example1',
            'time': '02:00',
            'type': ScheduleType.DAILY,
            'description': 'Daily news download at 2 AM'
        },
        {
            'url': 'https://vimeo.com/example2',
            'time': '14:30',
            'type': ScheduleType.ONCE,
            'description': 'One-time download at 2:30 PM today'
        },
        {
            'url': 'https://youtube.com/watch?v=example3',
            'time': '',
            'type': ScheduleType.OFF_PEAK,
            'description': 'Large file download during off-peak hours'
        },
        {
            'url': 'https://soundcloud.com/example4',
            'time': '09:00',
            'type': ScheduleType.WEEKLY,
            'description': 'Weekly podcast download every Monday at 9 AM'
        },
        {
            'url': 'https://youtube.com/watch?v=example5',
            'time': '',
            'type': ScheduleType.BANDWIDTH_OPTIMIZED,
            'description': 'Bandwidth-optimized download (3 AM)'
        }
    ]
    
    print("📋 Scheduling demo downloads...")
    print()
    
    scheduled_ids = []
    for i, schedule in enumerate(demo_schedules, 1):
        print(f"📺 Schedule {i}: {schedule['description']}")
        print(f"🔗 URL: {schedule['url']}")
        print(f"⏰ Time: {schedule['time'] if schedule['time'] else 'Auto-optimized'}")
        print(f"🔄 Type: {schedule['type'].value}")
        
        # Schedule the download
        download_id = scheduler.schedule_download(
            url=schedule['url'],
            scheduled_time=schedule['time'],
            schedule_type=schedule['type'],
            output_dir='./demo_downloads'
        )
        
        scheduled_ids.append(download_id)
        print(f"✅ Scheduled with ID: {download_id[:8]}...")
        print("-" * 50)
        print()
    
    # Show scheduled downloads
    print("📋 Current Scheduled Downloads:")
    print("=" * 35)
    
    downloads = scheduler.list_scheduled_downloads()
    for download in downloads:
        print(f"🆔 ID: {download['id'][:8]}...")
        print(f"🔗 URL: {download['url']}")
        print(f"📊 Status: {download['status']}")
        print(f"⏰ Next run: {download['next_run']}")
        print(f"🔄 Schedule: {download['schedule_type']} at {download['scheduled_time']}")
        print("-" * 40)
    
    print()
    
    # Demo network condition monitoring
    print("🌐 Network Condition Monitoring:")
    print("=" * 35)
    
    monitor = NetworkConditionMonitor()
    is_off_peak = monitor.is_off_peak_time()
    optimal_time = monitor.get_optimal_download_time()
    
    print(f"📊 Current time is off-peak: {'Yes' if is_off_peak else 'No'}")
    print(f"⏰ Next optimal download time: {optimal_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Demo cancellation
    print("❌ Demonstrating Download Cancellation:")
    print("=" * 40)
    
    if scheduled_ids:
        cancel_id = scheduled_ids[0]
        print(f"🗑️ Cancelling download: {cancel_id[:8]}...")
        
        if scheduler.cancel_download(cancel_id):
            print("✅ Successfully cancelled download")
        else:
            print("❌ Failed to cancel download")
        print()
    
    # Show usage instructions
    print("🚀 Usage Instructions:")
    print("=" * 20)
    print("To schedule downloads with you-get:")
    print()
    print("1. Schedule a one-time download:")
    print("   you-get --schedule 14:30 --schedule-type once <URL>")
    print()
    print("2. Schedule daily downloads:")
    print("   you-get --schedule 02:00 --schedule-type daily <URL>")
    print()
    print("3. Schedule for off-peak hours:")
    print("   you-get --schedule-type off_peak <URL>")
    print()
    print("4. Start the scheduler daemon:")
    print("   you-get --scheduler-start")
    print()
    print("5. List scheduled downloads:")
    print("   you-get --scheduler-list")
    print()
    print("6. Cancel a scheduled download:")
    print("   you-get --scheduler-cancel <ID>")
    print()


def demo_scheduler_daemon():
    """Demonstrate the scheduler daemon (brief demo)"""
    print("\n🤖 Scheduler Daemon Demo")
    print("=" * 25)
    
    scheduler = DownloadScheduler()
    
    print("🚀 Starting scheduler daemon for 10 seconds...")
    print("(In real usage, this would run continuously)")
    
    # Start daemon
    scheduler.start_daemon()
    
    # Let it run for a few seconds
    for i in range(10, 0, -1):
        print(f"⏳ Daemon running... {i} seconds remaining", end='\r')
        time.sleep(1)
    
    # Stop daemon
    scheduler.stop_daemon()
    print("\n⏹️ Daemon stopped")


def demo_time_calculations():
    """Demonstrate time calculation logic"""
    print("\n🕐 Time Calculation Demo")
    print("=" * 25)
    
    scheduler = DownloadScheduler()
    
    # Test different schedule types
    test_times = [
        ("14:30", ScheduleType.ONCE),
        ("08:00", ScheduleType.DAILY),
        ("", ScheduleType.OFF_PEAK),
        ("", ScheduleType.BANDWIDTH_OPTIMIZED)
    ]
    
    for time_str, schedule_type in test_times:
        next_run = scheduler._calculate_next_run(time_str, schedule_type)
        print(f"📅 {schedule_type.value:20} -> {next_run.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        demo_download_scheduling()
        demo_time_calculations()
        demo_scheduler_daemon()
        
        print("\n🎉 Demo completed successfully!")
        print("The download scheduling system is ready to automate your downloads!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
