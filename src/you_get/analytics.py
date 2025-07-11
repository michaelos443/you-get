#!/usr/bin/env python3

"""
Download Analytics and Insights Dashboard for You-Get

This module provides comprehensive analytics and insights about download patterns,
usage statistics, and performance metrics. It integrates with the download history
to provide meaningful data visualization and reporting.

Features:
- Download pattern analysis (time-based, site-based, format-based)
- Bandwidth usage tracking and optimization suggestions
- Popular content and site analytics
- Performance metrics and trends
- Export capabilities for reports
- Interactive CLI dashboard

Example usage:
    from you_get.analytics import AnalyticsDashboard
    
    dashboard = AnalyticsDashboard()
    
    # Get comprehensive analytics
    insights = dashboard.get_insights()
    
    # Display interactive dashboard
    dashboard.show_dashboard()
    
    # Export analytics report
    dashboard.export_report('analytics_report.json')
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, Counter
import statistics
from urllib.parse import urlparse

from .download_history import DownloadHistoryManager, DownloadRecord
from .util import log


@dataclass
class AnalyticsInsight:
    """Represents a single analytics insight"""
    category: str
    title: str
    value: Any
    description: str
    trend: Optional[str] = None  # 'up', 'down', 'stable'
    recommendation: Optional[str] = None


@dataclass
class DownloadPattern:
    """Represents download patterns and trends"""
    hourly_distribution: Dict[int, int]
    daily_distribution: Dict[str, int]
    monthly_distribution: Dict[str, int]
    site_distribution: Dict[str, int]
    format_distribution: Dict[str, int]
    quality_distribution: Dict[str, int]


class AnalyticsDashboard:
    """Comprehensive analytics dashboard for download insights"""

    def __init__(self, history_manager: Optional[DownloadHistoryManager] = None):
        """Initialize the analytics dashboard
        
        Args:
            history_manager: Optional history manager instance
        """
        self.history_manager = history_manager or DownloadHistoryManager()
        self._cache = {}
        self._cache_expiry = {}

    def _get_cached_or_compute(self, key: str, compute_func, cache_duration_minutes: int = 30):
        """Get cached result or compute new one"""
        now = datetime.now()
        
        if (key in self._cache and 
            key in self._cache_expiry and 
            now < self._cache_expiry[key]):
            return self._cache[key]
        
        result = compute_func()
        self._cache[key] = result
        self._cache_expiry[key] = now + timedelta(minutes=cache_duration_minutes)
        return result

    def get_download_patterns(self, days_back: int = 30) -> DownloadPattern:
        """Analyze download patterns over specified period"""
        
        def compute_patterns():
            # Get recent download history
            records = self.history_manager.get_download_history(limit=10000)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_records = [
                r for r in records 
                if datetime.fromisoformat(r.download_date) >= cutoff_date
            ]
            
            # Initialize distributions
            hourly_dist = defaultdict(int)
            daily_dist = defaultdict(int)
            monthly_dist = defaultdict(int)
            site_dist = defaultdict(int)
            format_dist = defaultdict(int)
            quality_dist = defaultdict(int)
            
            for record in recent_records:
                dt = datetime.fromisoformat(record.download_date)
                
                # Hourly distribution
                hourly_dist[dt.hour] += 1
                
                # Daily distribution
                daily_dist[dt.strftime('%A')] += 1
                
                # Monthly distribution
                monthly_dist[dt.strftime('%Y-%m')] += 1
                
                # Site distribution
                try:
                    domain = urlparse(record.url).netloc
                    site_dist[domain] += 1
                except:
                    site_dist['unknown'] += 1
                
                # Format distribution
                if record.format:
                    format_dist[record.format] += 1
                
                # Quality distribution
                if record.quality:
                    quality_dist[record.quality] += 1
            
            return DownloadPattern(
                hourly_distribution=dict(hourly_dist),
                daily_distribution=dict(daily_dist),
                monthly_distribution=dict(monthly_dist),
                site_distribution=dict(site_dist),
                format_distribution=dict(format_dist),
                quality_distribution=dict(quality_dist)
            )
        
        return self._get_cached_or_compute('download_patterns', compute_patterns)

    def show_dashboard(self, days_back: int = 30):
        """Display interactive analytics dashboard in CLI"""
        print("\n" + "="*60)
        print("🎯 YOU-GET ANALYTICS DASHBOARD")
        print("="*60)
        
        # Get data
        patterns = self.get_download_patterns(days_back)
        
        print(f"\n📊 DOWNLOAD PATTERNS (Last {days_back} days)")
        print("-" * 40)
        
        # Top sites
        if patterns.site_distribution:
            print("Top Sites:")
            sorted_sites = sorted(patterns.site_distribution.items(), key=lambda x: x[1], reverse=True)
            for site, count in sorted_sites[:5]:
                print(f"  • {site}: {count} downloads")
        
        print("\n" + "="*60)

    def export_report(self, filepath: str, days_back: int = 30):
        """Export comprehensive analytics report to JSON"""
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period_days': days_back,
            'patterns': asdict(self.get_download_patterns(days_back))
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Analytics report exported to: {filepath}")


# Global analytics instance
_analytics_dashboard = None

def get_analytics_dashboard() -> AnalyticsDashboard:
    """Get the global analytics dashboard instance"""
    global _analytics_dashboard
    if _analytics_dashboard is None:
        _analytics_dashboard = AnalyticsDashboard()
    return _analytics_dashboard