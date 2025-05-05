#!/usr/bin/env python
"""
FLV file processing module for merging multiple FLV files into a single file.

This module provides functionality to validate, read, and merge FLV (Flash Video) files.
It handles corrupted files gracefully by validating each file before processing and
skipping invalid ones during the merging process.
"""

import struct
import os
import logging
from io import BytesIO

# FLV tag type constants
TAG_TYPE_METADATA = 18
TAG_TYPE_AUDIO = 8
TAG_TYPE_VIDEO = 9

logger = logging.getLogger(__name__)

##################################################
# AMF0
##################################################

AMF_TYPE_NUMBER = 0x00
AMF_TYPE_BOOLEAN = 0x01
AMF_TYPE_STRING = 0x02
AMF_TYPE_OBJECT = 0x03
AMF_TYPE_MOVIECLIP = 0x04
AMF_TYPE_NULL = 0x05
AMF_TYPE_UNDEFINED = 0x06
AMF_TYPE_REFERENCE = 0x07
AMF_TYPE_MIXED_ARRAY = 0x08
AMF_TYPE_END_OF_OBJECT = 0x09
AMF_TYPE_ARRAY = 0x0A
AMF_TYPE_DATE = 0x0B
AMF_TYPE_LONG_STRING = 0x0C
AMF_TYPE_UNSUPPORTED = 0x0D
AMF_TYPE_RECORDSET = 0x0E
AMF_TYPE_XML = 0x0F
AMF_TYPE_CLASS_OBJECT = 0x10
AMF_TYPE_AMF3_OBJECT = 0x11

class ECMAObject:
    """ECMA object implementation for handling ActionScript objects in FLV files.

    This class provides a dictionary-like interface for storing and manipulating
    ActionScript object data with ordered key-value pairs.
    """
    def __init__(self, max_number):
        """Initialize an ECMAObject with a maximum number of entries.

        Args:
            max_number (int): Maximum number of entries in the object
        """
        self.max_number = max_number
        self.data = []
        self.map = {}

    def put(self, k, v):
        """Add a key-value pair to the object.

        Args:
            k: Key
            v: Value
        """
        self.data.append((k, v))
        self.map[k] = v

    def get(self, k):
        """Get a value by key.

        Args:
            k: Key to look up

        Returns:
            The value associated with the key
        """
        return self.map[k]

    def set(self, k, v):
        """Update an existing key-value pair.

        Args:
            k: Key to update
            v: New value

        Raises:
            KeyError: If the key doesn't exist
        """
        for i in range(len(self.data)):
            if self.data[i][0] == k:
                self.data[i] = (k, v)
                break
        else:
            raise KeyError(k)
        self.map[k] = v

    def keys(self):
        """Get all keys in the object.

        Returns:
            A view of all keys
        """
        return self.map.keys()

    def __str__(self):
        """String representation of the object.

        Returns:
            String representation
        """
        return 'ECMAObject<' + repr(self.map) + '>'

    def __eq__(self, other):
        """Check if two ECMAObjects are equal.

        Args:
            other: Another ECMAObject to compare with

        Returns:
            bool: True if equal, False otherwise
        """
        return self.max_number == other.max_number and self.data == other.data

def read_amf_number(stream):
    """Read an AMF number (double) from a stream.

    Args:
        stream: Binary stream to read from

    Returns:
        float: The double value read from the stream
    """
    return struct.unpack('>d', stream.read(8))[0]

def read_amf_boolean(stream):
    """Read an AMF boolean from a stream.

    Args:
        stream: Binary stream to read from

    Returns:
        bool: The boolean value read from the stream
    """
    b = read_byte(stream)
    assert b in (0, 1)
    return bool(b)

def read_amf_string(stream):
    """Read an AMF string from a stream.

    Args:
        stream: Binary stream to read from

    Returns:
        str: The string value read from the stream, or None if invalid
    """
    xx = stream.read(2)
    if xx == b'':
        # dirty fix for the invalid Qiyi flv
        return None
    n = struct.unpack('>H', xx)[0]
    s = stream.read(n)
    assert len(s) == n
    return s.decode('utf-8')

def read_amf_object(stream):
    obj = {}
    while True:
        k = read_amf_string(stream)
        if not k:
            assert read_byte(stream) == AMF_TYPE_END_OF_OBJECT
            break
        v = read_amf(stream)
        obj[k] = v
    return obj

def read_amf_mixed_array(stream):
    max_number = read_uint(stream)
    mixed_results = ECMAObject(max_number)
    while True:
        k = read_amf_string(stream)
        if k is None:
            # dirty fix for the invalid Qiyi flv
            break
        if not k:
            assert read_byte(stream) == AMF_TYPE_END_OF_OBJECT
            break
        v = read_amf(stream)
        mixed_results.put(k, v)
    assert len(mixed_results.data) == max_number
    return mixed_results

