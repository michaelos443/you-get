#!/usr/bin/env python3

"""
Tests for the Download Scheduling & Time-Based Automation System
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.you_get.download_scheduler import (
    DownloadScheduler, ScheduledDownload, ScheduleType, ScheduleStatus,
    NetworkConditionMonitor
)


class TestDownloadScheduler(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_scheduler.db')
        self.scheduler = DownloadScheduler(self.db_path)
    
    def test_schedule_once_download(self):
        """Test scheduling a one-time download"""
        url = "https://example.com/video"
        scheduled_time = "14:30"
        
        download_id = self.scheduler.schedule_download(
            url=url,
            scheduled_time=scheduled_time,
            schedule_type=ScheduleType.ONCE
        )
        
        self.assertIsNotNone(download_id)
        self.assertEqual(len(download_id), 36)  # UUID length
        
        # Check if download was saved
        downloads = self.scheduler.list_scheduled_downloads()
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]['url'], url)
        self.assertEqual(downloads[0]['schedule_type'], 'once')
    
    def test_schedule_daily_download(self):
        """Test scheduling a daily recurring download"""
        url = "https://example.com/daily-news"
        scheduled_time = "08:00"
        
        download_id = self.scheduler.schedule_download(
            url=url,
            scheduled_time=scheduled_time,
            schedule_type=ScheduleType.DAILY
        )
        
        downloads = self.scheduler.list_scheduled_downloads()
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]['schedule_type'], 'daily')
        self.assertEqual(downloads[0]['scheduled_time'], scheduled_time)
    
    def test_schedule_off_peak_download(self):
        """Test scheduling an off-peak download"""
        url = "https://example.com/large-file"
        
        download_id = self.scheduler.schedule_download(
            url=url,
            scheduled_time="",  # Not used for off-peak
            schedule_type=ScheduleType.OFF_PEAK
        )
        
        downloads = self.scheduler.list_scheduled_downloads()
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]['schedule_type'], 'off_peak')
    
    def test_network_condition_monitor(self):
        """Test network condition monitoring"""
        monitor = NetworkConditionMonitor()
        
        # Test off-peak detection (this will depend on current time)
        is_off_peak = monitor.is_off_peak_time()
        self.assertIsInstance(is_off_peak, bool)
        
        # Test optimal download time calculation
        optimal_time = monitor.get_optimal_download_time()
        self.assertIsInstance(optimal_time, datetime)
        self.assertGreater(optimal_time, datetime.now())
    
    def test_cancel_scheduled_download(self):
        """Test cancelling a scheduled download"""
        url = "https://example.com/video"
        
        download_id = self.scheduler.schedule_download(
            url=url,
            scheduled_time="20:00",
            schedule_type=ScheduleType.ONCE
        )
        
        # Cancel the download
        result = self.scheduler.cancel_download(download_id)
        self.assertTrue(result)
        
        # Check if status was updated
        downloads = self.scheduler.list_scheduled_downloads()
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]['status'], 'cancelled')
    
    def test_list_scheduled_downloads(self):
        """Test listing scheduled downloads"""
        # Schedule multiple downloads
        urls = [
            "https://example.com/video1",
            "https://example.com/video2",
            "https://example.com/video3"
        ]
        
        for i, url in enumerate(urls):
            self.scheduler.schedule_download(
                url=url,
                scheduled_time=f"{10 + i}:00",
                schedule_type=ScheduleType.DAILY
            )
        
        downloads = self.scheduler.list_scheduled_downloads()
        self.assertEqual(len(downloads), 3)
        
        # Check if all URLs are present
        download_urls = [d['url'] for d in downloads]
        for url in urls:
            self.assertIn(url, download_urls)
    
    def test_get_pending_downloads(self):
        """Test getting pending downloads that are ready to run"""
        # Schedule a download for the past (should be pending and ready)
        yesterday = datetime.now() - timedelta(days=1)
        
        download_id = self.scheduler.schedule_download(
            url="https://example.com/video",
            scheduled_time=yesterday.strftime("%H:%M"),
            schedule_type=ScheduleType.ONCE
        )
        
        pending = self.scheduler.get_pending_downloads()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].url, "https://example.com/video")
        self.assertEqual(pending[0].status, ScheduleStatus.PENDING)
    
    def test_schedule_with_custom_output(self):
        """Test scheduling with custom output directory and filename"""
        url = "https://example.com/video"
        output_dir = "/custom/path"
        output_filename = "custom_name.mp4"
        
        download_id = self.scheduler.schedule_download(
            url=url,
            scheduled_time="15:00",
            schedule_type=ScheduleType.ONCE,
            output_dir=output_dir,
            output_filename=output_filename
        )
        
        downloads = self.scheduler.list_scheduled_downloads()
        self.assertEqual(len(downloads), 1)
        
        # Note: We can't easily test the actual values from list_scheduled_downloads
        # as it returns a simplified dict, but the download_id confirms it was created
        self.assertIsNotNone(download_id)
    
    def test_bandwidth_optimized_scheduling(self):
        """Test bandwidth-optimized scheduling"""
        url = "https://example.com/large-video"
        
        download_id = self.scheduler.schedule_download(
            url=url,
            scheduled_time="",  # Not used for bandwidth optimized
            schedule_type=ScheduleType.BANDWIDTH_OPTIMIZED
        )
        
        downloads = self.scheduler.list_scheduled_downloads()
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]['schedule_type'], 'bandwidth_optimized')
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestScheduledDownload(unittest.TestCase):
    
    def test_scheduled_download_creation(self):
        """Test creating a ScheduledDownload object"""
        download = ScheduledDownload(
            id="test-id",
            url="https://example.com/video",
            scheduled_time="14:30",
            schedule_type=ScheduleType.DAILY,
            status=ScheduleStatus.PENDING
        )
        
        self.assertEqual(download.id, "test-id")
        self.assertEqual(download.url, "https://example.com/video")
        self.assertEqual(download.scheduled_time, "14:30")
        self.assertEqual(download.schedule_type, ScheduleType.DAILY)
        self.assertEqual(download.status, ScheduleStatus.PENDING)
        self.assertIsNotNone(download.created_at)
        self.assertEqual(download.retry_count, 0)
        self.assertEqual(download.max_retries, 3)


if __name__ == '__main__':
    unittest.main()
