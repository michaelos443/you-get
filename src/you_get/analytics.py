#!/usr/bin/env python3

"""
Download Analytics Dashboard for You-Get

This module provides a simple web-based dashboard for visualizing download statistics
and trends. It tracks download metrics and serves a lightweight web interface.
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import urlparse, parse_qs

from .middleware import register_hook, DownloadEvent


class AnalyticsManager:
    """Manages download analytics and statistics"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.expanduser("~/.you-get/analytics.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
        self.setup_hooks()
    
    def init_database(self):
        """Initialize the analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                site TEXT,
                size_bytes INTEGER,
                duration_seconds REAL,
                speed_bytes_per_sec REAL,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_download(self, event_data):
        """Log a download event to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        data = event_data.data
        cursor.execute('''
            INSERT INTO downloads (url, title, site, size_bytes, duration_seconds, 
                                 speed_bytes_per_sec, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('url', ''),
            data.get('title', ''),
            data.get('site', ''),
            data.get('size', 0),
            data.get('duration', 0),
            data.get('speed', 0),
            data.get('status', 'completed')
        ))
        
        conn.commit()
        conn.close()
    
    def get_stats(self, days=7):
        """Get download statistics for the specified number of days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_downloads,
                SUM(size_bytes) as total_bytes,
                AVG(speed_bytes_per_sec) as avg_speed,
                AVG(duration_seconds) as avg_duration,
                site,
                DATE(timestamp) as date
            FROM downloads 
            WHERE timestamp >= datetime('now', '-{} days')
            GROUP BY site, date
            ORDER BY date DESC
        '''.format(days))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_dashboard_data(self):
        """Get data formatted for the dashboard"""
        stats = self.get_stats()
        
        sites = {}
        timeline = {}
        
        for row in stats:
            total, bytes_downloaded, avg_speed, avg_duration, site, date = row
            
            if site not in sites:
                sites[site] = {'count': 0, 'bytes': 0}
            sites[site]['count'] += total
            sites[site]['bytes'] += bytes_downloaded
            
            if date not in timeline:
                timeline[date] = {'downloads': 0, 'bytes': 0}
            timeline[date]['downloads'] += total
            timeline[date]['bytes'] += bytes_downloaded
        
        return {
            'sites': sites,
            'timeline': timeline,
            'total_downloads': sum(s['count'] for s in sites.values()),
            'total_bytes': sum(s['bytes'] for s in sites.values())
        }
    
    def setup_hooks(self):
        """Set up middleware hooks for tracking downloads"""
        @register_hook(DownloadEvent.DOWNLOAD_COMPLETE)
        def on_download_complete(event_data):
            self.log_download(event_data)


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the analytics dashboard"""
    
    def __init__(self, analytics_manager, *args, **kwargs):
        self.analytics = analytics_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/':
            self.serve_dashboard()
        elif parsed_url.path == '/api/stats':
            self.serve_stats()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = self.generate_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_stats(self):
        """Serve JSON statistics"""
        data = self.analytics.get_dashboard_data()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def generate_dashboard_html(self):
        """Generate the dashboard HTML"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>You-Get Analytics Dashboard</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .stat-card { text-align: center; padding: 20px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2196F3; }
        .chart { height: 300px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>You-Get Analytics Dashboard</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-downloads">0</div>
                <div>Total Downloads</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-bytes">0</div>
                <div>Total Data Downloaded</div>
            </div>
        </div>
        
        <div class="card">
            <h3>Downloads by Site</h3>
            <div id="sites-chart"></div>
        </div>
        
        <div class="card">
            <h3>Download Timeline</h3>
            <div id="timeline-chart"></div>
        </div>
    </div>
    
    <script>
        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-downloads').textContent = data.total_downloads;
                    document.getElementById('total-bytes').textContent = 
                        (data.total_bytes / (1024*1024*1024)).toFixed(2) + ' GB';
                });
        }
        
        loadStats();
        setInterval(loadStats, 5000);
    </script>
</body>
</html>
        '''


class DashboardServer:
    """Web server for the analytics dashboard"""
    
    def __init__(self, analytics_manager, port=8080):
        self.analytics = analytics_manager
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the dashboard server"""
        def handler(*args, **kwargs):
            return DashboardHandler(self.analytics, *args, **kwargs)
        
        self.server = HTTPServer(('localhost', self.port), handler)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        
        print(f"📊 Analytics dashboard started at http://localhost:{self.port}")
    
    def stop(self):
        """Stop the dashboard server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()


def start_dashboard(port=8080):
    """Start the analytics dashboard"""
    analytics = AnalyticsManager()
    server = DashboardServer(analytics, port)
    server.start()
    return server
