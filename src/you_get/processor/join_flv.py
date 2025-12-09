#!/usr/bin/env python
"""
FLV file joining module.

This module provides functionality for reading, writing, and concatenating
FLV (Flash Video) files. It includes support for parsing AMF0 (Action Message
Format) data structures commonly used in FLV metadata.

Notes
-----
FLV files contain audio and video data with metadata encoded in AMF0 format.
This module handles the low-level parsing and writing of these structures
to enable joining multiple FLV segments into a single file.
"""

from __future__ import annotations

import struct
from io import BytesIO
from typing import Any, BinaryIO, Callable

TAG_TYPE_METADATA: int = 18

##################################################
# AMF0
##################################################

AMF_TYPE_NUMBER: int = 0x00
AMF_TYPE_BOOLEAN: int = 0x01
AMF_TYPE_STRING: int = 0x02
AMF_TYPE_OBJECT: int = 0x03
AMF_TYPE_MOVIECLIP: int = 0x04
AMF_TYPE_NULL: int = 0x05
AMF_TYPE_UNDEFINED: int = 0x06
AMF_TYPE_REFERENCE: int = 0x07
AMF_TYPE_MIXED_ARRAY: int = 0x08
AMF_TYPE_END_OF_OBJECT: int = 0x09
AMF_TYPE_ARRAY: int = 0x0A
AMF_TYPE_DATE: int = 0x0B
AMF_TYPE_LONG_STRING: int = 0x0C
AMF_TYPE_UNSUPPORTED: int = 0x0D
AMF_TYPE_RECORDSET: int = 0x0E
AMF_TYPE_XML: int = 0x0F
AMF_TYPE_CLASS_OBJECT: int = 0x10
AMF_TYPE_AMF3_OBJECT: int = 0x11


class ECMAObject:
    """
    ECMA Array object for AMF0 data structures.

    An ordered dictionary-like structure that maintains both insertion order
    and key-value mapping, used in AMF0 mixed arrays.

    Parameters
    ----------
    max_number : int
        The maximum number of elements expected in the array.

    Attributes
    ----------
    max_number : int
        The maximum number of elements in the array.
    data : list[tuple[str, Any]]
        Ordered list of key-value pairs.
    map : dict[str, Any]
        Dictionary mapping keys to values for fast lookup.
    """

    def __init__(self, max_number: int) -> None:
        self.max_number: int = max_number
        self.data: list[tuple[str, Any]] = []
        self.map: dict[str, Any] = {}

    def put(self, k: str, v: Any) -> None:
        """
        Add a key-value pair to the object.

        Parameters
        ----------
        k : str
            The key to add.
        v : Any
            The value associated with the key.
        """
        self.data.append((k, v))
        self.map[k] = v

    def get(self, k: str) -> Any:
        """
        Get a value by key.

        Parameters
        ----------
        k : str
            The key to look up.

        Returns
        -------
        Any
            The value associated with the key.
        """
        return self.map[k]

    def set(self, k: str, v: Any) -> None:
        """
        Set an existing key to a new value.

        Parameters
        ----------
        k : str
            The key to update.
        v : Any
            The new value.

        Raises
        ------
        KeyError
            If the key does not exist in the object.
        """
        for i in range(len(self.data)):
            if self.data[i][0] == k:
                self.data[i] = (k, v)
                break
        else:
            raise KeyError(k)
        self.map[k] = v

    def keys(self) -> list[str]:
        """
        Get all keys in the object.

        Returns
        -------
        list[str]
            A list of all keys.
        """
        return list(self.map.keys())

    def __str__(self) -> str:
        """Return a string representation of the ECMAObject."""
        return 'ECMAObject<' + repr(self.map) + '>'

    def __eq__(self, other: object) -> bool:
        """Check equality with another ECMAObject."""
        if not isinstance(other, ECMAObject):
            return NotImplemented
        return self.max_number == other.max_number and self.data == other.data


def read_amf_number(stream: BinaryIO) -> float:
    """
    Read an AMF0 number (64-bit IEEE 754 double) from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    float
        The decoded number value.
    """
    return struct.unpack('>d', stream.read(8))[0]


def read_amf_boolean(stream: BinaryIO) -> bool:
    """
    Read an AMF0 boolean value from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    bool
        The decoded boolean value.
    """
    b = read_byte(stream)
    assert b in (0, 1)
    return bool(b)


