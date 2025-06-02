#!/usr/bin/env python

"""
join_flv.py - Join FLV files into a single file.

This module provides functions for joining FLV files.

The module contains functions for reading and writing FLV files, as well as
functions for reading and writing AMF data.

The module is intended for use in video streaming applications, specifically for
joining FLV files into a single file.

The module is compatible with Python 3.6 and above.

Example usage:

    python join_flv.py --output output.flv input1.flv input2.flv

For more information, see the documentation at https://github.com/soimort/you-get.
"""

import struct
from typing import Any, BinaryIO, Dict, List, Optional, Tuple
from io import BytesIO
import io
import sys

TAG_TYPE_METADATA = 18

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
    def __init__(self, max_number):
        self.max_number = max_number
        self.data = []
        self.map = {}

    def put(self, k: str, v: Any) -> None:
        """
        Puts a key-value pair into the ECMAObject.

        Args:
            k (str): The key of the pair.
            v (Any): The value of the pair.
        """
        self.data.append((k, v))
        self.map[k] = v

    def get(self, k):
        return self.map.get(k)

    def set(self, k, v):
        for i in range(len(self.data)):
            if self.data[i][0] == k:
                self.data[i] = (k, v)
                break
        else:
            raise KeyError(f"Key '{k}' not found in ECMAObject. Available keys: {list(self.map.keys())}")
        self.map[k] = v

    def keys(self):
        return list(self.map.keys())

    def __str__(self):
        return 'ECMAObject<' + repr(self.map) + '>'

    def __eq__(self, other):
        return self.max_number == other.max_number and self.data == other.data


def read_amf_number(stream: BinaryIO) -> float:
    """Reads an AMF number (double precision) from a binary stream.

    Args:
        stream (BinaryIO): The input stream to read from.

    Returns:
        float: The unpacked AMF number.

    Raises:
        ValueError: If the stream does not contain enough data.
    """
    data = stream.read(8)
    if len(data) < 8:
        raise ValueError("Insufficient data to unpack AMF number.")
    return struct.unpack('>d', data)[0]


def read_amf_boolean(stream: BinaryIO) -> bool:
    """
    Reads a boolean value (0 or 1) from the binary stream and returns it
    as a boolean.

    Args:
        stream (BinaryIO): The binary stream to read from.
    
    Returns:
        bool: The boolean value corresponding to the byte read.
    """
    b = read_byte(stream)
    assert b in (0, 1), f"Expected 0 or 1, got {b}"
    return bool(b)


def read_amf_key(
    stream: BinaryIO) -> Optional[str]:
    k = read_amf_string(stream)
    if not k and read_byte(stream) != AMF_TYPE_END_OF_OBJECT:
        raise ValueError("Expected end of object marker after an empty key.")
    return k


def read_amf_string(stream: BinaryIO) -> str:
    xx = stream.read(2)
    if xx == b'':
        # dirty fix for the invalid Qiyi flv
        return None
    n = struct.unpack('>H', xx)[0]
    s = stream.read(n)
    assert len(s) == n
    return s.decode('utf-8')


def read_amf_object(stream: BinaryIO) -> Dict[str, Any]:
    """
    Reads an AMF object from the stream and returns a dictionary containing the parsed data.

    Args:
        stream (BinaryIO): The input stream to read from.

    Returns:
        Dict[str, Any]: A dictionary containing the parsed data.
    """
    obj: Dict[str, Any] = {}
    while True:
        # Read the key (AMFF string)
        k = read_amf_key(stream)
        # Read the value stored in the dictionary.
        v = read_amf(stream)
        obj[k] = v
    return obj


