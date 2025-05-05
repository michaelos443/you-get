#!/usr/bin/env python

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import io
import struct
from io import BytesIO

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from you_get.processor.join_flv import (
    # AMF0 functions
    read_amf_number, read_amf_boolean, read_amf_string, read_amf_object,
    read_amf_mixed_array, read_amf_array, read_amf,
    write_amf_number, write_amf_boolean, write_amf_string, write_amf_object,
    write_amf_mixed_array, write_amf_array, write_amf,
    # FLV functions
    read_int, read_uint, write_uint, read_byte, write_byte,
    read_unsigned_medium_int, read_tag, write_tag,
    read_flv_header, write_flv_header, read_meta_data, read_meta_tag,
    write_meta_tag,
    # Main functions
    guess_output, concat_flv, ECMAObject
)


class TestJoinFLV(unittest.TestCase):
    """Test cases for the join_flv.py module."""

    def test_ecma_object(self):
        """Test ECMAObject class."""
        obj = ECMAObject(2)
        obj.put('key1', 'value1')
        obj.put('key2', 'value2')

        # Test get method
        self.assertEqual(obj.get('key1'), 'value1')
        self.assertEqual(obj.get('key2'), 'value2')

        # Test set method
        obj.set('key1', 'new_value1')
        self.assertEqual(obj.get('key1'), 'new_value1')

        # Test keys method
        self.assertEqual(set(obj.keys()), {'key1', 'key2'})

        # Test __str__ method
        self.assertTrue('ECMAObject<' in str(obj))
        self.assertTrue('key1' in str(obj))
        self.assertTrue('new_value1' in str(obj))

        # Test __eq__ method
        obj2 = ECMAObject(2)
        obj2.put('key1', 'new_value1')
        obj2.put('key2', 'value2')
        self.assertEqual(obj, obj2)

        # Test inequality
        obj3 = ECMAObject(3)
        obj3.put('key1', 'new_value1')
        obj3.put('key2', 'value2')
        self.assertNotEqual(obj, obj3)

    def test_read_amf_number(self):
        """Test read_amf_number function."""
        # Create a BytesIO with a double-precision float
        stream = BytesIO(struct.pack('>d', 123.456))
        result = read_amf_number(stream)
        self.assertAlmostEqual(result, 123.456)

    def test_read_amf_boolean(self):
        """Test read_amf_boolean function."""
        # Test True
        stream = BytesIO(b'\x01')
        result = read_amf_boolean(stream)
        self.assertTrue(result)

        # Test False
        stream = BytesIO(b'\x00')
        result = read_amf_boolean(stream)
        self.assertFalse(result)

    def test_read_amf_string(self):
        """Test read_amf_string function."""
        # Create a BytesIO with a string length and string data
        test_str = "Hello, World!"
        stream = BytesIO(struct.pack('>H', len(test_str)) + test_str.encode('utf-8'))
        result = read_amf_string(stream)
        self.assertEqual(result, test_str)

        # Test empty string
        stream = BytesIO(struct.pack('>H', 0))
        result = read_amf_string(stream)
        self.assertEqual(result, '')

    @patch('you_get.processor.join_flv.read_amf_string')
    @patch('you_get.processor.join_flv.read_amf')
    @patch('you_get.processor.join_flv.read_byte')
    def test_read_amf_object(self, mock_read_byte, mock_read_amf, mock_read_amf_string):
        """Test read_amf_object function."""
        # Setup mocks
        mock_read_amf_string.side_effect = ['key1', 'key2', '']
        mock_read_amf.side_effect = ['value1', 'value2']
        mock_read_byte.return_value = 9  # AMF_TYPE_END_OF_OBJECT

        # Call function
        result = read_amf_object(BytesIO())

        # Check result
        self.assertEqual(result, {'key1': 'value1', 'key2': 'value2'})
        self.assertEqual(mock_read_amf_string.call_count, 3)
        self.assertEqual(mock_read_amf.call_count, 2)
        self.assertEqual(mock_read_byte.call_count, 1)

    @patch('you_get.processor.join_flv.read_uint')
    @patch('you_get.processor.join_flv.read_amf_string')
    @patch('you_get.processor.join_flv.read_amf')
    @patch('you_get.processor.join_flv.read_byte')
    def test_read_amf_mixed_array(self, mock_read_byte, mock_read_amf, mock_read_amf_string, mock_read_uint):
        """Test read_amf_mixed_array function."""
        # Setup mocks
        mock_read_uint.return_value = 2
        mock_read_amf_string.side_effect = ['key1', 'key2', '']
        mock_read_amf.side_effect = ['value1', 'value2']
        mock_read_byte.return_value = 9  # AMF_TYPE_END_OF_OBJECT

        # Call function
        result = read_amf_mixed_array(BytesIO())

        # Check result
        self.assertEqual(result.max_number, 2)
        self.assertEqual(result.get('key1'), 'value1')
        self.assertEqual(result.get('key2'), 'value2')
        self.assertEqual(mock_read_amf_string.call_count, 3)
        self.assertEqual(mock_read_amf.call_count, 2)
        self.assertEqual(mock_read_byte.call_count, 1)

    @patch('you_get.processor.join_flv.read_uint')
    @patch('you_get.processor.join_flv.read_amf')
    def test_read_amf_array(self, mock_read_amf, mock_read_uint):
        """Test read_amf_array function."""
        # Setup mocks
        mock_read_uint.return_value = 3
        mock_read_amf.side_effect = ['value1', 'value2', 'value3']

        # Call function
        result = read_amf_array(BytesIO())

        # Check result
        self.assertEqual(result, ['value1', 'value2', 'value3'])
        self.assertEqual(mock_read_amf.call_count, 3)

    @patch('you_get.processor.join_flv.read_byte')
    @patch('you_get.processor.join_flv.amf_readers')
    def test_read_amf(self, mock_amf_readers, mock_read_byte):
        """Test read_amf function."""
        # Setup mocks
        mock_read_byte.return_value = 0  # AMF_TYPE_NUMBER
        mock_reader = MagicMock()
        mock_reader.return_value = 123.456
        mock_amf_readers.__getitem__.return_value = mock_reader

        # Call function
        result = read_amf(BytesIO())

        # Check result
        self.assertEqual(result, 123.456)
        mock_read_byte.assert_called_once()
        mock_amf_readers.__getitem__.assert_called_once_with(0)
        mock_reader.assert_called_once()

    def test_write_amf_number(self):
        """Test write_amf_number function."""
        stream = BytesIO()
        write_amf_number(stream, 123.456)
        stream.seek(0)
        result = struct.unpack('>d', stream.read(8))[0]
        self.assertAlmostEqual(result, 123.456)

    def test_write_amf_boolean(self):
        """Test write_amf_boolean function."""
        # Test True
        stream = BytesIO()
        write_amf_boolean(stream, True)
        stream.seek(0)
        self.assertEqual(stream.read(), b'\x01')

        # Test False
        stream = BytesIO()
        write_amf_boolean(stream, False)
        stream.seek(0)
        self.assertEqual(stream.read(), b'\x00')

    def test_write_amf_string(self):
        """Test write_amf_string function."""
        test_str = "Hello, World!"
        stream = BytesIO()
        write_amf_string(stream, test_str)
        stream.seek(0)
        length = struct.unpack('>H', stream.read(2))[0]
        self.assertEqual(length, len(test_str))
        self.assertEqual(stream.read().decode('utf-8'), test_str)

    @patch('you_get.processor.join_flv.write_amf_string')
    @patch('you_get.processor.join_flv.write_amf')
    @patch('you_get.processor.join_flv.write_byte')
    def test_write_amf_object(self, mock_write_byte, mock_write_amf, mock_write_amf_string):
        """Test write_amf_object function."""
        obj = {'key1': 'value1', 'key2': 'value2'}
        stream = BytesIO()

        write_amf_object(stream, obj)

        # Check that write_amf_string was called for each key and the empty string
        self.assertEqual(mock_write_amf_string.call_count, 3)
        # Check that write_amf was called for each value
        self.assertEqual(mock_write_amf.call_count, 2)
        # Check that write_byte was called once for END_OF_OBJECT
        mock_write_byte.assert_called_once_with(stream, 9)

    @patch('you_get.processor.join_flv.write_uint')
    @patch('you_get.processor.join_flv.write_amf_string')
    @patch('you_get.processor.join_flv.write_amf')
    @patch('you_get.processor.join_flv.write_byte')
    def test_write_amf_mixed_array(self, mock_write_byte, mock_write_amf, mock_write_amf_string, mock_write_uint):
        """Test write_amf_mixed_array function."""
        obj = ECMAObject(2)
        obj.put('key1', 'value1')
        obj.put('key2', 'value2')
        stream = BytesIO()

        write_amf_mixed_array(stream, obj)

        # Check that write_uint was called with max_number
        mock_write_uint.assert_called_once_with(stream, 2)
        # Check that write_amf_string was called for each key and the empty string
        self.assertEqual(mock_write_amf_string.call_count, 3)
        # Check that write_amf was called for each value
        self.assertEqual(mock_write_amf.call_count, 2)
        # Check that write_byte was called once for END_OF_OBJECT
        mock_write_byte.assert_called_once_with(stream, 9)

    @patch('you_get.processor.join_flv.write_uint')
    @patch('you_get.processor.join_flv.write_amf')
    def test_write_amf_array(self, mock_write_amf, mock_write_uint):
        """Test write_amf_array function."""
        arr = ['value1', 'value2', 'value3']
        stream = BytesIO()

        write_amf_array(stream, arr)

        # Check that write_uint was called with array length
        mock_write_uint.assert_called_once_with(stream, 3)
        # Check that write_amf was called for each value
        self.assertEqual(mock_write_amf.call_count, 3)

    @patch('you_get.processor.join_flv.amf_writers_tags')
    @patch('you_get.processor.join_flv.write_byte')
    @patch('you_get.processor.join_flv.amf_writers')
    def test_write_amf(self, mock_amf_writers, mock_write_byte, mock_amf_writers_tags):
        """Test write_amf function."""
        # Setup mocks for a number
        mock_amf_writers_tags.__getitem__.return_value = 0  # AMF_TYPE_NUMBER
        mock_writer = MagicMock()
        mock_amf_writers.__getitem__.return_value = mock_writer

        # Call function
        stream = BytesIO()
        write_amf(stream, 123.456)

        # Check result
        mock_amf_writers_tags.__getitem__.assert_called_once_with(float)
        mock_write_byte.assert_called_once_with(stream, 0)
        mock_amf_writers.__getitem__.assert_called_once_with(0)
        mock_writer.assert_called_once_with(stream, 123.456)

    def test_read_int(self):
        """Test read_int function."""
        stream = BytesIO(struct.pack('>i', -12345))
        result = read_int(stream)
        self.assertEqual(result, -12345)

    def test_read_uint(self):
        """Test read_uint function."""
        stream = BytesIO(struct.pack('>I', 12345))
        result = read_uint(stream)
        self.assertEqual(result, 12345)

    def test_write_uint(self):
        """Test write_uint function."""
        stream = BytesIO()
        write_uint(stream, 12345)
        stream.seek(0)
        result = struct.unpack('>I', stream.read(4))[0]
        self.assertEqual(result, 12345)

    def test_read_byte(self):
        """Test read_byte function."""
        stream = BytesIO(b'\x42')
        result = read_byte(stream)
        self.assertEqual(result, 0x42)

    def test_write_byte(self):
        """Test write_byte function."""
        stream = BytesIO()
        write_byte(stream, 0x42)
        stream.seek(0)
        result = stream.read()
        self.assertEqual(result, b'\x42')

    def test_read_unsigned_medium_int(self):
        """Test read_unsigned_medium_int function."""
        stream = BytesIO(b'\x01\x23\x45')
        result = read_unsigned_medium_int(stream)
        self.assertEqual(result, 0x012345)

    @patch('you_get.processor.join_flv.struct.unpack')
    def test_read_tag(self, mock_unpack):
        """Test read_tag function."""
        # Setup mock for header
        mock_unpack.return_value = (0, 18, 0, 0, 100, 0, 0, 1, 0, 0, 0, 0)

        # Create a mock stream with header and body
        stream = MagicMock()
        stream.read.side_effect = [b'x' * 15, b'y' * 100]

        # Call function
        result = read_tag(stream)

        # Check result
        self.assertEqual(result[0], 18)  # data_type
        self.assertEqual(result[1], 1)   # timestamp
        self.assertEqual(result[2], 100)  # body_size
        self.assertEqual(result[3], b'y' * 100)  # body
        self.assertEqual(result[4], 0)   # previous_tag_size

    @patch('you_get.processor.join_flv.write_uint')
    @patch('you_get.processor.join_flv.write_byte')
    def test_write_tag(self, mock_write_byte, mock_write_uint):
        """Test write_tag function."""
        tag = (18, 1000, 100, b'x' * 100, 0)
        stream = MagicMock()

        write_tag(stream, tag)

        # Check that write_uint was called for previous_tag_size
        mock_write_uint.assert_called_once_with(stream, 0)
        # Check that write_byte was called for data_type and other fields
        self.assertEqual(mock_write_byte.call_count, 8)
        # Check that stream.write was called for body
        stream.write.assert_any_call(b'x' * 100)

    def test_read_flv_header(self):
        """Test read_flv_header function."""
        stream = BytesIO(b'FLV\x01\x05\x00\x00\x00\x09')
        result = read_flv_header(stream)
        self.assertTrue(result)

    def test_write_flv_header(self):
        """Test write_flv_header function."""
        stream = BytesIO()
        write_flv_header(stream)
        stream.seek(0)
        self.assertEqual(stream.read(), b'FLV\x01\x05\x00\x00\x00\x09')

    @patch('you_get.processor.join_flv.read_amf')
    def test_read_meta_data(self, mock_read_amf):
        """Test read_meta_data function."""
        mock_read_amf.side_effect = ['meta_type', 'meta_data']
        stream = BytesIO()

        result = read_meta_data(stream)

        self.assertEqual(result, ('meta_type', 'meta_data'))
        self.assertEqual(mock_read_amf.call_count, 2)

    @patch('you_get.processor.join_flv.read_meta_data')
    def test_read_meta_tag(self, mock_read_meta_data):
        """Test read_meta_tag function."""
        mock_read_meta_data.return_value = ('meta_type', 'meta_data')
        tag = (18, 0, 100, b'x' * 100, 0)

        result = read_meta_tag(tag)

        self.assertEqual(result, ('meta_type', 'meta_data'))
        mock_read_meta_data.assert_called_once()

    @patch('you_get.processor.join_flv.BytesIO')
    @patch('you_get.processor.join_flv.write_amf')
    @patch('you_get.processor.join_flv.write_tag')
    def test_write_meta_tag(self, mock_write_tag, mock_write_amf, mock_bytesio):
        """Test write_meta_tag function."""
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'x' * 100
        mock_bytesio.return_value = mock_buffer

        stream = MagicMock()
        meta_type = 'meta_type'
        meta_data = 'meta_data'

        write_meta_tag(stream, meta_type, meta_data)

        # Check that write_amf was called for meta_type and meta_data
        self.assertEqual(mock_write_amf.call_count, 2)
        # Check that write_tag was called with the correct parameters
        mock_write_tag.assert_called_once_with(stream, (18, 0, 100, b'x' * 100, 0))

    @patch('os.path.basename')
    def test_guess_output(self, mock_basename):
        """Test guess_output function."""
        # Mock basename to return the filenames directly
        mock_basename.side_effect = lambda x: x

        # Test with common prefix
        result = guess_output(['video_part1.flv', 'video_part2.flv'])
        self.assertEqual(result, 'video_.flv')

        # Test with no common prefix
        result = guess_output(['video1.flv', 'different.flv'])
        self.assertEqual(result, 'output.flv')

    @patch('you_get.processor.join_flv.validate_flv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('you_get.processor.join_flv.read_flv_header')
    @patch('you_get.processor.join_flv.read_tag')
    @patch('you_get.processor.join_flv.write_flv_header')
    @patch('you_get.processor.join_flv.write_meta_tag')
    @patch('you_get.processor.join_flv.write_tag')
    @patch('you_get.processor.join_flv.write_uint')
    def test_concat_flv(self, mock_write_uint, mock_write_tag, mock_write_meta_tag,
                        mock_write_flv_header, mock_read_tag,
                        mock_read_flv_header, mock_open, mock_validate_flv):
        """Test concat_flv function."""
        # Setup mocks
        mock_meta = MagicMock()
        mock_meta.get.return_value = 10.0

        # Setup validate_flv to return valid for both files
        mock_validate_flv.return_value = (True, ('onMetaData', mock_meta))

        # Mock read_tag to return a tag once, then None for each file
        tag = (8, 1000, 100, b'x' * 100, 0)
        mock_read_tag.side_effect = [tag, None, tag, None]

        # Call function
        result = concat_flv(['file1.flv', 'file2.flv'], 'output.flv')

        # Check result
        self.assertEqual(result, 'output.flv')

        # Check that all the necessary functions were called
        mock_validate_flv.assert_called()
        mock_write_flv_header.assert_called_once()
        mock_write_meta_tag.assert_called_once()
        mock_write_uint.assert_called_once()

        # Check that duration was updated
        mock_meta.set.assert_called_once_with('duration', 20.0)


if __name__ == '__main__':
    unittest.main()
