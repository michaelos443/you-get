#!/usr/bin/env python

# reference: c041828_ISO_IEC_14496-12_2005(E).pdf

##################################################
# reader and writer
##################################################

import contextlib
import struct
from typing import BinaryIO, List, Optional, Tuple, Callable, Dict
import io
from io import BytesIO, BufferedReader

MAX_READ_LIMIT = 1024 * 8

def skip(stream: BinaryIO, n: int) -> None:
    """
    Skips `n` bytes in the stream.
    """
    stream.seek(stream.tell() + n)

def skip_zeros(stream: BinaryIO, n: int) -> None:
    """
    Skips `n` zeros in the stream.
    """
    data = stream.read(n)
    assert data == b'\x00' * n, f"Expected {n} zeros, but got {data}"

def read_int(stream: BinaryIO) -> int:
    """Reads a signed 4-byte integer from the stream in big-endian order."""
    return struct.unpack('>i', stream.read(4))[0]

def read_uint(stream: BinaryIO) -> int:
    """
    Reads a 4-byte unsigned integer from the stream in big-endian order.
    """
    return struct.unpack('>I', stream.read(4))[0]

def write_uint(stream: BinaryIO, n: int) -> None:
    """
    Writes a 4-byte unsigned integer to the stream in big-endian order.
    """
    stream.write(struct.pack('>I', n))

def write_ulong(stream: BinaryIO, n: int) -> None:
    """
    Writes an 8-byte unsigned long integer to the stream in big-endian order.
    """
    stream.write(struct.pack('>Q', n))

def read_ushort(stream: BinaryIO) -> int:
    """
    Reads a 2-byte unsigned short integer from the stream in big-endian order.
    """
    return struct.unpack('>H', stream.read(2))[0]

def read_ulong(stream: BinaryIO) -> int:
    """
    Reads an 8-byte unsigned long integer from the stream in big-endian order.
    """
    return struct.unpack('>Q', stream.read(8))[0]

def read_byte(stream: BinaryIO) -> int:
    """
    Reads a single byte from the stream.
    """
    return ord(stream.read(1))

def copy_stream(source: BinaryIO, target: BinaryIO, n: int) -> None:
    """
    Copies `n` bytes from the source stream to the target stream using a buffer.
    Ensures minimal memory usage by reading in chunks.
    """
    buffer_size = min(1024 * 1024, n)
    while n > 0:
        to_read = min(buffer_size, n)  # Determine how many bytes to read.
        s = source.read(min(to_read, MAX_READ_LIMIT))
        if not s:  # Check for the end of stream.
            raise EOFError('Source stream ended before reading required bytes.')

        target.write(s)  # Write the data to the target stream.
        n -= len(s)  # Update the remaining bytes to read.

class Atom:
    def __init__(self, atom_type: bytes, size: int, body: bytes):
        """
        Initializes an Atom object with the given type, size, and body.
        """
        assert len(atom_type) == 4
        self.type = atom_type
        self.size = size
        self.body = body
    def __str__(self) -> str:
        return f'<Atom({self.type}):{self.body}>'
    def __repr__(self) -> str:
        return str(self)
    def write1(self, stream: BinaryIO) -> None:
        """
        Writes the size and type of the atom to the stream.
        """
        write_uint(stream, self.size)
        stream.write(self.type)
    def write(self, stream: BinaryIO) -> None:
        """
        Writes the body of the atom to the stream.
        """
        assert type(self.body) == bytes, '%s: %s' % (self.type, type(self.body))
        assert self.size == 8 + len(self.body)
        self.write1(stream)
        stream.write(self.body)
    def calsize(self):
        return self.size

class CompositeAtom(Atom):
    def __init__(self, type, size, body):
        assert isinstance(body, list)
        super().__init__(type, size, body)
    def write(self, stream):
        assert type(self.body) == list
        self.write1(stream)
        for atom in self.body:
            atom.write(stream)
    def calsize(self):
        self.size = 8 + sum([atom.calsize() for atom in self.body])
        return self.size
    def get1(self, k):
        for a in self.body:
            if a.type == k:
                return a
        else:
            raise ValueError(f'Atom with type {k} not found')
    def get(self, *keys):
        atom = self
        for k in keys:
            atom = atom.get1(k)
        return atom
    def get_all(self, k):
        return [atom for atom in self.body if atom.type == k]
        #return list(filter(lambda x: x.type == k, self.body))

class VariableAtom(Atom):
    def __init__(self, type, size, body, variables):
        assert isinstance(body, bytes)
        super().__init__(type, size, body)
        self.variables = variables
    def write(self, stream):
        self.write1(stream)
        i = 0
        n = 0
        for name, offset, value, bsize in self.variables:
            stream.write(self.body[i:offset])
            if bsize == 4:
                write_uint(stream, value)
            elif bsize == 8:
                write_ulong(stream, value)
            else:
                raise NotImplementedError()
            n += offset - i + bsize
            i = offset + bsize
        stream.write(self.body[i:])
        n += len(self.body) - i
        assert n == len(self.body)
    def get(self, k):
        for v in self.variables:
            if v[0] == k:
                return v[2]
        else:
            raise Exception('field not found: ' + k)
    def set(self, k, v):
        for i in range(len(self.variables)):
            variable = self.variables[i]
            if variable[0] == k:
                self.variables[i] = (k, variable[1], v, variable[3])
                break
        else:
            raise Exception('field not found: '+k)

