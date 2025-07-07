#!/usr/bin/env python3

"""
Demo script showing the Smart Retry feature for You-Get
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def demo_smart_retry():
    """Demonstrate the smart retry feature"""
    
    print("🎬 You-Get Smart Retry Feature Demo")
    print("=" * 50)
    
    print("\n📋 Available Commands:")
    print("   --smart-retry          : Retry failed downloads with exponential backoff")
    print("   --max-retries N        : Set maximum retry attempts (default: 3)")
    print("   --history              : Show download history")
    print("   --failed-downloads     : Show only failed downloads")
    print("   --smart-resume         : Resume interrupted downloads")
    
    print("\n🔧 How Smart Retry Works:")
    print("   1. Identifies failed downloads from history")
    print("   2. Uses exponential backoff (1s, 2s, 4s, 8s...)")
    print("   3. Adds random jitter to prevent server overload")
    print("   4. Respects maximum retry limits")
    print("   5. Tracks retry attempts and success rates")
    
    print("\n💡 Example Usage:")
    print("   python you-get --smart-retry")
    print("   python you-get --smart-retry --max-retries 5")
    print("   python you-get --history")
    print("   python you-get --failed-downloads")
    
    print("\n🚀 Benefits:")
    print("   ✅ Automatic recovery from temporary failures")
    print("   ✅ Intelligent backoff prevents server overload")
    print("   ✅ Detailed statistics and progress tracking")
    print("   ✅ Configurable retry limits")
    print("   ✅ Integrates with existing download history")
    
    print("\n📊 Sample Output:")
    print("   🔄 Starting smart retry for failed downloads...")
    print("   🔄 Retrying download (attempt 1/3): Example Video")
    print("      URL: https://example.com/video.mp4")
    print("      ✅ Retry successful, queued for download")
    print("   ✅ Smart retry completed:")
    print("      - Total failed downloads: 5")
    print("      - Retry attempts made: 3")
    print("      - Successful retries: 2")
    print("      - Failed retries: 1")
    print("      - Skipped (max retries exceeded): 2")
    
    print("\n🎯 This feature enhances You-Get's reliability by:")
    print("   • Automatically handling temporary network issues")
    print("   • Reducing manual intervention for failed downloads")
    print("   • Providing intelligent retry strategies")
    print("   • Maintaining comprehensive download history")

if __name__ == '__main__':
    demo_smart_retry()