def read_amf_string(stream: BinaryIO) -> str | None:
    """
    Read an AMF0 string from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    str or None
        The decoded UTF-8 string, or None if the stream is empty
        (dirty fix for invalid Qiyi FLV files).
    """
    xx = stream.read(2)
    if xx == b'':
        # dirty fix for the invalid Qiyi flv
        return None
    n = struct.unpack('>H', xx)[0]
    s = stream.read(n)
    assert len(s) == n
    return s.decode('utf-8')


def read_amf_object(stream: BinaryIO) -> dict[str, Any]:
    """
    Read an AMF0 object from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    dict[str, Any]
        A dictionary containing the object's key-value pairs.
    """
    obj: dict[str, Any] = {}
    while True:
        k = read_amf_string(stream)
        if not k:
            assert read_byte(stream) == AMF_TYPE_END_OF_OBJECT
            break
        v = read_amf(stream)
        obj[k] = v
    return obj


def read_amf_mixed_array(stream: BinaryIO) -> ECMAObject:
    """
    Read an AMF0 mixed array (ECMA array) from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    ECMAObject
        An ECMAObject containing the mixed array data.
    """
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


def read_amf_array(stream: BinaryIO) -> list[Any]:
    """
    Read an AMF0 strict array from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    list[Any]
        A list containing the array elements.
    """
    n = read_uint(stream)
    v: list[Any] = []
    for _ in range(n):
        v.append(read_amf(stream))
    return v


amf_readers: dict[int, Callable[[BinaryIO], Any]] = {
    AMF_TYPE_NUMBER: read_amf_number,
    AMF_TYPE_BOOLEAN: read_amf_boolean,
    AMF_TYPE_STRING: read_amf_string,
    AMF_TYPE_OBJECT: read_amf_object,
    AMF_TYPE_MIXED_ARRAY: read_amf_mixed_array,
    AMF_TYPE_ARRAY: read_amf_array,
}


def read_amf(stream: BinaryIO) -> Any:
    """
    Read an AMF0 value from a stream.

    Reads the type marker byte and dispatches to the appropriate reader.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    Any
        The decoded AMF0 value.
    """
    return amf_readers[read_byte(stream)](stream)


def write_amf_number(stream: BinaryIO, v: float) -> None:
    """
    Write an AMF0 number to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    v : float
        The number value to write.
    """
    stream.write(struct.pack('>d', v))


def write_amf_boolean(stream: BinaryIO, v: bool) -> None:
    """
    Write an AMF0 boolean to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    v : bool
        The boolean value to write.
    """
    if v:
        stream.write(b'\x01')
    else:
        stream.write(b'\x00')


def write_amf_string(stream: BinaryIO, s: str) -> None:
    """
    Write an AMF0 string to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    s : str
        The string to write.
    """
    encoded = s.encode('utf-8')
    stream.write(struct.pack('>H', len(encoded)))
    stream.write(encoded)


def write_amf_object(stream: BinaryIO, o: dict[str, Any]) -> None:
    """
    Write an AMF0 object to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    o : dict[str, Any]
        The dictionary object to write.
    """
    for k in o:
        write_amf_string(stream, k)
        write_amf(stream, o[k])
    write_amf_string(stream, '')
    write_byte(stream, AMF_TYPE_END_OF_OBJECT)


def write_amf_mixed_array(stream: BinaryIO, o: ECMAObject) -> None:
    """
    Write an AMF0 mixed array to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    o : ECMAObject
        The ECMAObject to write.
    """
    write_uint(stream, o.max_number)
    for k, v in o.data:
        write_amf_string(stream, k)
        write_amf(stream, v)
    write_amf_string(stream, '')
    write_byte(stream, AMF_TYPE_END_OF_OBJECT)


def write_amf_array(stream: BinaryIO, o: list[Any]) -> None:
    """
    Write an AMF0 strict array to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    o : list[Any]
        The list to write.
    """
    write_uint(stream, len(o))
    for v in o:
        write_amf(stream, v)


amf_writers_tags: dict[type, int] = {
    float: AMF_TYPE_NUMBER,
    bool: AMF_TYPE_BOOLEAN,
    str: AMF_TYPE_STRING,
    dict: AMF_TYPE_OBJECT,
    ECMAObject: AMF_TYPE_MIXED_ARRAY,
    list: AMF_TYPE_ARRAY,
}

amf_writers: dict[int, Callable[[BinaryIO, Any], None]] = {
    AMF_TYPE_NUMBER: write_amf_number,
    AMF_TYPE_BOOLEAN: write_amf_boolean,
    AMF_TYPE_STRING: write_amf_string,
    AMF_TYPE_OBJECT: write_amf_object,
    AMF_TYPE_MIXED_ARRAY: write_amf_mixed_array,
    AMF_TYPE_ARRAY: write_amf_array,
}