def read_raw(stream: BinaryIO, size: int, left: int, type_: str) -> Atom:
    """
    Reads a raw chunk of data from the stream and returns an Atom object.

    Args:
        stream (BinaryIO): The input stream to read from (e.g., a file-like object)
        size (int): The total size of the raw data.
        left (int): The number of bytes left to read from the stream.
        type (str): The type identifier of the raw data.

    Returns:
        Atom: An Atom object containing the type, size and raw body of the data.
    """
    # Assert that the size is valid.
    assert size == left + 8
    # Read the 'left' number of bytes from the stream.
    body = stream.read(left)
    # Return an Atom object containing the type, size and body data.
    return Atom(type_, size, body)

def read_udta(stream: BinaryIO, size: int, left: int, type: str) -> Atom:
    """
    Reads a raw chunk of data from the stream and returns an Atom object.

    Args:
        stream (BinaryIO): The input stream to read from (e.g., a file-like object)
        size (int): The total size of the raw data.
        left (int): The number of bytes left to read from the stream.
        type (str): The type identifier of the raw data.

    Returns:
        Atom: An Atom object containing the type, size and raw body of the data.
    """
    assert size == left + 8
    body = stream.read(left)
    class Udta(Atom):
        def write(self, stream):
            return
        def calsize(self):
            return 0
    return Udta(type, size, body)

def read_body_stream(stream: BinaryIO, left: int) -> Tuple[bytes, BufferedReader]:
    """
    Reads a body stream from the stream and returns a tuple containing the body and a BufferedReader object.

    Args:
        stream (BinaryIO): The input stream to read from (e.g., a file-like object)
        left (int): The number of bytes left to read from the stream.

    Returns:
        Tuple[bytes, BufferedReader]: A tuple containing the body and a BufferedReader object.
    """
    body = stream.read(left)
    assert len(body) == left, f"Expected {left} bytes, but got {len(body)}"
    return body, BufferedReader(BytesIO(body))

def read_full_atom(stream, return_version=False):
    value = read_uint(stream)
    version = value >> 24
    flags = value & 0xffffff
    return (version, value) if return_version else value

def read_mvhd(stream: BinaryIO, size: int, left: int, type: str) -> Atom:
    """
    Reads a mvhd atom from the stream and returns an Atom object.

    Args:
        stream (BinaryIO): The input stream to read from (e.g., a file-like object)
        size (int): The total size of the atom.
        left (int): The number of bytes left to read from the stream.
        type (str): The type identifier of the atom.

    Returns:
        Atom: An Atom object containing the type, size and body of the mvhd atom.
    """
    body, stream = read_body_stream(stream, left)
    value = read_full_atom(stream)
    left -= 4
    # new Date(movieTime * 1000 - 2082850791998L); 
    creation_time = read_uint(stream)
    modification_time = read_uint(stream)
    time_scale = read_uint(stream)
    duration = read_uint(stream)
    left -= 16
    
    qt_preferred_fate = read_uint(stream)
    qt_preferred_volume = read_ushort(stream)
    assert stream.read(10) == b'\x00' * 10
    qt_matrixA = read_uint(stream)
    qt_matrixB = read_uint(stream)
    qt_matrixU = read_uint(stream)
    qt_matrixC = read_uint(stream)
    qt_matrixD = read_uint(stream)
    qt_matrixV = read_uint(stream)
    qt_matrixX = read_uint(stream)
    qt_matrixY = read_uint(stream)
    qt_matrixW = read_uint(stream)
    qt_previewTime = read_uint(stream)
    qt_previewDuration = read_uint(stream)
    qt_posterTime = read_uint(stream)
    qt_selectionTime = read_uint(stream)
    qt_selectionDuration = read_uint(stream)
    qt_currentTime = read_uint(stream)
    nextTrackID = read_uint(stream)
    left -= 80
    assert left == 0
    return VariableAtom(b'mvhd', size, body, [('duration', 16, duration, 4)])

