#!/usr/bin/env python

import unittest

from you_get.common import *

class TestCommon(unittest.TestCase):

    def test_match1(self):
        self.assertEqual(match1('http://youtu.be/1234567890A', r'youtu.be/([^/]+)'), '1234567890A')
        self.assertEqual(match1('http://youtu.be/1234567890A', r'youtu.be/([^/]+)', r'youtu.(\w+)'), ['1234567890A', 'be'])

    def test_match1_with_mixed_patterns(self):
        """Test match1 with multiple patterns where some don't match."""
        # Test with a pattern that doesn't match and one that does
        self.assertEqual(
            match1('http://example.com/video/1234', r'nonexistent/([^/]+)', r'video/([^/]+)'),
            [None, '1234']
        )

        # Test with a pattern that doesn't match at all
        self.assertIsNone(match1('http://example.com', r'nonexistent/([^/]+)'))

        # Test with an empty string
        self.assertIsNone(match1('', r'pattern/([^/]+)'))

    def test_matchall(self):
        """Test the matchall function with various patterns."""
        # Test with a single pattern
        text = "The price is $10, $20, and $30"
        self.assertEqual(
            matchall(text, [r'\$([0-9]+)']),
            ['10', '20', '30']
        )

        # Test with multiple patterns
        html = '<img src="image1.jpg" alt="Image 1"><img src="image2.png" alt="Image 2">'
        self.assertEqual(
            matchall(html, [r'src="([^"]+)"', r'alt="([^"]+)"']),
            ['image1.jpg', 'image2.png', 'Image 1', 'Image 2']
        )

        # Test with no matches
        self.assertEqual(matchall('No matches here', [r'nonexistent/([^/]+)']), [])
