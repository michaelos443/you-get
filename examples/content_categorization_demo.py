#!/usr/bin/env python3

"""
Content Categorization & Auto-Organization Demo

This demo showcases the intelligent content categorization system that automatically
organizes downloaded content into appropriate folder structures based on content analysis.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from you_get.content_categorizer import (
    ContentCategorizer, CategoryConfig, ContentCategory, ContentType
)


def demo_content_categorization():
    """Demonstrate content categorization capabilities"""
    
    print("🎯 Content Categorization & Auto-Organization Demo")
    print("=" * 60)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Demo directory: {temp_dir}")
    print()
    
    # Configure categorizer
    config = CategoryConfig(
        base_output_dir=temp_dir,
        organize_by_category=True,
        use_smart_naming=True,
        organize_by_date=False
    )
    
    categorizer = ContentCategorizer(config)
    
    # Demo content examples
    demo_content = [
        {
            'url': 'https://youtube.com/watch?v=tutorial123',
            'title': 'Python Programming Tutorial - Advanced Concepts',
            'metadata': {'duration': 1800, 'uploader': 'CodeAcademy', 'quality': 'HD'}
        },
        {
            'url': 'https://soundcloud.com/artist/song',
            'title': 'Amazing Rock Song - Official Music Video',
            'metadata': {'duration': 240, 'container': 'mp3', 'uploader': 'RockBand'}
        },
        {
            'url': 'https://twitch.tv/gamer/stream',
            'title': 'Minecraft Survival Let\'s Play - Building Epic Castle',
            'metadata': {'duration': 3600, 'uploader': 'GamerPro', 'quality': '1080p'}
        },
        {
            'url': 'https://youtube.com/watch?v=doc456',
            'title': 'The History of Space Exploration - Documentary',
            'metadata': {'duration': 5400, 'uploader': 'ScienceChannel'}
        },
        {
            'url': 'https://vimeo.com/tech789',
            'title': 'iPhone 15 Pro Review - Unboxing and First Impressions',
            'metadata': {'duration': 900, 'uploader': 'TechReviewer', 'quality': '4K'}
        }
    ]
    
    print("🔍 Analyzing and categorizing content...")
    print()
    
    for i, content in enumerate(demo_content, 1):
        print(f"📺 Content {i}: {content['title'][:50]}...")
        print(f"🔗 URL: {content['url']}")
        
        # Analyze content
        category_info = categorizer.analyze_content(
            content['url'], 
            content['title'], 
            content['metadata']
        )
        
        # Display categorization results
        print(f"📂 Category: {category_info.category.value.title()}")
        if category_info.subcategory:
            print(f"📁 Subcategory: {category_info.subcategory}")
        print(f"🎯 Confidence: {category_info.confidence:.2f}")
        print(f"🏷️  Tags: {', '.join(category_info.tags)}")
        
        # Show organization
        original_path = f"/downloads/{content['title'][:30]}.mp4"
        organized_path = categorizer.get_organized_path(original_path, category_info)
        
        print(f"📍 Original path: {original_path}")
        print(f"✨ Organized path: {organized_path}")
        
        # Create the directory structure for demo
        os.makedirs(os.path.dirname(organized_path), exist_ok=True)
        
        print("-" * 50)
        print()
    
    # Show final directory structure
    print("📁 Final Directory Structure:")
    print("=" * 30)
    
    def print_directory_tree(path, prefix=""):
        """Print directory tree structure"""
        items = sorted(os.listdir(path))
        for i, item in enumerate(items):
            item_path = os.path.join(path, item)
            is_last = i == len(items) - 1
            
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item}")
            
            if os.path.isdir(item_path):
                next_prefix = prefix + ("    " if is_last else "│   ")
                print_directory_tree(item_path, next_prefix)
    
    print_directory_tree(temp_dir)
    print()
    
    # Show usage instructions
    print("🚀 Usage Instructions:")
    print("=" * 20)
    print("To use auto-organization with you-get:")
    print("  you-get --auto-organize <URL>")
    print()
    print("To customize organization:")
    print("  you-get --auto-organize --categorize-config config.json <URL>")
    print()
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"🧹 Cleaned up demo directory: {temp_dir}")


def demo_learning_system():
    """Demonstrate the learning system"""
    print("\n🧠 Learning System Demo")
    print("=" * 25)
    
    config = CategoryConfig()
    categorizer = ContentCategorizer(config)
    
    # Simulate user feedback
    url = "https://example.com/video"
    correct_category = ContentCategory.TUTORIAL
    
    print(f"📚 Learning from user feedback...")
    print(f"🔗 URL: {url}")
    print(f"✅ Correct category: {correct_category.value}")
    
    categorizer.learn_from_user_feedback(url, correct_category)
    print("💡 Feedback recorded for future improvements!")


if __name__ == "__main__":
    try:
        demo_content_categorization()
        demo_learning_system()
        
        print("\n🎉 Demo completed successfully!")
        print("The content categorization system is ready to organize your downloads!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