def read_tkhd(stream, size, left, type):
    body, stream = read_body_stream(stream, left)
    value = read_full_atom(stream)
    left -= 4
    
    # new Date(movieTime * 1000 - 2082850791998L); 
    creation_time = read_uint(stream)
    modification_time = read_uint(stream)
    track_id = read_uint(stream)
    assert stream.read(4) == b'\x00' * 4
    duration = read_uint(stream)
    left -= 20
    
    assert stream.read(8) == b'\x00' * 8
    qt_layer = read_ushort(stream)
    qt_alternate_group = read_ushort(stream)
    qt_volume = read_ushort(stream)
    assert stream.read(2) == b'\x00\x00'
    qt_matrixA = read_uint(stream)
    qt_matrixB = read_uint(stream)
    qt_matrixU = read_uint(stream)
    qt_matrixC = read_uint(stream)
    qt_matrixD = read_uint(stream)
    qt_matrixV = read_uint(stream)
    qt_matrixX = read_uint(stream)
    qt_matrixY = read_uint(stream)
    qt_matrixW = read_uint(stream)
    qt_track_width = read_uint(stream)
    width = qt_track_width >> 16
    qt_track_height = read_uint(stream)
    height = qt_track_height >> 16
    left -= 60
    assert left == 0
    return VariableAtom(b'tkhd', size, body, [('duration', 20, duration, 4)])

def read_mdhd(stream: BinaryIO, size: int, left: int, type: str) -> Atom:
    """
    Reads a mdhd atom from the stream and returns an Atom object.

    Args:
        stream (BinaryIO): The input stream to read from (e.g., a file-like object)
        size (int): The size of the atom.
        left (int): The number of bytes left to read from the stream.
        type (str): The type identifier of the atom.

    Returns:
        Atom: An Atom object representing the mdhd atom.
    """
    body, stream = read_body_stream(stream, left)
    ver, value = read_full_atom(stream, return_version=True)
    left -= 4

    if ver == 1:
        creation_time = read_ulong(stream)
        modification_time = read_ulong(stream)
        time_scale = read_uint(stream)
        duration = read_ulong(stream)
        var = [('duration', 24, duration, 8)]
        left -= 28
    else: 
        assert ver == 0, "ver=%d" % ver
        creation_time = read_uint(stream)
        modification_time = read_uint(stream)
        time_scale = read_uint(stream)
        duration = read_uint(stream)
        var = [('duration', 16, duration, 4)]
        left -= 16
    
    packed_language = read_ushort(stream)
    qt_quality = read_ushort(stream)
    left -= 4
    
    assert left == 0
    return VariableAtom(b'mdhd', size, body, var)

def read_hdlr(stream: BinaryIO, size: int, left: int, atom_type: bytes) -> Atom:
    body, stream = read_body_stream(stream, left)
    value = read_full_atom(stream)
    left -= 4
    
    qt_component_type = read_uint(stream)
    handler_type = read_uint(stream)
    qt_component_manufacturer = read_uint(stream)
    qt_component_flags = read_uint(stream)
    qt_component_flags_mask = read_uint(stream)
    left -= 20
    
    track_name = stream.read(left)
    #assert track_name[-1] == b'\x00'
    
    return Atom(b'hdlr', size, body)

def read_vmhd(stream, size, left, type) -> Atom:
    body, stream = read_body_stream(stream, left)
    value = read_full_atom(stream)
    left -= 4
    
    assert left == 8
    graphic_mode = read_ushort(stream)
    op_color_read = read_ushort(stream)
    op_color_green = read_ushort(stream)
    op_color_blue = read_ushort(stream)
    
    return Atom(b'vmhd', size, body)

def read_stsd(stream, size, left, type):
    value = read_full_atom(stream)
    left -= 4
    
    entry_count = read_uint(stream)
    left -= 4
    
    children = []
    for i in range(entry_count):
        atom = read_atom(stream)
        children.append(atom)
        left -= atom.size
    
    assert left == 0
    #return Atom('stsd', size, children)
    class stsd_atom(Atom):
        def __init__(self, type, size, body):
            super().__init__(type, size, body)
        def write(self, stream):
            self.write1(stream)
            write_uint(stream, self.body[0])
            write_uint(stream, len(self.body[1]))
            for atom in self.body[1]:
                atom.write(stream)
        def calsize(self):
            oldsize = self.size # TODO: remove
            self.size = 8 + 4 + 4 + sum([atom.calsize() for atom in self.body[1]])
            assert oldsize == self.size, '%s: %d, %d' % (self.type, oldsize, self.size) # TODO: remove
            return self.size
    return stsd_atom(b'stsd', size, (value, children))

def read_avc1(stream, size, left, type):
    body, stream = read_body_stream(stream, left)
    
    skip_zeros(stream, 6)
    data_reference_index = read_ushort(stream)
    skip_zeros(stream, 2)
    skip_zeros(stream, 2)
    skip_zeros(stream, 12)
    width = read_ushort(stream)
    height = read_ushort(stream)
    horizontal_rez = read_uint(stream) >> 16
    vertical_rez = read_uint(stream) >> 16
    assert stream.read(4) == b'\x00' * 4
    frame_count = read_ushort(stream)
    string_len = read_byte(stream)
    compressor_name = stream.read(31)
    depth = read_ushort(stream)
    assert stream.read(2) == b'\xff\xff'
    left -= 78
    
    child = read_atom(stream)
    assert child.type in (b'avcC', b'pasp'), 'if the sub atom is not avcC or pasp (actual %s), you should not cache raw body' % child.type
    left -= child.size
    stream.read(left) # XXX
    return Atom(b'avc1', size, body)