def read_amf_array(stream):
    n = read_uint(stream)
    v = []
    for i in range(n):
        v.append(read_amf(stream))
    return v

amf_readers = {
    AMF_TYPE_NUMBER: read_amf_number,
    AMF_TYPE_BOOLEAN: read_amf_boolean,
    AMF_TYPE_STRING: read_amf_string,
    AMF_TYPE_OBJECT: read_amf_object,
    AMF_TYPE_MIXED_ARRAY: read_amf_mixed_array,
    AMF_TYPE_ARRAY: read_amf_array,
}

def read_amf(stream):
    return amf_readers[read_byte(stream)](stream)

def write_amf_number(stream, v):
    stream.write(struct.pack('>d', v))

def write_amf_boolean(stream, v):
    if v:
        stream.write(b'\x01')
    else:
        stream.write(b'\x00')

def write_amf_string(stream, s):
    s = s.encode('utf-8')
    stream.write(struct.pack('>H', len(s)))
    stream.write(s)

def write_amf_object(stream, o):
    for k in o:
        write_amf_string(stream, k)
        write_amf(stream, o[k])
    write_amf_string(stream, '')
    write_byte(stream, AMF_TYPE_END_OF_OBJECT)

def write_amf_mixed_array(stream, o):
    write_uint(stream, o.max_number)
    for k, v in o.data:
        write_amf_string(stream, k)
        write_amf(stream, v)
    write_amf_string(stream, '')
    write_byte(stream, AMF_TYPE_END_OF_OBJECT)

def write_amf_array(stream, o):
    write_uint(stream, len(o))
    for v in o:
        write_amf(stream, v)

amf_writers_tags = {
    float: AMF_TYPE_NUMBER,
    bool: AMF_TYPE_BOOLEAN,
    str: AMF_TYPE_STRING,
    dict: AMF_TYPE_OBJECT,
    ECMAObject: AMF_TYPE_MIXED_ARRAY,
    list: AMF_TYPE_ARRAY,
}

amf_writers = {
    AMF_TYPE_NUMBER: write_amf_number,
    AMF_TYPE_BOOLEAN: write_amf_boolean,
    AMF_TYPE_STRING: write_amf_string,
    AMF_TYPE_OBJECT: write_amf_object,
    AMF_TYPE_MIXED_ARRAY: write_amf_mixed_array,
    AMF_TYPE_ARRAY: write_amf_array,
}

def write_amf(stream, v):
    if isinstance(v, ECMAObject):
        tag = amf_writers_tags[ECMAObject]
    else:
        tag = amf_writers_tags[type(v)]
    write_byte(stream, tag)
    amf_writers[tag](stream, v)

##################################################
# FLV
##################################################

def read_int(stream):
    return struct.unpack('>i', stream.read(4))[0]

def read_uint(stream):
    return struct.unpack('>I', stream.read(4))[0]

def write_uint(stream, n):
    stream.write(struct.pack('>I', n))

def read_byte(stream):
    return ord(stream.read(1))

def write_byte(stream, b):
    stream.write(bytes([b]))

def read_unsigned_medium_int(stream):
    x1, x2, x3 = struct.unpack('BBB', stream.read(3))
    return (x1 << 16) | (x2 << 8) | x3

def read_tag(stream):
    """Read and validate an FLV tag from a stream.

    Reads the tag header and body, performing validation on:
    - Tag type (must be audio, video, or metadata)
    - Body size (must be reasonable)
    - Stream ID (must be 0)
    - Complete body (must match expected size)

    Args:
        stream: Binary stream to read from

    Returns:
        tuple: (data_type, timestamp, body_size, body, previous_tag_size) if valid,
               None if invalid or end of file
    """
    # header size: 15 bytes
    try:
        header = stream.read(15)
        if len(header) < 15:
            # End of file or incomplete tag
            return None

        x = struct.unpack('>IBBBBBBBBBBB', header)
        previous_tag_size = x[0]
        data_type = x[1]
        body_size = (x[2] << 16) | (x[3] << 8) | x[4]

        # Validate tag type
        if data_type not in (TAG_TYPE_AUDIO, TAG_TYPE_VIDEO, TAG_TYPE_METADATA):
            logger.debug(f"Invalid tag type: {data_type}")
            return None

        # Validate body size
        if body_size > 1024 * 1024 * 128:
            logger.debug(f"Tag body size too big: {body_size} bytes (> 128MB)")
            return None

        timestamp = (x[5] << 16) | (x[6] << 8) | x[7]
        timestamp += x[8] << 24

        # Validate stream ID (should be 0)
        if x[9:] != (0, 0, 0):
            logger.debug(f"Invalid stream ID: {x[9:]}")
            return None

        # Read the tag body
        body = stream.read(body_size)

        # Check if we got the full body
        if len(body) < body_size:
            logger.debug(f"Incomplete tag body: expected {body_size} bytes, got {len(body)} bytes")
            return None

        return (data_type, timestamp, body_size, body, previous_tag_size)
    except Exception as e:
        logger.debug(f"Error reading tag: {e}")
        return None

