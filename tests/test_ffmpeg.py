#!/usr/bin/env python

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import sys
import tempfile

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from you_get.processor.ffmpeg import (
    get_usable_ffmpeg,
    generate_concat_list,
    ffmpeg_concat_av,
    has_ffmpeg_installed
)


class TestFFmpeg(unittest.TestCase):
    """Test cases for the ffmpeg.py module."""

    @patch('subprocess.Popen')
    def test_get_usable_ffmpeg_success(self, mock_popen):
        """Test get_usable_ffmpeg with a successful ffmpeg command."""
        # Mock the subprocess.Popen to return a successful result
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = (
            b'ffmpeg version 4.2.2 Copyright (c) 2000-2019 the FFmpeg developers',
            b''
        )
        mock_popen.return_value = process_mock

        # Call the function
        result = get_usable_ffmpeg('ffmpeg')

        # Check the result
        self.assertEqual(result[0], 'ffmpeg')
        self.assertEqual(result[1], 'ffprobe')
        self.assertEqual(result[2], [4, 2, 2])

    @patch('subprocess.Popen')
    def test_get_usable_ffmpeg_failure(self, mock_popen):
        """Test get_usable_ffmpeg with a failed command."""
        # Mock the subprocess.Popen to return a failed result
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.communicate.return_value = (b'', b'command not found')
        mock_popen.return_value = process_mock

        # Call the function
        result = get_usable_ffmpeg('ffmpeg')

        # Check the result
        self.assertIsNone(result)

    @patch('subprocess.Popen')
    def test_get_usable_ffmpeg_avconv(self, mock_popen):
        """Test get_usable_ffmpeg with avconv command."""
        # Mock the subprocess.Popen to return a successful result for avconv
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = (
            b'avconv version 11.12 Copyright (c) 2000-2019 the Libav developers',
            b''
        )
        mock_popen.return_value = process_mock

        # Call the function
        result = get_usable_ffmpeg('avconv')

        # Check the result
        self.assertEqual(result[0], 'avconv')
        self.assertEqual(result[1], 'avprobe')
        self.assertEqual(result[2], [11, 12])

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_generate_concat_list(self, mock_makedirs, mock_exists, mock_isfile):
        """Test generate_concat_list function."""
        # Mock file existence checks
        mock_isfile.return_value = True
        mock_exists.return_value = True

        # Mock open to avoid actual file operations
        with patch('builtins.open', mock_open()) as mock_file:
            # Call the function
            result = generate_concat_list(['file1.mp4', 'file2.mp4'], 'output')

            # Check the result
            self.assertEqual(result, 'output.txt')
            
            # Check that the file was written to correctly
            mock_file.assert_called_once_with('output.txt', 'w', encoding='utf-8')
            mock_file().write.assert_any_call('file file1.mp4\n')
            mock_file().write.assert_any_call('file file2.mp4\n')

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_generate_concat_list_no_valid_files(self, mock_makedirs, mock_exists, mock_isfile):
        """Test generate_concat_list with no valid files."""
        # Mock file existence checks
        mock_isfile.return_value = False
        mock_exists.return_value = True

        # Mock open to avoid actual file operations
        with patch('builtins.open', mock_open()) as mock_file:
            # Call the function
            result = generate_concat_list(['file1.mp4', 'file2.mp4'], 'output')

            # Check the result
            self.assertEqual(result, 'output.txt')
            
            # Check that the file was opened but no write calls were made
            mock_file.assert_called_once_with('output.txt', 'w', encoding='utf-8')
            mock_file().write.assert_not_called()

    @patch('subprocess.call')
    @patch('os.path.isfile')
    def test_ffmpeg_concat_av_success(self, mock_isfile, mock_call):
        """Test ffmpeg_concat_av with successful first attempt."""
        # Mock file existence checks
        mock_isfile.return_value = True
        
        # Mock subprocess.call to return success
        mock_call.return_value = 0

        # Call the function
        result = ffmpeg_concat_av(['file1.mp4', 'file2.mp4'], 'output.mp4', 'mp4')

        # Check the result
        self.assertEqual(result, 0)
        
        # Check that subprocess.call was called once
        self.assertEqual(mock_call.call_count, 1)

    @patch('subprocess.call')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_ffmpeg_concat_av_retry(self, mock_remove, mock_exists, mock_isfile, mock_call):
        """Test ffmpeg_concat_av with failed first attempt and successful retry."""
        # Mock file existence checks
        mock_isfile.return_value = True
        mock_exists.return_value = True
        
        # Mock subprocess.call to fail first, then succeed
        mock_call.side_effect = [1, 0]

        # Call the function
        result = ffmpeg_concat_av(['file1.mp4', 'file2.mp4'], 'output.mp4', 'mp4')

        # Check the result
        self.assertEqual(result, 0)
        
        # Check that subprocess.call was called twice
        self.assertEqual(mock_call.call_count, 2)
        
        # Check that os.remove was called
        mock_remove.assert_called_once()

    @patch('subprocess.call')
    @patch('os.path.isfile')
    def test_ffmpeg_concat_av_no_valid_files(self, mock_isfile, mock_call):
        """Test ffmpeg_concat_av with no valid files."""
        # Mock file existence checks
        mock_isfile.return_value = False
        
        # Call the function
        result = ffmpeg_concat_av(['file1.mp4', 'file2.mp4'], 'output.mp4', 'mp4')

        # Check the result
        self.assertEqual(result, 1)
        
        # Check that subprocess.call was not called
        mock_call.assert_not_called()

    @patch('you_get.processor.ffmpeg.FFMPEG', None)
    def test_has_ffmpeg_installed_false(self):
        """Test has_ffmpeg_installed when ffmpeg is not installed."""
        self.assertFalse(has_ffmpeg_installed())

    @patch('you_get.processor.ffmpeg.FFMPEG', 'ffmpeg')
    def test_has_ffmpeg_installed_true(self):
        """Test has_ffmpeg_installed when ffmpeg is installed."""
        self.assertTrue(has_ffmpeg_installed())


if __name__ == '__main__':
    unittest.main()