def read_avcC(stream, size, left, type):
    stream.read(left)
    return Atom(b'avcC', size, None)

def read_stts(stream, size, left, type):
    value = read_full_atom(stream)
    left -= 4
    
    entry_count = read_uint(stream)
    #assert entry_count == 1
    left -= 4
    
    samples = []
    for i in range(entry_count):
        sample_count = read_uint(stream)
        sample_duration = read_uint(stream)
        samples.append((sample_count, sample_duration))
        left -= 8

    assert left == 0
    #return Atom('stts', size, None)
    class stts_atom(Atom):
        def __init__(self, type, size, body):
            super().__init__(type, size, body)
        def write(self, stream):
            self.write1(stream)
            write_uint(stream, self.body[0])
            write_uint(stream, len(self.body[1]))
            for sample_count, sample_duration in self.body[1]:
                write_uint(stream, sample_count)
                write_uint(stream, sample_duration)
        def calsize(self):
            #oldsize = self.size # TODO: remove
            self.size = 8 + 4 + 4 + len(self.body[1]) * 8
            #assert oldsize == self.size, '%s: %d, %d' % (self.type, oldsize, self.size) # TODO: remove
            return self.size
    return stts_atom(b'stts', size, (value, samples))

def read_stss(stream, size, left, type):
    value = read_full_atom(stream)
    left -= 4
    
    entry_count = read_uint(stream)
    left -= 4
    
    samples = []
    for i in range(entry_count):
            sample = read_uint(stream)
            samples.append(sample)
            left -= 4
    
    assert left == 0
    #return Atom('stss', size, None)
    class stss_atom(Atom):
        def __init__(self, type, size, body):
            super().__init__(type, size, body)
        def write(self, stream):
            self.write1(stream)
            write_uint(stream, self.body[0])
            write_uint(stream, len(self.body[1]))
            for sample in self.body[1]:
                write_uint(stream, sample)
        def calsize(self):
            self.size = 8 + 4 + 4 + len(self.body[1]) * 4
            return self.size
    return stss_atom(b'stss', size, (value, samples))

def read_stsc(stream, size, left, type):
    value = read_full_atom(stream)
    left -= 4
    
    entry_count = read_uint(stream)
    left -= 4
    
    chunks = []
    for i in range(entry_count):
        first_chunk = read_uint(stream)
        samples_per_chunk = read_uint(stream)
        sample_description_index = read_uint(stream)
        assert sample_description_index == 1 # what is it?
        chunks.append((first_chunk, samples_per_chunk, sample_description_index))
        left -= 12
    #chunks, samples = zip(*chunks)
    #total = 0
    #for c, s in zip(chunks[1:], samples):
    #	total += c*s
    #print 'total', total
    
    assert left == 0
    #return Atom('stsc', size, None)
    class stsc_atom(Atom):
        def __init__(self, type, size, body):
            super().__init__(type, size, body)
        def write(self, stream):
            self.write1(stream)
            write_uint(stream, self.body[0])
            write_uint(stream, len(self.body[1]))
            for first_chunk, samples_per_chunk, sample_description_index in self.body[1]:
                write_uint(stream, first_chunk)
                write_uint(stream, samples_per_chunk)
                write_uint(stream, sample_description_index)
        def calsize(self):
            self.size = 8 + 4 + 4 + len(self.body[1]) * 12
            return self.size
    return stsc_atom(b'stsc', size, (value, chunks))

def read_stsz(stream, size, left, type):
    value = read_full_atom(stream)
    left -= 4
    
    sample_size = read_uint(stream)
    sample_count = read_uint(stream)
    left -= 8
    
    assert sample_size == 0
    total = 0
    sizes = []
    if sample_size == 0:
        for i in range(sample_count):
            entry_size = read_uint(stream)
            sizes.append(entry_size)
            total += entry_size
            left -= 4
    
    assert left == 0
    #return Atom('stsz', size, None)
    class stsz_atom(Atom):
        def __init__(self, type, size, body):
            super().__init__(type, size, body)
        def write(self, stream):
            self.write1(stream)
            write_uint(stream, self.body[0])
            write_uint(stream, self.body[1])
            write_uint(stream, self.body[2])
            for entry_size in self.body[3]:
                write_uint(stream, entry_size)
        def calsize(self):
            self.size = 8 + 4 + 8 + len(self.body[3]) * 4
            return self.size
    return stsz_atom(b'stsz', size, (value, sample_size, sample_count, sizes))

def read_stco(stream: BinaryIO, size: int, left: int, atom_type: bytes) -> Atom:
    value = read_full_atom(stream)
    left -= 4
    
    entry_count = read_uint(stream)
    left -= 4
    
    offsets = []
    for i in range(entry_count):
        chunk_offset = read_uint(stream)
        offsets.append(chunk_offset)
        left -= 4
    
    assert left == 0
    #return Atom('stco', size, None)
    class stco_atom(Atom):
        def __init__(self, atom_type, size, body):
            super().__init__(atom_type, size, body)
        def write(self, stream):
            self.write1(stream)
            write_uint(stream, self.body[0])
            write_uint(stream, len(self.body[1]))
            for chunk_offset in self.body[1]:
                write_uint(stream, chunk_offset)
        def calsize(self):
            self.size = 8 + 4 + 4 + len(self.body[1]) * 4
            return self.size
    return stco_atom(b'stco', size, (value, offsets))