def write_tag(stream, tag):
    data_type, timestamp, body_size, body, previous_tag_size = tag
    write_uint(stream, previous_tag_size)
    write_byte(stream, data_type)
    write_byte(stream, body_size>>16 & 0xff)
    write_byte(stream, body_size>>8  & 0xff)
    write_byte(stream, body_size     & 0xff)
    write_byte(stream, timestamp>>16 & 0xff)
    write_byte(stream, timestamp>>8  & 0xff)
    write_byte(stream, timestamp     & 0xff)
    write_byte(stream, timestamp>>24 & 0xff)
    stream.write(b'\0\0\0')
    stream.write(body)

def read_flv_header(stream):
    """Read and validate an FLV file header.

    Checks for the FLV signature, version 1, video+audio type flags,
    and standard data offset.

    Args:
        stream: Binary stream to read from

    Returns:
        bool: True if header is valid, False otherwise
    """
    try:
        header = stream.read(3)
        if header != b'FLV':
            return False
        header_version = read_byte(stream)
        if header_version != 1:
            return False
        type_flags = read_byte(stream)
        if type_flags != 5:
            return False
        data_offset = read_uint(stream)
        if data_offset != 9:
            return False
        return True
    except Exception as e:
        logger.debug(f"Error reading FLV header: {e}")
        return False

def write_flv_header(stream):
    stream.write(b'FLV')
    write_byte(stream, 1)
    write_byte(stream, 5)
    write_uint(stream, 9)

def read_meta_data(stream):
    meta_type = read_amf(stream)
    meta = read_amf(stream)
    return meta_type, meta

def read_meta_tag(tag):
    try:
        data_type, timestamp, body_size, body, previous_tag_size = tag
        if data_type != TAG_TYPE_METADATA:
            logger.debug(f"Expected metadata tag, got tag type {data_type}")
            return None
        # Some files might have non-zero timestamp or previous_tag_size for metadata
        # We'll be more lenient here
        return read_meta_data(BytesIO(body))
    except Exception as e:
        logger.debug(f"Error reading metadata tag: {e}")
        return None

#def write_meta_data(stream, meta_type, meta_data):
#    assert isinstance(meta_type, basesting)
#    write_amf(meta_type)
#    write_amf(meta_data)

def write_meta_tag(stream, meta_type, meta_data):
    buffer = BytesIO()
    write_amf(buffer, meta_type)
    write_amf(buffer, meta_data)
    body = buffer.getvalue()
    write_tag(stream, (TAG_TYPE_METADATA, 0, len(body), body, 0))


##################################################
# main
##################################################

def guess_output(inputs):
    """Guess the output filename based on common prefix of input files.

    Analyzes the input filenames to find the longest common prefix,
    with special handling for filenames with numbering patterns like
    'video_part1.flv', 'video_part2.flv', etc.

    Args:
        inputs (list): List of input filenames

    Returns:
        str: Guessed output filename, or 'output.flv' if no common prefix found
    """
    import os.path
    inputs = list(map(os.path.basename, inputs))
    n = min(map(len, inputs))

    # Find the longest common prefix
    for i in reversed(range(1, n)):
        prefixes = set(s[:i] for s in inputs)
        if len(prefixes) == 1:
            # If we have a common prefix like 'video_part', use it
            if '_' in inputs[0][:i] and inputs[0][:i].rindex('_') < i - 1:
                return inputs[0][:inputs[0][:i].rindex('_') + 1] + '.flv'
            return inputs[0][:i] + '.flv'

    return 'output.flv'

def validate_flv(file_path):
    """Validate if a file is a valid FLV file.

    Performs multiple validation checks on an FLV file including:
    - File existence
    - Minimum file size
    - Valid FLV header
    - Valid metadata tag
    - At least one content tag after metadata

    Args:
        file_path (str): Path to the FLV file

    Returns:
        tuple: (is_valid, metadata) - Boolean indicating if file is valid and metadata if available
    """
    try:
        if not os.path.exists(file_path):
            logger.debug(f"File does not exist: {file_path}")
            return False, None

        if os.path.getsize(file_path) < 9:  # Minimum size for FLV header
            logger.debug(f"File too small to be valid FLV: {file_path}")
            return False, None

        with open(file_path, 'rb') as f:
            # Check header
            if not read_flv_header(f):
                logger.debug(f"Invalid FLV header: {file_path}")
                return False, None

            # Try to read metadata tag
            meta_tag = read_tag(f)
            if not meta_tag:
                logger.debug(f"Could not read first tag: {file_path}")
                return False, None

            meta = read_meta_tag(meta_tag)
            if not meta:
                logger.debug(f"Could not read metadata: {file_path}")
                return False, None

            # Try to read at least one more tag to ensure file is not truncated
            next_tag = read_tag(f)
            if not next_tag:
                logger.debug(f"File contains only metadata tag: {file_path}")
                return False, None

            return True, meta
    except Exception as e:
        logger.debug(f"Error validating FLV file {file_path}: {e}")
        return False, None

