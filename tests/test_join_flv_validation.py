#!/usr/bin/env python

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import tempfile
import io

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from you_get.processor.join_flv import (
    validate_flv,
    concat_flv,
    read_flv_header,
    read_tag,
    read_meta_tag
)


class TestJoinFLVValidation(unittest.TestCase):
    """Test cases for the validation functions in join_flv.py module."""

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_flv_nonexistent_file(self, mock_open, mock_getsize, mock_exists):
        """Test validate_flv with a nonexistent file."""
        mock_exists.return_value = False
        
        result, meta = validate_flv('nonexistent.flv')
        
        self.assertFalse(result)
        self.assertIsNone(meta)
        mock_open.assert_not_called()

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_flv_too_small_file(self, mock_open, mock_getsize, mock_exists):
        """Test validate_flv with a file that's too small."""
        mock_exists.return_value = True
        mock_getsize.return_value = 5  # Less than minimum FLV header size
        
        result, meta = validate_flv('small.flv')
        
        self.assertFalse(result)
        self.assertIsNone(meta)
        mock_open.assert_not_called()

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('you_get.processor.join_flv.read_flv_header')
    @patch('builtins.open')
    def test_validate_flv_invalid_header(self, mock_open, mock_read_header, mock_getsize, mock_exists):
        """Test validate_flv with a file that has an invalid header."""
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        mock_read_header.return_value = False
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result, meta = validate_flv('invalid_header.flv')
        
        self.assertFalse(result)
        self.assertIsNone(meta)
        mock_read_header.assert_called_once_with(mock_file)

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('you_get.processor.join_flv.read_flv_header')
    @patch('you_get.processor.join_flv.read_tag')
    @patch('builtins.open')
    def test_validate_flv_no_meta_tag(self, mock_open, mock_read_tag, mock_read_header, mock_getsize, mock_exists):
        """Test validate_flv with a file that has no metadata tag."""
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        mock_read_header.return_value = True
        mock_read_tag.return_value = None
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result, meta = validate_flv('no_meta.flv')
        
        self.assertFalse(result)
        self.assertIsNone(meta)
        mock_read_tag.assert_called_once_with(mock_file)

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('you_get.processor.join_flv.read_flv_header')
    @patch('you_get.processor.join_flv.read_tag')
    @patch('you_get.processor.join_flv.read_meta_tag')
    @patch('builtins.open')
    def test_validate_flv_invalid_meta(self, mock_open, mock_read_meta, mock_read_tag, 
                                      mock_read_header, mock_getsize, mock_exists):
        """Test validate_flv with a file that has invalid metadata."""
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        mock_read_header.return_value = True
        mock_read_tag.return_value = 'tag'
        mock_read_meta.return_value = None
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result, meta = validate_flv('invalid_meta.flv')
        
        self.assertFalse(result)
        self.assertIsNone(meta)
        mock_read_meta.assert_called_once_with('tag')

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('you_get.processor.join_flv.read_flv_header')
    @patch('you_get.processor.join_flv.read_tag')
    @patch('you_get.processor.join_flv.read_meta_tag')
    @patch('builtins.open')
    def test_validate_flv_only_meta_tag(self, mock_open, mock_read_meta, mock_read_tag, 
                                       mock_read_header, mock_getsize, mock_exists):
        """Test validate_flv with a file that has only a metadata tag."""
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        mock_read_header.return_value = True
        mock_read_tag.side_effect = ['tag', None]  # First call returns tag, second call returns None
        mock_read_meta.return_value = 'meta'
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result, meta = validate_flv('only_meta.flv')
        
        self.assertFalse(result)
        self.assertIsNone(meta)
        self.assertEqual(mock_read_tag.call_count, 2)

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('you_get.processor.join_flv.read_flv_header')
    @patch('you_get.processor.join_flv.read_tag')
    @patch('you_get.processor.join_flv.read_meta_tag')
    @patch('builtins.open')
    def test_validate_flv_valid(self, mock_open, mock_read_meta, mock_read_tag, 
                               mock_read_header, mock_getsize, mock_exists):
        """Test validate_flv with a valid FLV file."""
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        mock_read_header.return_value = True
        mock_read_tag.side_effect = ['tag', 'next_tag']  # First call returns tag, second call returns next_tag
        mock_read_meta.return_value = 'meta'
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result, meta = validate_flv('valid.flv')
        
        self.assertTrue(result)
        self.assertEqual(meta, 'meta')
        self.assertEqual(mock_read_tag.call_count, 2)

    @patch('you_get.processor.join_flv.validate_flv')
    def test_concat_flv_no_files(self, mock_validate):
        """Test concat_flv with no files."""
        with self.assertRaises(ValueError):
            concat_flv([])

    @patch('you_get.processor.join_flv.validate_flv')
    def test_concat_flv_no_valid_files(self, mock_validate):
        """Test concat_flv with no valid files."""
        mock_validate.return_value = (False, None)
        
        with self.assertRaises(ValueError):
            concat_flv(['invalid1.flv', 'invalid2.flv'])

    @patch('you_get.processor.join_flv.validate_flv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('you_get.processor.join_flv.write_flv_header')
    @patch('you_get.processor.join_flv.write_meta_tag')
    @patch('you_get.processor.join_flv.read_flv_header')
    @patch('you_get.processor.join_flv.read_tag')
    @patch('you_get.processor.join_flv.write_tag')
    @patch('you_get.processor.join_flv.write_uint')
    def test_concat_flv_with_valid_files(self, mock_write_uint, mock_write_tag, mock_read_tag, 
                                        mock_read_header, mock_write_meta_tag, mock_write_header, 
                                        mock_open, mock_validate):
        """Test concat_flv with valid files."""
        # Create mock metadata
        mock_meta = MagicMock()
        mock_meta.get.return_value = 10.0
        
        # Setup validate_flv to return valid for both files
        mock_validate.return_value = (True, ('onMetaData', mock_meta))
        
        # Setup read_tag to return a tag once, then None for each file
        tag = (8, 1000, 100, b'x' * 100, 0)
        mock_read_tag.side_effect = [tag, None, tag, None]
        
        # Call function
        result = concat_flv(['file1.flv', 'file2.flv'], 'output.flv')
        
        # Check result
        self.assertEqual(result, 'output.flv')
        
        # Check that all the necessary functions were called
        mock_validate.assert_called()
        mock_write_header.assert_called_once()
        mock_write_meta_tag.assert_called_once()
        mock_write_uint.assert_called_once()


if __name__ == '__main__':
    unittest.main()