def read_ctts(stream, size, left, type):
    value = read_full_atom(stream)
    left -= 4
    
    entry_count = read_uint(stream)
    left -= 4
    
    samples = []
    for i in range(entry_count):
        sample_count = read_uint(stream)
        sample_offset = read_uint(stream)
        samples.append((sample_count, sample_offset))
        left -= 8
    
    assert left == 0
    class ctts_atom(Atom):
        def __init__(self, type, size, body):
            super().__init__(type, size, body)
        def write(self, stream):
            self.write1(stream)
            write_uint(stream, self.body[0])
            write_uint(stream, len(self.body[1]))
            for sample_count, sample_offset in self.body[1]:
                write_uint(stream, sample_count)
                write_uint(stream, sample_offset)
        def calsize(self):
            self.size = 8 + 4 + 4 + len(self.body[1]) * 8
            return self.size
    return ctts_atom(b'ctts', size, (value, samples))

def read_smhd(stream, size, left, type):
    body, stream = read_body_stream(stream, left)
    value = read_full_atom(stream)
    left -= 4
    
    balance = read_ushort(stream)
    assert stream.read(2) == b'\x00\x00'
    left -= 4
    
    assert left == 0
    return Atom(b'smhd', size, body)

def read_mp4a(stream, size, left, type):
    body, stream = read_body_stream(stream, left)
    
    assert stream.read(6) == b'\x00' * 6
    data_reference_index = read_ushort(stream)
    assert stream.read(8) == b'\x00' * 8
    channel_count = read_ushort(stream)
    sample_size = read_ushort(stream)
    assert stream.read(4) == b'\x00' * 4
    time_scale = read_ushort(stream)
    assert stream.read(2) == b'\x00' * 2
    left -= 28
    
    atom = read_atom(stream)
    assert atom.type == b'esds'
    left -= atom.size
    
    assert left == 0
    return Atom(b'mp4a', size, body)

def read_descriptor(stream):
    tag = read_byte(stream)
    raise NotImplementedError()

def read_esds(stream, size, left, type):
    value = read_uint(stream)
    version = value >> 24
    assert version == 0
    flags = value & 0xffffff
    left -= 4
    
    body = stream.read(left)
    return Atom(b'esds', size, None)

def read_composite_atom(stream, size, left, atom_type):
    children = []
    while left > 0:
        atom = read_atom(stream)
        children.append(atom)
        left -= atom.size
    assert left == 0, left
    return CompositeAtom(atom_type, size, children)

def read_mdat(stream, size, left, type):
    source_start = stream.tell()
    source_size = left
    skip(stream, left)
    #return Atom(type, size, None)
    #raise NotImplementedError()
    class mdat_atom(Atom):
        def __init__(self, type, size, body):
            super().__init__(type, size, body)
        def write(self, stream):
            self.write1(stream)
            self.write2(stream)
        def write2(self, stream):
            source, source_start, source_size = self.body
            original = source.tell()
            source.seek(source_start)
            copy_stream(source, stream, source_size)
        def calsize(self):
            return self.size
    return mdat_atom(b'mdat', size, (stream, source_start, source_size))

atom_readers = {
    b'mvhd': read_mvhd, # merge duration
    b'tkhd': read_tkhd, # merge duration
    b'mdhd': read_mdhd, # merge duration
    b'hdlr': read_hdlr, # nothing
    b'vmhd': read_vmhd, # nothing
    b'stsd': read_stsd, # nothing
    b'avc1': read_avc1, # nothing
    b'avcC': read_avcC, # nothing
    b'stts': read_stts, # sample_count, sample_duration
    b'stss': read_stss, # join indexes
    b'stsc': read_stsc, # merge # sample numbers
    b'stsz': read_stsz, # merge # samples
    b'stco': read_stco, # merge # chunk offsets
    b'ctts': read_ctts, # merge
    b'smhd': read_smhd, # nothing
    b'mp4a': read_mp4a, # nothing
    b'esds': read_esds, # noting
    
    b'ftyp': read_raw,
    b'yqoo': read_raw,
    b'moov': read_composite_atom,
    b'trak': read_composite_atom,
    b'mdia': read_composite_atom,
    b'minf': read_composite_atom,
    b'dinf': read_composite_atom,
    b'stbl': read_composite_atom,
    b'iods': read_raw,
    b'dref': read_raw,
    b'free': read_raw,
    b'edts': read_raw,
    b'pasp': read_raw,

    b'mdat': read_mdat,
    b'udta': read_udta,
}
#stsd sample descriptions (codec types, initialization etc.) 
#stts (decoding) time-to-sample  
#ctts (composition) time to sample 
#stsc sample-to-chunk, partial data-offset information 
#stsz sample sizes (framing) 
#stz2 compact sample sizes (framing) 
#stco chunk offset, partial data-offset information 
#co64 64-bit chunk offset 
#stss sync sample table (random access points) 
#stsh shadow sync sample table 
#padb sample padding bits 
#stdp sample degradation priority 
#sdtp independent and disposable samples 
#sbgp sample-to-group 
#sgpd sample group description 
#subs sub-sample information