def concat_flv(flvs, output = None):
    """Concatenate multiple FLV files into one.

    This function validates all input files, skips corrupted ones, and merges
    valid files into a single output file. It handles metadata properly by
    combining duration information and adjusting timestamps for seamless playback.

    Args:
        flvs (list): List of FLV file paths
        output (str, optional): Output file path

    Returns:
        str: Path to the output file

    Raises:
        ValueError: If no valid FLV files are found
    """
    if not flvs:
        raise ValueError('No FLV files provided')

    import os.path
    if not output:
        output = guess_output(flvs)
    elif os.path.isdir(output):
        output = os.path.join(output, guess_output(flvs))

    print('Validating video parts...')
    valid_files = []
    valid_metas = []

    # Validate all input files
    for flv in flvs:
        is_valid, meta = validate_flv(flv)
        if is_valid and meta:
            valid_files.append(flv)
            valid_metas.append(meta)
        else:
            print(f"Warning: Skipping corrupted or invalid file: {flv}")

    if not valid_files:
        raise ValueError('No valid FLV files found')

    # Extract metadata types and ensure they're consistent
    meta_types = [meta[0] for meta in valid_metas]
    if len(set(meta_types)) != 1:
        print("Warning: Inconsistent metadata types across files. Using the most common type.")
        # Use the most common metadata type
        from collections import Counter
        meta_type = Counter(meta_types).most_common(1)[0][0]
    else:
        meta_type = meta_types[0]

    # Extract metadata objects
    metas = [meta[1] for meta in valid_metas]

    print(f'Merging {len(valid_files)} valid video parts...')

    try:
        # Calculate total duration
        total_duration = sum(meta.get('duration', 0) for meta in metas)

        # Use the first file's metadata as base
        meta_data = metas[0]
        meta_data.set('duration', total_duration)

        # Open output file
        out = open(output, 'wb')
        write_flv_header(out)
        write_meta_tag(out, meta_type, meta_data)

        # Process each valid file
        timestamp_start = 0
        previous_tag_size = 0

        for flv in valid_files:
            try:
                with open(flv, 'rb') as stream:
                    # Skip the header
                    read_flv_header(stream)

                    # Skip the first tag (metadata)
                    first_tag = read_tag(stream)
                    if not first_tag:
                        print(f"Warning: Could not read metadata tag from {flv}, skipping file")
                        continue

                    # Read and write all remaining tags
                    current_timestamp = 0
                    while True:
                        tag = read_tag(stream)
                        if not tag:
                            break

                        data_type, timestamp, body_size, body, _ = tag
                        current_timestamp = timestamp
                        adjusted_timestamp = current_timestamp + timestamp_start
                        tag = data_type, adjusted_timestamp, body_size, body, previous_tag_size
                        write_tag(out, tag)
                        previous_tag_size = body_size + 11  # 11 is the size of the tag header

                    # Update timestamp for next file
                    timestamp_start += current_timestamp
            except Exception as e:
                print(f"Warning: Error processing file {flv}: {e}")
                continue

        # Write final previous tag size
        write_uint(out, previous_tag_size)
        out.close()

        print(f"Successfully merged {len(valid_files)} files into {output}")
        return output

    except Exception as e:
        print(f"Error merging FLV files: {e}")
        # Try to close and remove the output file if it exists
        try:
            if 'out' in locals() and not out.closed:
                out.close()
            if os.path.exists(output):
                os.remove(output)
        except:
            pass
        raise

def usage():
    print('Usage: [python3] join_flv.py --output TARGET.flv flv...')

def main():
    """Command-line entry point for the FLV concatenation tool.

    Parses command-line arguments and calls concat_flv with appropriate parameters.
    Handles errors gracefully with informative error messages.

    Usage: join_flv.py --output TARGET.flv flv...
    """
    import sys, getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:", ["help", "output="])
    except getopt.GetoptError as err:
        usage()
        sys.exit(1)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        else:
            usage()
            sys.exit(1)
    if not args:
        usage()
        sys.exit(1)

    try:
        concat_flv(args, output)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
