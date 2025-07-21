#!/usr/bin/env python3

"""
Intelligent Content Categorization & Auto-Organization System for You-Get

This module provides automatic content categorization and organization capabilities
that analyze downloaded content using metadata, URL patterns, and content analysis
to intelligently organize files into appropriate folder structures.

Features:
- Automatic content type detection (music, documentaries, tutorials, entertainment, etc.)
- Smart folder organization based on content categories
- Intelligent file naming with metadata enrichment
- Configurable organization rules and patterns
- Integration with existing you-get download workflow

Example usage:
    from you_get.content_categorizer import ContentCategorizer, CategoryConfig
    
    categorizer = ContentCategorizer()
    
    # Analyze and categorize content
    category_info = categorizer.analyze_content(
        url='https://youtube.com/watch?v=example',
        title='Python Tutorial - Advanced Concepts',
        metadata={'duration': 1800, 'uploader': 'TechChannel'}
    )
    
    # Get organized file path
    organized_path = categorizer.get_organized_path(
        original_path='/downloads/video.mp4',
        category_info=category_info
    )
"""

import os
import re
import json
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .util import log


class ContentCategory(Enum):
    """Content category types"""
    MUSIC = "music"
    TUTORIAL = "tutorial"
    DOCUMENTARY = "documentary"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    GAMING = "gaming"
    TECH = "tech"
    EDUCATION = "education"
    SPORTS = "sports"
    LIFESTYLE = "lifestyle"
    UNKNOWN = "unknown"