def read_atom(stream: BinaryIO) -> Optional[Atom]:
    """
    Reads an atom from the given binary stream.

    Args:
        stream: A binary stream from which the atom is read.
    
    Returns:
        An atom object if a valid atom is read, otherwise None.

    Raises:
        NotImplementedError: If the atom type is not supported.
    """
    # Read the header from the stream and check if it is empty
    header = stream.read(8)
    if not header:
        return None  # Return None if the stream is empty
    assert len(header) == 8, f"Expected 8 bytes, but got {len(header)}"
    n = 0
    size = struct.unpack('>I', header[:4])[0]
    assert size > 0
    n += 4
    type = header[4:8]
    n += 4
    assert type != b'uuid'
    if size == 1:
        size = read_ulong(stream)
        n += 8

    left = size - n
    if type in atom_readers:
        return atom_readers[type](stream, size, left, type)
    raise NotImplementedError(f'Atom type {type} not supported')

def write_atom(stream: BinaryIO, atom: Atom) -> None:
    """
    Writes an atom to the given binary stream.

    Args:
        stream: The binary stream to which the atom will be written.
        atom: The atom object that will be written to the stream.
    """
    atom.write(stream)

def parse_atoms(stream: BinaryIO) -> List[Atom]:
    """
    Parses all atoms from the given binary stream.

    Args:
        stream: The binary stream from which the atoms will be parsed.

    Returns:
        List[Atom]: A list of atoms parsed from the stream.
    """
    atoms = []
    while (atom := read_atom(stream)):
        atoms.append(atom)
    return atoms

def read_mp4(stream: BinaryIO) -> Tuple[List[Atom], Atom, Atom]:
    """
    Reads and parses an MP4 file from the given binary stream.

    Args:
        stream: A binary stream containing the MP4 data.
    
    Returns:
        A tuple containing:
            - A list of atoms parsed from the stream.
            - The first moov atom found in the stream.
            - The first mdat atom found in the stream.
    """
    if not isinstance(stream, io.IOBase):
        raise TypeError(f"Expected io.IOBase, got {type(stream)}")
    print(stream.name)
    # Parse atoms from the stream
    atoms = parse_atoms(stream)
    # Extract `moov` and `mdat` atoms using filtering.
    moov = list(filter(lambda x: x.type == b'moov', atoms))
    mdat = list(filter(lambda x: x.type == b'mdat', atoms))
    # Ensure we have exactly one `moov` and `mdat` atom.
    assert len(moov) == 1
    assert len(mdat) == 1
    moov = moov[0]
    mdat = mdat[0]
    return atoms, moov, mdat

##################################################
# merge
##################################################

def merge_stts(samples_list: List[List[Tuple[int, int]]]) -> List[Tuple[int, int]]:
    """
    Merges time-to-sample (stts) data across multiple sample lists.

    Args:
        samples_list (List[List[Tuple[int, int]]]): List of time-to-sample data to merge.

    Returns:
        List[Tuple[int, int]]: Merged sample counts and durations.
    """
    sample_list = [sample for samples in samples_list for sample in samples]
    counts, durations = zip(*sample_list)
    #assert len(set(durations)) == 1, 'not all durations equal'
    if len(set(durations)) == 1:
        return [(sum(counts), durations[0])]
    return sample_list

def merge_stss(sample_lists: List[List[int]], sample_numbers: List[int]) -> List[int]:
    """
    Merges multiple sample lists into a single flattened list of integers, with each
    sample being offset by the sum of the previous sample numbers.

    Args:
        sample_lists (List[List[int]]): A list of sample lists, where each inner list
        contains integers.
        sample_numbers (List[int]): A list of integers representing the number of elements
        in each corresponding sample list.

    Returns:
        List[int]: A single list containing all the integers from the sample lists, with
        offsets applied.

    Raises:
        ValueError: If the lengths of sample_lists and sample_numbers do not match.
    """
    results = []
    start = 0
    for sample, number in zip(sample_lists, sample_numbers):
        results.extend(map(lambda x: start + x, sample))
        start += number
    return results

def merge_stsc(
        chunks_list: List[List[Tuple[int, int, str]]],
        total_chunk_number_list: List[int]) -> List[Tuple[int, int, str]]:
    results = []
    chunk_index = 1
    for chunks, total in zip(chunks_list, total_chunk_number_list):
        for i in range(len(chunks)):
            if i < len(chunks) - 1:
                chunk_number = chunks[i + 1][0] - chunks[i][0]
            else:
                chunk_number = total + 1 - chunks[i][0]
            sample_number = chunks[i][1]
            description = chunks[i][2]
            results.append((chunk_index, sample_number, description))
            chunk_index += chunk_number
    return results

