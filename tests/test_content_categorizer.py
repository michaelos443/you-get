#!/usr/bin/env python3

"""
Tests for the Content Categorization & Auto-Organization System
"""

import unittest
import tempfile
import os
from pathlib import Path

from src.you_get.content_categorizer import (
    ContentCategorizer, CategoryConfig, ContentCategory, ContentType, CategoryInfo
)


class TestContentCategorizer(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = CategoryConfig(base_output_dir=self.temp_dir)
        self.categorizer = ContentCategorizer(self.config)
    
    def test_tutorial_categorization(self):
        """Test tutorial content categorization"""
        url = "https://youtube.com/watch?v=example"
        title = "Python Tutorial - Advanced Concepts"
        metadata = {'duration': 1800, 'uploader': 'TechChannel'}
        
        category_info = self.categorizer.analyze_content(url, title, metadata)
        
        self.assertEqual(category_info.category, ContentCategory.TUTORIAL)
        self.assertEqual(category_info.subcategory, "Programming")
        self.assertGreater(category_info.confidence, 0.0)
        self.assertIn("Tutorial", category_info.tags)
    
    def test_music_categorization(self):
        """Test music content categorization"""
        url = "https://soundcloud.com/artist/song"
        title = "Amazing Song - Official Music Video"
        metadata = {'duration': 240, 'container': 'mp3'}
        
        category_info = self.categorizer.analyze_content(url, title, metadata)
        
        self.assertEqual(category_info.category, ContentCategory.MUSIC)
        self.assertGreater(category_info.confidence, 0.0)
        self.assertIn("Official", category_info.tags)
    
    def test_gaming_categorization(self):
        """Test gaming content categorization"""
        url = "https://twitch.tv/streamer"
        title = "Minecraft Survival Let's Play Episode 1"
        metadata = {'duration': 3600}
        
        category_info = self.categorizer.analyze_content(url, title, metadata)
        
        self.assertEqual(category_info.category, ContentCategory.GAMING)
        self.assertEqual(category_info.subcategory, "Sandbox")
        self.assertIn("Long", category_info.tags)
    
    def test_folder_organization(self):
        """Test folder path generation"""
        category_info = CategoryInfo(
            category=ContentCategory.TUTORIAL,
            content_type=ContentType.VIDEO,
            confidence=0.8,
            subcategory="Programming"
        )
        
        folder_path = self.categorizer._generate_folder_path(category_info)
        expected_path = os.path.join(self.temp_dir, "Tutorials", "Programming")
        
        self.assertEqual(folder_path, expected_path)
    
    def test_filename_generation(self):
        """Test smart filename generation"""
        category_info = CategoryInfo(
            category=ContentCategory.TUTORIAL,
            content_type=ContentType.VIDEO,
            confidence=0.8,
            metadata={'quality': 'HD'}
        )
        
        original_title = "Python Advanced Tutorial"
        filename = self.categorizer._generate_filename(original_title, category_info)
        
        self.assertIn("[Tutorial]", filename)
        self.assertIn("Python Advanced Tutorial", filename)
        self.assertIn("[HD]", filename)
    
    def test_organized_path_generation(self):
        """Test complete organized path generation"""
        category_info = CategoryInfo(
            category=ContentCategory.MUSIC,
            content_type=ContentType.AUDIO,
            confidence=0.9,
            suggested_folder=os.path.join(self.temp_dir, "Music"),
            suggested_filename="Great Song"
        )
        
        original_path = "/downloads/video.mp4"
        organized_path = self.categorizer.get_organized_path(original_path, category_info)
        
        expected_path = os.path.join(self.temp_dir, "Music", "Great Song.mp4")
        self.assertEqual(organized_path, expected_path)
    
    def test_content_type_detection(self):
        """Test content type detection"""
        # Test video detection
        video_type = self.categorizer._detect_content_type("video.mp4", {})
        self.assertEqual(video_type, ContentType.VIDEO)
        
        # Test audio detection
        audio_type = self.categorizer._detect_content_type("song.mp3", {})
        self.assertEqual(audio_type, ContentType.AUDIO)
        
        # Test metadata-based detection
        metadata_type = self.categorizer._detect_content_type("file", {'container': 'webm'})
        self.assertEqual(metadata_type, ContentType.VIDEO)
    
    def test_unknown_category_fallback(self):
        """Test fallback to unknown category"""
        url = "https://unknown-site.com/content"
        title = "Random Content Without Clear Category"
        
        category_info = self.categorizer.analyze_content(url, title)
        
        self.assertEqual(category_info.category, ContentCategory.UNKNOWN)
        self.assertLessEqual(category_info.confidence, 0.1)
    
    def test_filename_cleaning(self):
        """Test filename cleaning functionality"""
        dirty_filename = 'Video<>:"/\\|?*Title'
        clean_filename = self.categorizer._clean_filename(dirty_filename)
        
        self.assertEqual(clean_filename, "VideoTitle")
        self.assertNotIn('<', clean_filename)
        self.assertNotIn('>', clean_filename)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