class ContentType(Enum):
    """Content media types"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"


@dataclass
class CategoryInfo:
    """Information about categorized content"""
    category: ContentCategory
    content_type: ContentType
    confidence: float  # 0.0 to 1.0
    subcategory: Optional[str] = None
    tags: List[str] = None
    suggested_folder: str = ""
    suggested_filename: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CategoryConfig:
    """Configuration for content categorization"""
    base_output_dir: str = "."
    organize_by_category: bool = True
    organize_by_date: bool = False
    organize_by_source: bool = False
    use_smart_naming: bool = True
    max_filename_length: int = 100
    folder_structure_template: str = "{category}/{subcategory}"
    filename_template: str = "{title}"
    
    # Category-specific folder names
    category_folders: Dict[ContentCategory, str] = None
    
    def __post_init__(self):
        if self.category_folders is None:
            self.category_folders = {
                ContentCategory.MUSIC: "Music",
                ContentCategory.TUTORIAL: "Tutorials",
                ContentCategory.DOCUMENTARY: "Documentaries", 
                ContentCategory.ENTERTAINMENT: "Entertainment",
                ContentCategory.NEWS: "News",
                ContentCategory.GAMING: "Gaming",
                ContentCategory.TECH: "Technology",
                ContentCategory.EDUCATION: "Education",
                ContentCategory.SPORTS: "Sports",
                ContentCategory.LIFESTYLE: "Lifestyle",
                ContentCategory.UNKNOWN: "Uncategorized"
            }


class ContentCategorizer:
    """Main content categorization and organization system"""
    
    def __init__(self, config: Optional[CategoryConfig] = None):
        self.config = config or CategoryConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize categorization patterns
        self._init_patterns()
        
        # Initialize database for learning
        self._init_database()
    
    def _init_patterns(self):
        """Initialize URL and content patterns for categorization"""
        
        # URL domain patterns
        self.domain_patterns = {
            ContentCategory.MUSIC: [
                r'spotify\.com', r'soundcloud\.com', r'bandcamp\.com',
                r'music\.youtube\.com', r'apple\.com/music'
            ],
            ContentCategory.TUTORIAL: [
                r'youtube\.com.*tutorial', r'udemy\.com', r'coursera\.org',
                r'khanacademy\.org', r'edx\.org'
            ],
            ContentCategory.DOCUMENTARY: [
                r'youtube\.com.*documentary', r'vimeo\.com.*documentary',
                r'netflix\.com.*documentary'
            ],
            ContentCategory.NEWS: [
                r'cnn\.com', r'bbc\.com', r'reuters\.com', r'ap\.org',
                r'youtube\.com.*news'
            ],
            ContentCategory.GAMING: [
                r'twitch\.tv', r'youtube\.com.*gaming', r'steam\.com'
            ]
        }
        
        # Title/content patterns
        self.title_patterns = {
            ContentCategory.TUTORIAL: [
                r'tutorial', r'how to', r'guide', r'lesson', r'course',
                r'learn', r'training', r'walkthrough', r'step by step'
            ],
            ContentCategory.MUSIC: [
                r'official music video', r'lyrics', r'album', r'song',
                r'acoustic', r'live performance', r'concert'
            ],
            ContentCategory.DOCUMENTARY: [
                r'documentary', r'investigation', r'behind the scenes',
                r'history of', r'the story of'
            ],
            ContentCategory.NEWS: [
                r'breaking news', r'news update', r'report', r'interview',
                r'press conference'
            ],
            ContentCategory.GAMING: [
                r'gameplay', r'walkthrough', r'review', r'trailer',
                r'let\'s play', r'speedrun'
            ],
            ContentCategory.TECH: [
                r'review', r'unboxing', r'tech news', r'gadget',
                r'software', r'programming', r'coding'
            ]
        }
        
        # File extension patterns
        self.extension_patterns = {
            ContentType.VIDEO: ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            ContentType.AUDIO: ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
            ContentType.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            ContentType.DOCUMENT: ['.pdf', '.doc', '.docx', '.txt', '.rtf']
        }
    
    def _init_database(self):
        """Initialize SQLite database for learning user preferences"""
        db_dir = Path.home() / '.you-get'
        db_dir.mkdir(exist_ok=True)
        self.db_path = db_dir / 'categorization.db'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS categorization_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_hash TEXT NOT NULL,
                    original_title TEXT,
                    detected_category TEXT,
                    user_category TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_value TEXT NOT NULL,
                    category TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def analyze_content(self, url: str, title: str, metadata: Optional[Dict] = None) -> CategoryInfo:
        """Analyze content and determine its category"""
        if metadata is None:
            metadata = {}

        # Determine content type from file extension or metadata
        content_type = self._detect_content_type(title, metadata)

        # Analyze URL patterns
        url_category, url_confidence = self._analyze_url_patterns(url)

        # Analyze title patterns
        title_category, title_confidence = self._analyze_title_patterns(title)

        # Combine analysis results
        category, confidence = self._combine_analysis_results(
            url_category, url_confidence,
            title_category, title_confidence,
            metadata
        )

        # Generate subcategory and tags
        subcategory = self._generate_subcategory(category, title, metadata)
        tags = self._generate_tags(title, metadata)

        # Create category info
        category_info = CategoryInfo(
            category=category,
            content_type=content_type,
            confidence=confidence,
            subcategory=subcategory,
            tags=tags,
            metadata=metadata
        )

        # Generate folder and filename suggestions
        category_info.suggested_folder = self._generate_folder_path(category_info)
        category_info.suggested_filename = self._generate_filename(title, category_info)

        # Save to database for learning
        self._save_categorization_result(url, title, category_info)

        return category_info

    def _detect_content_type(self, title: str, metadata: Dict) -> ContentType:
        """Detect content type from title and metadata"""
        # Check file extension in title
        for content_type, extensions in self.extension_patterns.items():
            for ext in extensions:
                if title.lower().endswith(ext):
                    return content_type

        # Check metadata for content type hints
        if 'container' in metadata:
            container = metadata['container'].lower()
            if container in ['mp4', 'avi', 'mkv', 'mov', 'webm']:
                return ContentType.VIDEO
            elif container in ['mp3', 'wav', 'flac', 'aac', 'ogg']:
                return ContentType.AUDIO

        # Default to video for most web content
        return ContentType.VIDEO

    def _analyze_url_patterns(self, url: str) -> Tuple[ContentCategory, float]:
        """Analyze URL to determine category"""
        url_lower = url.lower()

        for category, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return category, 0.8  # High confidence for domain matches

        return ContentCategory.UNKNOWN, 0.0

    def _analyze_title_patterns(self, title: str) -> Tuple[ContentCategory, float]:
        """Analyze title to determine category"""
        title_lower = title.lower()

        category_scores = {}

        for category, patterns in self.title_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, title_lower))
                score += matches * 0.2  # Each match adds to confidence

            if score > 0:
                category_scores[category] = min(score, 0.9)  # Cap at 0.9

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category, category_scores[best_category]

        return ContentCategory.UNKNOWN, 0.0

    def _combine_analysis_results(self, url_category: ContentCategory, url_confidence: float,
                                title_category: ContentCategory, title_confidence: float,
                                metadata: Dict) -> Tuple[ContentCategory, float]:
        """Combine URL and title analysis results"""

        # If both analyses agree, increase confidence
        if url_category == title_category and url_category != ContentCategory.UNKNOWN:
            combined_confidence = min(url_confidence + title_confidence, 1.0)
            return url_category, combined_confidence

        # If only one analysis found a category, use it
        if url_category != ContentCategory.UNKNOWN and title_category == ContentCategory.UNKNOWN:
            return url_category, url_confidence
        elif title_category != ContentCategory.UNKNOWN and url_category == ContentCategory.UNKNOWN:
            return title_category, title_confidence

        # If they disagree, use the one with higher confidence
        if url_confidence > title_confidence:
            return url_category, url_confidence
        elif title_confidence > url_confidence:
            return title_category, title_confidence

        # Default to unknown
        return ContentCategory.UNKNOWN, 0.1

    def _generate_subcategory(self, category: ContentCategory, title: str, metadata: Dict) -> Optional[str]:
        """Generate subcategory based on content analysis"""
        title_lower = title.lower()

        if category == ContentCategory.TUTORIAL:
            if any(word in title_lower for word in ['python', 'programming', 'coding']):
                return "Programming"
            elif any(word in title_lower for word in ['design', 'photoshop', 'art']):
                return "Design"
            elif any(word in title_lower for word in ['cooking', 'recipe', 'kitchen']):
                return "Cooking"
            else:
                return "General"

        elif category == ContentCategory.MUSIC:
            if any(word in title_lower for word in ['rock', 'metal', 'punk']):
                return "Rock"
            elif any(word in title_lower for word in ['pop', 'mainstream']):
                return "Pop"
            elif any(word in title_lower for word in ['classical', 'orchestra', 'symphony']):
                return "Classical"
            else:
                return "General"

        elif category == ContentCategory.GAMING:
            if any(word in title_lower for word in ['minecraft', 'survival', 'building']):
                return "Sandbox"
            elif any(word in title_lower for word in ['fps', 'shooter', 'call of duty']):
                return "FPS"
            elif any(word in title_lower for word in ['rpg', 'role playing', 'adventure']):
                return "RPG"
            else:
                return "General"

        return None

    def _generate_tags(self, title: str, metadata: Dict) -> List[str]:
        """Generate tags based on content analysis"""
        tags = []
        title_lower = title.lower()

        # Common tags from title
        tag_keywords = [
            'tutorial', 'review', 'unboxing', 'gameplay', 'walkthrough',
            'documentary', 'interview', 'live', 'official', 'hd', '4k',
            'music video', 'acoustic', 'cover', 'remix'
        ]

        for keyword in tag_keywords:
            if keyword in title_lower:
                tags.append(keyword.title())

        # Add metadata-based tags
        if 'duration' in metadata:
            duration = metadata['duration']
            if duration < 300:  # 5 minutes
                tags.append('Short')
            elif duration >= 3600:  # 1 hour or more
                tags.append('Long')

        if 'uploader' in metadata:
            tags.append(f"By {metadata['uploader']}")

        return tags[:5]  # Limit to 5 tags

    def _generate_folder_path(self, category_info: CategoryInfo) -> str:
        """Generate organized folder path"""
        if not self.config.organize_by_category:
            return self.config.base_output_dir

        folder_parts = [self.config.base_output_dir]

        # Add category folder
        category_folder = self.config.category_folders.get(
            category_info.category,
            category_info.category.value.title()
        )
        folder_parts.append(category_folder)

        # Add subcategory if available
        if category_info.subcategory and self.config.folder_structure_template:
            folder_parts.append(category_info.subcategory)

        # Add date organization if enabled
        if self.config.organize_by_date:
            date_folder = datetime.now().strftime("%Y-%m")
            folder_parts.append(date_folder)

        return os.path.join(*folder_parts)

    def _generate_filename(self, original_title: str, category_info: CategoryInfo) -> str:
        """Generate smart filename with metadata enrichment"""
        if not self.config.use_smart_naming:
            return original_title

        # Clean title
        clean_title = self._clean_filename(original_title)

        # Add category prefix for certain types
        if category_info.category == ContentCategory.TUTORIAL:
            clean_title = f"[Tutorial] {clean_title}"
        elif category_info.category == ContentCategory.DOCUMENTARY:
            clean_title = f"[Documentary] {clean_title}"

        # Add quality/format info if available
        if category_info.metadata:
            if 'quality' in category_info.metadata:
                quality = category_info.metadata['quality']
                if quality and quality not in clean_title.lower():
                    clean_title = f"{clean_title} [{quality}]"

        # Truncate if too long
        if len(clean_title) > self.config.max_filename_length:
            clean_title = clean_title[:self.config.max_filename_length-3] + "..."

        return clean_title

    def _clean_filename(self, filename: str) -> str:
        """Clean filename by removing invalid characters"""
        # Remove invalid characters for filesystem
        invalid_chars = r'[<>:"/\\|?*]'
        clean_name = re.sub(invalid_chars, '', filename)

        # Replace multiple spaces with single space
        clean_name = re.sub(r'\s+', ' ', clean_name)

        # Remove leading/trailing whitespace
        clean_name = clean_name.strip()

        return clean_name

    def get_organized_path(self, original_path: str, category_info: CategoryInfo) -> str:
        """Get the organized file path based on categorization"""
        original_file = Path(original_path)

        # Generate new folder path
        new_folder = category_info.suggested_folder

        # Generate new filename
        new_filename = category_info.suggested_filename
        if not new_filename:
            new_filename = original_file.stem

        # Preserve original extension
        new_filename_with_ext = f"{new_filename}{original_file.suffix}"

        # Create full path
        new_path = os.path.join(new_folder, new_filename_with_ext)

        return new_path

    def _save_categorization_result(self, url: str, title: str, category_info: CategoryInfo):
        """Save categorization result to database for learning"""
        url_hash = hashlib.md5(url.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO categorization_history
                (url_hash, original_title, detected_category, confidence, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                url_hash, title, category_info.category.value,
                category_info.confidence, json.dumps(category_info.metadata)
            ))
            conn.commit()

    def learn_from_user_feedback(self, url: str, correct_category: ContentCategory):
        """Learn from user feedback to improve categorization"""
        url_hash = hashlib.md5(url.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            # Update the categorization history with user feedback
            conn.execute('''
                UPDATE categorization_history
                SET user_category = ?
                WHERE url_hash = ?
            ''', (correct_category.value, url_hash))

            conn.commit()

        log.i(f"Learned from feedback: {url} -> {correct_category.value}")


# Global categorizer instance
_categorizer_instance = None

def get_categorizer(config: Optional[CategoryConfig] = None) -> ContentCategorizer:
    """Get global categorizer instance"""
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = ContentCategorizer(config)
    return _categorizer_instance
