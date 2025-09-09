#!/usr/bin/env python

import unittest

from you_get.common import *

class TestCommon(unittest.TestCase):

    def test_match1(self):
        self.assertEqual(match1('http://youtu.be/1234567890A', r'youtu.be/([^/]+)'), '1234567890A')
        self.assertEqual(match1('http://youtu.be/1234567890A', r'youtu.be/([^/]+)', r'youtu.(\w+)'), ['1234567890A', 'be'])

    def test_match1_with_query_params(self):
        """Test match1 function with URLs containing query parameters."""
        # Test extracting video ID from a URL with query parameters
        self.assertEqual(
            match1('https://www.example.com/watch?v=abcDEF123&feature=related', r'watch\?v=([^&]+)'),
            'abcDEF123'
        )
        # Test extracting multiple patterns from a URL with query parameters
        self.assertEqual(
            match1(
                'https://www.example.com/video.php?id=12345&format=hd&lang=en',
                r'id=(\d+)',
                r'format=(\w+)',
                r'lang=(\w+)'
            ),
            ['12345', 'hd', 'en']
        )

    def test_match1_with_complex_patterns(self):
        """Test match1 function with more complex URL patterns."""
        # Test extracting content from HTML meta tag
        self.assertEqual(
            match1(
                '<meta property="og:title" content="Test Video Title" />',
                r'<meta property="og:title" content="([^"]+)"'
            ),
            'Test Video Title'
        )
        # Test extracting content-type charset
        self.assertEqual(
            match1(
                'Content-Type: text/html; charset=UTF-8',
                r'charset=([\w-]+)'
            ),
            'UTF-8'
        )
        # Test with no match
        self.assertIsNone(
            match1('https://example.com/page', r'video_id=(\d+)')
        )
