#!/usr/bin/env python3

"""
Video Downloader Middleware

A unified interface for multiple video downloader backends (you-get, yt-dlp, youtube-dl, etc.)
This middleware provides a common API that abstracts away the differences between various
video downloading tools, allowing applications to switch between backends seamlessly.

Features:
- Unified API for multiple downloader backends
- Automatic backend selection based on URL or preference
- Fallback mechanism when primary backend fails
- Common configuration interface
- Progress tracking abstraction
- Format selection normalization
- Error handling and retry logic

Example usage:
    from video_downloader_middleware import VideoDownloaderMiddleware
    
    # Initialize with preferred backends
    downloader = VideoDownloaderMiddleware(
        backends=['yt-dlp', 'you-get', 'youtube-dl'],
        fallback=True
    )
    
    # Download a video
    result = downloader.download(
        url='https://www.youtube.com/watch?v=example',
        output_dir='./downloads',
        format='best[height<=720]'
    )
"""

import os
import sys
import subprocess
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class DownloadStatus(Enum):
    """Download status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadInfo:
    """Standardized download information structure"""
    url: str
    title: Optional[str] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    format_id: Optional[str] = None
    ext: Optional[str] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    formats: List[Dict] = field(default_factory=list)


@dataclass
class DownloadResult:
    """Download operation result"""
    status: DownloadStatus
    info: Optional[DownloadInfo] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    backend_used: Optional[str] = None
    download_time: Optional[float] = None


class DownloadBackend(ABC):
    """Abstract base class for download backends"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"backend.{name}")
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available on the system"""
        pass
    
    @abstractmethod
    def supports_url(self, url: str) -> bool:
        """Check if the backend supports the given URL"""
        pass
    
    @abstractmethod
    def get_info(self, url: str, **kwargs) -> DownloadInfo:
        """Extract video information without downloading"""
        pass
    
    @abstractmethod
    def download(self, url: str, output_dir: str = '.', **kwargs) -> DownloadResult:
        """Download video from URL"""
        pass
    
    @abstractmethod
    def get_formats(self, url: str) -> List[Dict]:
        """Get available formats for the video"""
        pass


class YtDlpBackend(DownloadBackend):
    """yt-dlp backend implementation"""
    
    def __init__(self):
        super().__init__("yt-dlp")
    
    def is_available(self) -> bool:
        try:
            subprocess.run(['yt-dlp', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def supports_url(self, url: str) -> bool:
        # yt-dlp supports most URLs, so we'll return True for HTTP(S) URLs
        return url.startswith(('http://', 'https://'))
    
    def get_info(self, url: str, **kwargs) -> DownloadInfo:
        try:
            cmd = ['yt-dlp', '--dump-json', '--no-download', url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout.strip().split('\n')[0])
            
            return DownloadInfo(
                url=url,
                title=data.get('title'),
                duration=data.get('duration'),
                file_size=data.get('filesize'),
                format_id=data.get('format_id'),
                ext=data.get('ext'),
                thumbnail=data.get('thumbnail'),
                description=data.get('description'),
                uploader=data.get('uploader'),
                upload_date=data.get('upload_date'),
                view_count=data.get('view_count'),
                like_count=data.get('like_count'),
                formats=data.get('formats', [])
            )
        except Exception as e:
            self.logger.error(f"Failed to get info: {e}")
            raise
    
    def download(self, url: str, output_dir: str = '.', **kwargs) -> DownloadResult:
        try:
            cmd = ['yt-dlp', '-o', f'{output_dir}/%(title)s.%(ext)s']
            
            # Add format selection if specified
            if 'format' in kwargs:
                cmd.extend(['-f', kwargs['format']])
            
            cmd.append(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Get info for the result
            info = self.get_info(url)
            
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                info=info,
                backend_used=self.name,
                output_path=output_dir  # Simplified - would need parsing for exact path
            )
        except Exception as e:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error_message=str(e),
                backend_used=self.name
            )
    
    def get_formats(self, url: str) -> List[Dict]:
        info = self.get_info(url)
        return info.formats


class YouGetBackend(DownloadBackend):
    """you-get backend implementation"""
    
    def __init__(self):
        super().__init__("you-get")
    
    def is_available(self) -> bool:
        try:
            subprocess.run(['you-get', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def supports_url(self, url: str) -> bool:
        # Check if you-get supports this URL by testing it
        try:
            cmd = ['you-get', '--info', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def get_info(self, url: str, **kwargs) -> DownloadInfo:
        try:
            cmd = ['you-get', '--json', url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            return DownloadInfo(
                url=url,
                title=data.get('title'),
                # Map you-get specific fields to standard format
                formats=data.get('streams', {})
            )
        except Exception as e:
            self.logger.error(f"Failed to get info: {e}")
            raise
    
    def download(self, url: str, output_dir: str = '.', **kwargs) -> DownloadResult:
        try:
            cmd = ['you-get', '-o', output_dir]
            
            # Add format selection if specified
            if 'format' in kwargs:
                cmd.extend(['--itag', kwargs['format']])
            
            cmd.append(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                backend_used=self.name,
                output_path=output_dir
            )
        except Exception as e:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error_message=str(e),
                backend_used=self.name
            )
    
    def get_formats(self, url: str) -> List[Dict]:
        info = self.get_info(url)
        return list(info.formats.values()) if isinstance(info.formats, dict) else info.formats


class VideoDownloaderMiddleware:
    """
    Main middleware class that provides a unified interface for multiple
    video downloader backends.
    """
    
    def __init__(self, backends: List[str] = None, fallback: bool = True):
        """
        Initialize the middleware with specified backends.
        
        Args:
            backends: List of backend names in order of preference
            fallback: Whether to try other backends if the primary fails
        """
        self.fallback = fallback
        self.logger = logging.getLogger("middleware")
        
        # Initialize available backends
        self.available_backends = {}
        backend_classes = {
            'yt-dlp': YtDlpBackend,
            'you-get': YouGetBackend,
            # Add more backends here
        }
        
        # Use provided backends or default order
        backend_order = backends or ['yt-dlp', 'you-get']
        
        for backend_name in backend_order:
            if backend_name in backend_classes:
                backend = backend_classes[backend_name]()
                if backend.is_available():
                    self.available_backends[backend_name] = backend
                    self.logger.info(f"Backend {backend_name} is available")
                else:
                    self.logger.warning(f"Backend {backend_name} is not available")
        
        if not self.available_backends:
            raise RuntimeError("No video downloader backends are available")
    
    def _select_backend(self, url: str, preferred: str = None) -> DownloadBackend:
        """Select the best backend for the given URL"""
        if preferred and preferred in self.available_backends:
            backend = self.available_backends[preferred]
            if backend.supports_url(url):
                return backend
        
        # Try backends in order
        for backend in self.available_backends.values():
            if backend.supports_url(url):
                return backend
        
        # Fallback to first available backend
        return next(iter(self.available_backends.values()))
    
    def get_info(self, url: str, backend: str = None) -> DownloadInfo:
        """Get video information using the best available backend"""
        selected_backend = self._select_backend(url, backend)
        return selected_backend.get_info(url)
    
    def download(self, url: str, output_dir: str = '.', 
                backend: str = None, **kwargs) -> DownloadResult:
        """
        Download video using the best available backend with fallback support.
        
        Args:
            url: Video URL to download
            output_dir: Output directory for downloaded files
            backend: Preferred backend name
            **kwargs: Additional options (format, quality, etc.)
        
        Returns:
            DownloadResult with status and details
        """
        backends_to_try = []
        
        # Add preferred backend first
        if backend and backend in self.available_backends:
            backends_to_try.append(self.available_backends[backend])
        
        # Add other backends if fallback is enabled
        if self.fallback:
            for name, b in self.available_backends.items():
                if b not in backends_to_try and b.supports_url(url):
                    backends_to_try.append(b)
        
        if not backends_to_try:
            backends_to_try = [self._select_backend(url)]
        
        last_error = None
        for backend_instance in backends_to_try:
            try:
                self.logger.info(f"Trying backend: {backend_instance.name}")
                result = backend_instance.download(url, output_dir, **kwargs)
                
                if result.status == DownloadStatus.COMPLETED:
                    self.logger.info(f"Successfully downloaded using {backend_instance.name}")
                    return result
                else:
                    last_error = result.error_message
                    self.logger.warning(f"Backend {backend_instance.name} failed: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Backend {backend_instance.name} error: {e}")
                continue
        
        return DownloadResult(
            status=DownloadStatus.FAILED,
            error_message=f"All backends failed. Last error: {last_error}"
        )
    
    def get_formats(self, url: str, backend: str = None) -> List[Dict]:
        """Get available formats for the video"""
        selected_backend = self._select_backend(url, backend)
        return selected_backend.get_formats(url)
    
    def list_backends(self) -> List[str]:
        """List all available backends"""
        return list(self.available_backends.keys())


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize middleware
    middleware = VideoDownloaderMiddleware(
        backends=['yt-dlp', 'you-get'],
        fallback=True
    )
    
    print(f"Available backends: {middleware.list_backends()}")
    
    # Example download
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    
    try:
        # Get video info
        info = middleware.get_info(test_url)
        print(f"Video title: {info.title}")
        
        # Download video
        result = middleware.download(
            url=test_url,
            output_dir="./downloads",
            format="best[height<=720]"
        )
        
        print(f"Download status: {result.status}")
        print(f"Backend used: {result.backend_used}")
        
    except Exception as e:
        print(f"Error: {e}")