def write_amf(stream: BinaryIO, v: Any) -> None:
    """
    Write an AMF0 value to a stream.

    Determines the appropriate type tag and writer based on the value type.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    v : Any
        The value to write.
    """
    if isinstance(v, ECMAObject):
        tag = amf_writers_tags[ECMAObject]
    else:
        tag = amf_writers_tags[type(v)]
    write_byte(stream, tag)
    amf_writers[tag](stream, v)

##################################################
# FLV
##################################################


# Type alias for FLV tags
FLVTag = tuple[int, int, int, bytes, int]


def read_int(stream: BinaryIO) -> int:
    """
    Read a signed 32-bit big-endian integer from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    int
        The decoded signed integer.
    """
    return struct.unpack('>i', stream.read(4))[0]


def read_uint(stream: BinaryIO) -> int:
    """
    Read an unsigned 32-bit big-endian integer from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    int
        The decoded unsigned integer.
    """
    return struct.unpack('>I', stream.read(4))[0]


def write_uint(stream: BinaryIO, n: int) -> None:
    """
    Write an unsigned 32-bit big-endian integer to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    n : int
        The unsigned integer to write.
    """
    stream.write(struct.pack('>I', n))


def read_byte(stream: BinaryIO) -> int:
    """
    Read a single byte from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    int
        The byte value (0-255).
    """
    return ord(stream.read(1))


def write_byte(stream: BinaryIO, b: int) -> None:
    """
    Write a single byte to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    b : int
        The byte value to write (0-255).
    """
    stream.write(bytes([b]))


def read_unsigned_medium_int(stream: BinaryIO) -> int:
    """
    Read an unsigned 24-bit big-endian integer from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    int
        The decoded 24-bit unsigned integer.
    """
    x1, x2, x3 = struct.unpack('BBB', stream.read(3))
    return (x1 << 16) | (x2 << 8) | x3


def read_tag(stream: BinaryIO) -> FLVTag | None:
    """
    Read an FLV tag from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    FLVTag or None
        A tuple of (data_type, timestamp, body_size, body, previous_tag_size),
        or None if end of stream is reached.

    Raises
    ------
    AssertionError
        If the tag body size exceeds 128MB or if the stream ID is non-zero.
    """
    # header size: 15 bytes
    header = stream.read(15)
    if len(header) == 4:
        return None
    x = struct.unpack('>IBBBBBBBBBBB', header)
    previous_tag_size = x[0]
    data_type = x[1]
    body_size = (x[2] << 16) | (x[3] << 8) | x[4]
    assert body_size < 1024 * 1024 * 128, 'tag body size too big (> 128MB)'
    timestamp = (x[5] << 16) | (x[6] << 8) | x[7]
    timestamp += x[8] << 24
    assert x[9:] == (0, 0, 0)
    body = stream.read(body_size)
    return (data_type, timestamp, body_size, body, previous_tag_size)


def write_tag(stream: BinaryIO, tag: FLVTag) -> None:
    """
    Write an FLV tag to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    tag : FLVTag
        A tuple of (data_type, timestamp, body_size, body, previous_tag_size).
    """
    data_type, timestamp, body_size, body, previous_tag_size = tag
    write_uint(stream, previous_tag_size)
    write_byte(stream, data_type)
    write_byte(stream, body_size >> 16 & 0xff)
    write_byte(stream, body_size >> 8 & 0xff)
    write_byte(stream, body_size & 0xff)
    write_byte(stream, timestamp >> 16 & 0xff)
    write_byte(stream, timestamp >> 8 & 0xff)
    write_byte(stream, timestamp & 0xff)
    write_byte(stream, timestamp >> 24 & 0xff)
    stream.write(b'\0\0\0')
    stream.write(body)


def read_flv_header(stream: BinaryIO) -> None:
    """
    Read and validate an FLV file header.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Raises
    ------
    AssertionError
        If the header is invalid or has unexpected values.
    """
    assert stream.read(3) == b'FLV'
    header_version = read_byte(stream)
    assert header_version == 1
    type_flags = read_byte(stream)
    assert type_flags == 5
    data_offset = read_uint(stream)
    assert data_offset == 9


def write_flv_header(stream: BinaryIO) -> None:
    """
    Write an FLV file header to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    """
    stream.write(b'FLV')
    write_byte(stream, 1)
    write_byte(stream, 5)
    write_uint(stream, 9)