def merge_stco(offsets_list: List[List[int]], mdats: List[Atom]) -> List[int]:
    """
    Merges stco data across multiple sample lists.

    Args:
        offsets_list (List[List[int]]): List of stco data to merge.
        mdats (List[Atom]): List of mdat atoms.

    Returns:
        List[int]: Merged stco data.

    Raises:
        ValueError: If the lengths of offsets_list and mdats do not match.
    """
    # Ensure inputs are of the same length
    if len(offsets_list) != len(mdats):
        raise ValueError(
            f"Inputs lengths do not match: "
            f"offsets_list: {len(offsets_list)}, mdats: {len(mdats)}"
        )
    offset = 0
    results = [
        offset + x - mdat.body[1]
        for offsets, mdat in zip(offsets_list, mdats)
        for offset, x in enumerate(offsets)
    ]
    return results


def merge_stsz(sizes_list: List[List[int]]) -> List[int]:
    """
    Merges sizes from multiple lists into a single list.

    Args:
        sizes_list (List[List[int]]): List of stsz data to merge.

    Returns:
        List[int]: Merged stsz data.
    """
    # Check that sizes_list is a list (or iterable)
    if not isinstance(sizes_list, list):
        raise TypeError("sizes_list must be a list")
    return [size for sizes in sizes_list for size in sizes]


def merge_mdats(mdats: List[Atom]):
    total_size = sum(x.size - 8 for x in mdats) + 8
    class multi_mdat_atom(Atom):
        def __init__(self, type, size, body):
            super().__init__(type, size, body)
        def write(self, stream):
            self.write1(stream)
            self.write2(stream)
        def write2(self, stream):
            for mdat in self.body:
                mdat.write2(stream)
        def calsize(self):
            return self.size
    return multi_mdat_atom(b'mdat', total_size, mdats)


def merge_moov(moovs, mdats):
    assert len(moovs) == len(mdats)
    mvhd_duration = sum(x.get(b'mvhd').get('duration') for x in moovs)
    tkhd_durations = [0, 0]
    mdhd_durations = [0, 0]
    for x in moovs:
        traks = x.get_all(b'trak')
        assert len(traks) == 2
        tkhd_durations[0] += traks[0].get(b'tkhd').get('duration')
        tkhd_durations[1] += traks[1].get(b'tkhd').get('duration')
        mdhd_durations[0] += traks[0].get(b'mdia', b'mdhd').get('duration')
        mdhd_durations[1] += traks[1].get(b'mdia', b'mdhd').get('duration')
    #mvhd_duration = min(mvhd_duration, tkhd_durations)
    
    trak0s = [x.get_all(b'trak')[0] for x in moovs]
    trak1s = [x.get_all(b'trak')[1] for x in moovs]
    
    stts0 = merge_stts(x.get(b'mdia', b'minf', b'stbl', b'stts').body[1] for x in trak0s)
    stts1 = merge_stts(x.get(b'mdia', b'minf', b'stbl', b'stts').body[1] for x in trak1s)
    
    stss = merge_stss((x.get(b'mdia', b'minf', b'stbl', b'stss').body[1] for x in trak0s), (len(x.get(b'mdia', b'minf', b'stbl', b'stsz').body[3]) for x in trak0s))
    
    stsc0 = merge_stsc((x.get(b'mdia', b'minf', b'stbl', b'stsc').body[1] for x in trak0s), (len(x.get(b'mdia', b'minf', b'stbl', b'stco').body[1]) for x in trak0s))
    stsc1 = merge_stsc((x.get(b'mdia', b'minf', b'stbl', b'stsc').body[1] for x in trak1s), (len(x.get(b'mdia', b'minf', b'stbl', b'stco').body[1]) for x in trak1s))
    
    stco0 = merge_stco((x.get(b'mdia', b'minf', b'stbl', b'stco').body[1] for x in trak0s), mdats)
    stco1 = merge_stco((x.get(b'mdia', b'minf', b'stbl', b'stco').body[1] for x in trak1s), mdats)
    
    stsz0 = merge_stsz((x.get(b'mdia', b'minf', b'stbl', b'stsz').body[3] for x in trak0s))
    stsz1 = merge_stsz((x.get(b'mdia', b'minf', b'stbl', b'stsz').body[3] for x in trak1s))
    
    ctts = sum((x.get(b'mdia', b'minf', b'stbl', b'ctts').body[1] for x in trak0s), [])
    
    moov = moovs[0]
    
    moov.get(b'mvhd').set('duration', mvhd_duration)
    trak0 = moov.get_all(b'trak')[0]
    trak1 = moov.get_all(b'trak')[1]
    trak0.get(b'tkhd').set('duration', tkhd_durations[0])
    trak1.get(b'tkhd').set('duration', tkhd_durations[1])
    trak0.get(b'mdia', b'mdhd').set('duration', mdhd_durations[0])
    trak1.get(b'mdia', b'mdhd').set('duration', mdhd_durations[1])
    
    stts_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stts')
    stts_atom.body = stts_atom.body[0], stts0
    stts_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stts')
    stts_atom.body = stts_atom.body[0], stts1
    
    stss_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stss')
    stss_atom.body = stss_atom.body[0], stss
    
    stsc_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stsc')
    stsc_atom.body = stsc_atom.body[0], stsc0
    stsc_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stsc')
    stsc_atom.body = stsc_atom.body[0], stsc1
    
    stco_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stco')
    stco_atom.body = stss_atom.body[0], stco0
    stco_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stco')
    stco_atom.body = stss_atom.body[0], stco1
    
    stsz_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stsz')
    stsz_atom.body = stsz_atom.body[0], stsz_atom.body[1], len(stsz0), stsz0
    stsz_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stsz')
    stsz_atom.body = stsz_atom.body[0], stsz_atom.body[1], len(stsz1), stsz1
    
    ctts_atom = trak0.get(b'mdia', b'minf', b'stbl', b'ctts')
    ctts_atom.body = ctts_atom.body[0], ctts
    
    old_moov_size = moov.size
    new_moov_size = moov.calsize()
    new_mdat_start = mdats[0].body[1] + new_moov_size - old_moov_size
    stco0 = list(map(lambda x: x + new_mdat_start, stco0))
    stco1 = list(map(lambda x: x + new_mdat_start, stco1))
    stco_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stco')
    stco_atom.body = stss_atom.body[0], stco0
    stco_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stco')
    stco_atom.body = stss_atom.body[0], stco1
    
    return moov