def read_amf_mixed_array(
    stream: BinaryIO
) -> ECMAObject:
    """
    Reads an AMF mixed array from the stream and returns an ECMAObject containing the parsed data.

    Args:
        stream (BinaryIO): The input stream to read from.

    Returns:
        ECMAObject: An ECMAObject containing the parsed data.
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


def read_amf_array(
    stream: BinaryIO
) -> List[Any]:
    """
    Reads an AMF array from the stream and returns a list containing the parsed data.

    Args:
        stream (BinaryIO): The input stream to read from.

    Returns:
        List[Any]: A list containing the parsed data.
    """
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


def read_amf(stream: BinaryIO) -> Any:
    """
    Reads an AMF object from the stream and returns the parsed data.

    Args:
        stream (BinaryIO): The input stream to read from.

    Returns:
        Any: The parsed data.
    """
    return amf_readers[read_byte(stream)](stream)


def write_amf_number(stream: BinaryIO, v: float) -> None:
    """
    Writes a doible-precision floating-point number to the binary stream.

    Args:
        stream (BinaryIO): The binary stream to write to.
        v (float): The number to write.
    """
    stream.write(struct.pack('>d', v))


def write_amf_boolean(stream: BinaryIO, v: bool) -> None:
    """
    Writes a boolean value to the binary stream.

    Args:
        stream (BinaryIO): The binary stream to write to.
        v (bool): The boolean value to write.
    """
    if v:
        stream.write(b'\x01')
    else:
        stream.write(b'\x00')


def write_amf_string(stream: BinaryIO, s: str) -> None:
    """
    Writes a string to the binary stream.

    Args:
        stream (BinaryIO): The binary stream to write to.
        s (str): The string to write.
    """
    s = s.encode('utf-8', 'strict')
    stream.write(struct.pack('>H', len(s)))
    stream.write(s)


def write_amf_object(stream: BinaryIO, o: Dict[str, Any]) -> None:
    """
    Writes an AMF object to the binary stream.

    Args:
        stream (BinaryIO): The binary stream to write to.
        o (Dict[str, Any]): The object to write.
    """
    for k in o:
        write_amf_string(stream, k)
        write_amf(stream, o[k])
    write_amf_string(stream, '')
    write_byte(stream, AMF_TYPE_END_OF_OBJECT)


def write_amf_mixed_array(stream: BinaryIO, o: ECMAObject) -> None:
    """
    Writes an AMF mixed array to the binary stream.

    Args:
        stream (BinaryIO): The binary stream to write to.
        o (ECMAObject): The mixed array to write.
    """
    write_uint(stream, o.max_number)
    for k, v in o.data:
        write_amf_string(stream, k)
        write_amf(stream, v)
    write_amf_string(stream, '')
    write_byte(stream, AMF_TYPE_END_OF_OBJECT)


def write_amf_array(stream: BinaryIO, o: List[Any]) -> None:
    """
    Writes an AMF array to the binary stream.

    Args:
        stream (BinaryIO): The binary stream to write to.
        o (List[Any]): The array to write.
    """
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


def write_amf(stream: BinaryIO, v: Any) -> None:
    # Check the type of the value and find the appropriate tag
    if isinstance(v, ECMAObject):
        tag = amf_writers_tags[ECMAObject]
    else:
        tag = amf_writers_tags[type(v)]
    # Write the tag to the stream
    write_byte(stream, tag)
    amf_writers[tag](stream, v)

##################################################
# FLV
##################################################


def read_int(stream: BinaryIO) -> int:
    return struct.unpack('>i', stream.read(4))[0]


def read_uint(stream: BinaryIO) -> int:
    return struct.unpack('>I', stream.read(4))[0]


def write_uint(
    stream: io.BufferedIOBase,
    n: int,
    endian: str = 'big',
) -> None:
    if not isinstance(stream, io.BufferedIOBase):
        raise TypeError(f"Expected a file-like object, got {type(stream)}")
    stream.write(struct.pack(f'>{endian}I', n))


def read_byte(
    stream: BinaryIO
) -> int:
    return ord(stream.read(1))


def write_byte(stream: BinaryIO, b: int) -> None:
    stream.write(bytes([b]))


def read_unsigned_medium_int(stream: BinaryIO) -> int:
    """Reads an unsigned medium integer from the stream"""
    x1, x2, x3 = struct.unpack('BBB', stream.read(3))
    return (x1 << 16) | (x2 << 8) | x3


def read_tag(stream: BinaryIO) -> Tuple[int, int, int, bytes, int]:
    """
    Reads a FLV tag header from the stream and returns a tuple containing the
    data type, timestamp, body size, body, and previous tag size.

    Args:
        stream (BinaryIO): The input stream to read from.

    Returns:
        Tuple[int, int, int, bytes, int]: A tuple containing the data type,
        timestamp, body size, body, and previous tag size.

    Raises:
        ValueError: If the stream does not contain enough data to read the
        header.
    """
    # header size: 15 bytes
    header = stream.read(15)
    if len(header) < 15:
        raise ValueError(
            f"Incomplete FLV tag header. Expected 15 bytes, "
            f"got {len(header)} bytes"
        )
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
    #previous_tag_size = read_uint(stream)
    #data_type = read_byte(stream)
    #body_size = read_unsigned_medium_int(stream)
    #assert body_size < 1024*1024*128, 'tag body size too big (> 128MB)'
    #timestamp = read_unsigned_medium_int(stream)
    #timestamp += read_byte(stream) << 24
    #assert read_unsigned_medium_int(stream) == 0
    #body = stream.read(body_size)
    #return (data_type, timestamp, body_size, body, previous_tag_size)


def write_tag(
    stream: BinaryIO, tag: Tuple[int, int, int, bytes, int]
) -> None:
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


def read_flv_header(stream: BinaryIO) -> None:
    """
    Reads and validates the FLV header from the given binary stream.

    This function checks that the stream begins with the FLV header and
    validates the header version, type flags, and data offset.

    Args:
        stream (BinaryIO): The input stream to read from.

    Raises:
        AssertionError: If the stream does not begin with the FLV header or
        if the header version, type flags, or data offset are invalid.
    """
    assert stream.read(3) == b'FLV'
    header_version = read_byte(stream)
    assert header_version == 1, f"Unsupported FLV header version: {header_version}"
    type_flags = read_byte(stream)
    assert type_flags == 5, f"Unsupported FLV type flags: {type_flags}"
    data_offset = read_uint(stream)
    assert data_offset == 9, f"Unsupported FLV data offset: {data_offset}"


def write_flv_header(stream: BinaryIO) -> None:
    stream.write(b'FLV')
    write_byte(stream, 1)
    write_byte(stream, 5)
    write_uint(stream, 9)


def read_meta_data(stream: BinaryIO) -> Tuple[str, Any]:
    """
    Reads metadata from the given binary stream and returns a tuple containing
    the metadata type and the metadata.

    Args:
        stream (BinaryIO): The input stream to read from.

    Returns:
        Tuple[str, Any]: A tuple containing the metadata type and the metadata.
    """
    meta_type = read_amf(stream)
    meta = read_amf(stream)
    return meta_type, meta


def read_meta_tag(tag: Tuple[int, int, int, bytes, int]) -> Tuple[str, Any]:
    data_type, timestamp, body_size, body, previous_tag_size = tag
    assert data_type == TAG_TYPE_METADATA
    assert timestamp == 0
    assert previous_tag_size == 0
    return read_meta_data(BytesIO(body))


#def write_meta_data(stream, meta_type, meta_data):
#    assert isinstance(meta_type, basesting)
#    write_amf(meta_type)
#    write_amf(meta_data)


def write_meta_tag(stream: BinaryIO, meta_type: Any, meta_data: Any) -> None:
    """
    Writes metadata to the given binary stream.

    Args:
        stream (BinaryIO): The output stream to write to.
        meta_type (Any): The metadata type.
        meta_data (Any): The metadata.
    """
    buffer = BytesIO()
    write_amf(buffer, meta_type)
    write_amf(buffer, meta_data)
    body = buffer.getvalue()
    write_tag(stream, (TAG_TYPE_METADATA, 0, len(body), body, 0))


##################################################
# main
##################################################


def guess_output(inputs: List[str]) -> str:
    """
    Guesses the common prefix of the input file paths (excluding directories) and
    returns the base filename with a '.flv' extension. If no common prefix is found,
    returns 'output.flv'.

    Args:
        inputs (List[str]): A list of input file paths.

    Returns:
        str: The output file path.
    """
    import os.path
    inputs = map(os.path.basename, inputs)
    n = min(map(len, inputs))
    for i in reversed(range(1, n)):
        if len(set(s[:i] for s in inputs)) == 1:
            return inputs[0][:i] + '.flv'
    return 'output.flv'


def validate_concat_flv_input(inputs: List[str]) -> None:
    """
    Validates the input files for concatenation.

    Args:
        inputs (List[str]): A list of input file paths.
    
    Raises:
        ValueError: If the input files are not valid FLV files.
    """
    import os.path
    for flv in inputs:
        if not os.path.exists(flv):
            raise ValueError(f"File not found: {flv}")
        if not os.path.isfile(flv):
            raise ValueError(f"Not a valid file: {flv}")
        with open(flv, "rb") as stream:
            header = stream.read(3)
            if header != b'FLV':
                raise ValueError(f"Not a valid FLV file: {flv}")


def concat_flv(flvs: List[str], output: Optional[str] = None) -> str:
    """
    Concatenates multiple FLV files into a single FLV file.

    Args:
        flvs (List[str]): A list of FLV file paths to be concatenated.
        output (Optional[str], optional): The output file path. Defaults to None.

    Returns:
        str: The output file path.
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
    print('Usage: [python3] join_flv.py --output TARGET.flv flv...')


def main() -> None:
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:", ["help", "output="])
    except getopt.GetoptError as err:
        usage()
        sys.exit(1)
    output = None
    for option, argument in opts:
        if option in ("-h", "--help"):
            usage()
            sys.exit()
        elif option in ("-o", "--output"):
            output = argument
        else:
            usage()
            sys.exit(1)
    if not args:
        usage()
        sys.exit(1)
    
    concat_flv(args, output)


if __name__ == '__main__':
    main()