def read_meta_data(stream: BinaryIO) -> tuple[Any, Any]:
    """
    Read FLV metadata from a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to read from.

    Returns
    -------
    tuple[Any, Any]
        A tuple of (meta_type, meta_data).
    """
    meta_type = read_amf(stream)
    meta = read_amf(stream)
    return meta_type, meta


def read_meta_tag(tag: FLVTag) -> tuple[Any, Any]:
    """
    Parse metadata from an FLV tag.

    Parameters
    ----------
    tag : FLVTag
        The FLV tag containing metadata.

    Returns
    -------
    tuple[Any, Any]
        A tuple of (meta_type, meta_data).

    Raises
    ------
    AssertionError
        If the tag is not a metadata tag or has unexpected values.
    """
    data_type, timestamp, body_size, body, previous_tag_size = tag
    assert data_type == TAG_TYPE_METADATA
    assert timestamp == 0
    assert previous_tag_size == 0
    return read_meta_data(BytesIO(body))


def write_meta_tag(stream: BinaryIO, meta_type: Any, meta_data: Any) -> None:
    """
    Write a metadata tag to a stream.

    Parameters
    ----------
    stream : BinaryIO
        The binary stream to write to.
    meta_type : Any
        The metadata type identifier.
    meta_data : Any
        The metadata content.
    """
    buffer = BytesIO()
    write_amf(buffer, meta_type)
    write_amf(buffer, meta_data)
    body = buffer.getvalue()
    write_tag(stream, (TAG_TYPE_METADATA, 0, len(body), body, 0))


##################################################
# main
##################################################


def guess_output(inputs: list[str]) -> str:
    """
    Guess an output filename based on common prefix of input filenames.

    Parameters
    ----------
    inputs : list[str]
        List of input file paths.

    Returns
    -------
    str
        A suggested output filename with '.flv' extension.
    """
    import os.path
    basenames = list(map(os.path.basename, inputs))
    n = min(map(len, basenames))
    for i in reversed(range(1, n)):
        if len(set(s[:i] for s in basenames)) == 1:
            return basenames[0][:i] + '.flv'
    return 'output.flv'


def concat_flv(flvs: list[str], output: str | None = None) -> str:
    """
    Concatenate multiple FLV files into a single file.

    Reads multiple FLV files, merges their metadata (updating total duration),
    and writes all tags to a single output file with adjusted timestamps.

    Parameters
    ----------
    flvs : list[str]
        List of input FLV file paths.
    output : str or None, optional
        Output file path. If None, a filename is guessed from inputs.
        If a directory, the guessed filename is placed in that directory.

    Returns
    -------
    str
        The path to the output file.

    Raises
    ------
    AssertionError
        If no FLV files are provided or if metadata types don't match.
    """
    assert flvs, 'no flv file found'
    import os.path
    if not output:
        output = guess_output(flvs)
    elif os.path.isdir(output):
        output = os.path.join(output, guess_output(flvs))

    print('Merging video parts...')
    ins = [open(flv, 'rb') for flv in flvs]
    for stream in ins:
        read_flv_header(stream)
    meta_tags = map(read_tag, ins)
    metas = list(map(read_meta_tag, meta_tags))
    meta_types, metas = zip(*metas)
    assert len(set(meta_types)) == 1
    meta_type = meta_types[0]

    # must merge fields: duration
    # TODO: check other meta info, update other meta info
    total_duration = sum(meta.get('duration') for meta in metas)
    meta_data = metas[0]
    meta_data.set('duration', total_duration)

    out = open(output, 'wb')
    write_flv_header(out)
    write_meta_tag(out, meta_type, meta_data)
    timestamp_start = 0
    for stream in ins:
        while True:
            tag = read_tag(stream)
            if tag:
                data_type, timestamp, body_size, body, previous_tag_size = tag
                timestamp += timestamp_start
                tag = data_type, timestamp, body_size, body, previous_tag_size
                write_tag(out, tag)
            else:
                break
        timestamp_start = timestamp
    write_uint(out, previous_tag_size)

    return output


def usage() -> None:
    """Print usage information for the command-line interface."""
    print('Usage: [python3] join_flv.py --output TARGET.flv flv...')


def main() -> None:
    """
    Main entry point for the FLV joining command-line tool.

    Parses command-line arguments and invokes the FLV concatenation.
    """
    import getopt
    import sys
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:", ["help", "output="])
    except getopt.GetoptError:
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

    concat_flv(args, output)


if __name__ == '__main__':
    main()