def merge_mp4s(files: List[str], output: Optional[str] = None) -> Optional[str]:
    """
    Merges multiple MP4 files into a single MP4 file.

    Args:
        files (List[str]): A list of MP4 file paths to be merged.
        output (Optional[str], optional): The output file path. Defaults to None.

    Returns:
        Optional[str]: The output file path if successful, otherwise None.
    """
    assert files
    try:
        with contextlib.ExitStack() as stack:
            ins = [stack.enter_context(open(mp4, 'rb')) for mp4 in files]
    except FileNotFoundError as e:
        print(f"Failed to open file: {e}")
        return None
    # Read and parse MP4 files into atoms, moov, and mdat
    mp4s = list(map(read_mp4, ins))
    # Extract moov and mdat atoms from each MP4 file
    moovs = list(map(lambda x: x[1], mp4s))
    mdats = list(map(lambda x: x[2], mp4s))
    # Merge moov and mdat atoms
    moov = merge_moov(moovs, mdats)
    mdat = merge_mdats(mdats)
    # Guess the output file path if not provided
    if not output:
        output = guess_output(files)
    # Write the merged MP4 file to the output file
    with open(output, 'wb') as out:
        for atom in mp4s[0][0]:
            if atom.type == b'moov':
                moov.write(out)
            elif atom.type == b'mdat':
                mdat.write(out)
            else:
                atom.write(out)
    return output

##################################################
# main
##################################################

# TODO: FIXME: duplicate of join_flv

def guess_output(inputs: List[str]) -> str:
    """
    Guesses the common prefix of the input file paths (excluding directories) and
    returns the base filename with a '.mp4' extension. If no common prefix is found,
    returns 'output.mp4'.

    Args:
        inputs (List[str]): A list of input file paths.

    Returns:
        str: The output file path.
    """
    import os.path
    # Extract the base filenames from the paths in `inputs`
    inputs = [os.path.basename(inp) for inp in inputs]
    # Find the length of the shortest filename to limit comparisons.
    n = min(map(len, inputs))
    # Iterate over the range from 1 to the length of the shortest filename, in reverse order.
    for i in reversed(range(1, n)):
        # Check if all filenames have the same prefix of length `i`.
        if len(set(s[:i] for s in inputs)) == 1:
            return inputs[0][:i] + '.mp4'
    # If no common prefix is found, return 'output.mp4'.
    return 'output.mp4'

def concat_mp4(mp4s: List[str], output: Optional[str] = None) -> str:
    """
    Concatenates multiple MP4 files into a single MP4 file.

    Args:
        mp4s (List[str]): A list of MP4 file paths to be concatenated.
        output (Optional[str], optional): The output file path. Defaults to None.

    Returns:
        str: The output file path.
    """
    assert mp4s, 'no mp4 file found'
    # Check if `output` is None or a directory. If so, append the output filename to the directory path.
    import os.path
    if not output:
        output = guess_output(mp4s)
    elif os.path.isdir(output):
        output = os.path.join(output, guess_output(mp4s))
    
    print('Merging video parts...')
    merge_mp4s(mp4s, output)
    
    return output

def usage() -> None:
    """
    Prints the usage information for the script.
    """
    print('Usage: [python3] join_mp4.py --output TARGET.mp4 mp4...')

def main() -> None:
    import sys, getopt
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
        sys.exit(1)  # Exiting the script due to no arguments
    
    concat_mp4(args, output)

if __name__ == '__main__':
    main()
