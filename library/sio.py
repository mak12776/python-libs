import io
import os
import typing
from typing import Union, Callable

from library.math import ceil_module, lower_bound

BinaryFile = typing.Union[typing.BinaryIO, io.RawIOBase]
TextFile = typing.Union[typing.TextIO, io.TextIOBase]
AnyFile = typing.Union[BinaryFile, TextFile]
BufferType = Union[bytes, bytearray]


def get_file_size(file_or_name: Union[BinaryFile, str]):
    if isinstance(file_or_name, str):
        return os.stat(file_or_name).st_size
    elif isinstance(file_or_name, io.RawIOBase):
        current = file_or_name.tell()
        file_or_name.seek(0, io.SEEK_END)
        size = file_or_name.tell()
        file_or_name.seek(current, io.SEEK_SET)
        return size


def read_file(file: BinaryFile, name: str) -> bytearray:
    size = get_file_size(file)
    buffer = bytearray(size)
    read_number = file.readinto(buffer)
    if read_number != size:
        raise EOFError(f'while reading: {name}')
    return buffer


def read_file_name(path: str):
    with open(path, 'rb', buffering=0) as infile:
        return read_file(infile, path)


# read, write
def read_int(infile: BinaryFile, size: int, byteorder: str, signed: bool):
    buffer = infile.read(size)
    if len(buffer) != size:
        signed = 'signed' if signed else 'unsigned'
        raise EOFError(f'while reading {size} byte {signed} int')
    return int.from_bytes(buffer, byteorder, signed=signed)


def write_int(outfile: BinaryFile, value: int, size: int, byteorder: str, signed: bool):
    return outfile.write(value.to_bytes(size, byteorder, signed=signed))


# read, write unsigned int
def read_unsigned_int(infile: BinaryFile, size: int):
    return read_int(infile, size, byteorder='big', signed=False)


def write_unsigned_int(outfile: BinaryFile, value: int, size: int):
    return write_int(outfile, value, size, byteorder='big', signed=False)


# read, write big int
INITIAL_MASK = 0b0011_1111
INITIAL_BITS = 6

VALUE_MASK = 0b0111_1111
VALUE_BITS = 7

SIGN_MASK = 0b0100_0000
CONTINUE_MASK = 0b1000_0000


def __read_big_int_unsigned(infile: BinaryFile):
    byte = read_int(infile, 1, byteorder='big', signed=False)
    value = byte & VALUE_MASK
    while value & CONTINUE_MASK:
        byte = read_int(infile, 1, byteorder='big', signed=False)
        value = (value << VALUE_BITS) | (byte & VALUE_MASK)
    return value


def __read_big_int_signed(infile: BinaryFile):
    byte = read_int(infile, 1, byteorder='big', signed=False)
    is_negative = bool(byte & SIGN_MASK)
    value = byte & INITIAL_MASK
    while byte & CONTINUE_MASK:
        byte = read_int(infile, 1, byteorder='big', signed=False)
        value = (value << VALUE_BITS) | (byte & VALUE_MASK)
    return -value if is_negative else value


def read_big_int(infile: BinaryFile, signed: bool = True):
    if signed:
        return __read_big_int_signed(infile)
    return __read_big_int_unsigned(infile)


def __count_unsigned_bits(value):
    total = 8
    while value & 0xFF00:
        value >>= 8
        total += 8
    while value & 0x80 == 0:
        value <<= 1
        total -= 1
    return total


def __write_big_int_unsigned(outfile: BinaryFile, value: int):
    _write_byte: Callable[[int], int] = lambda _byte: write_int(outfile, _byte, 1, byteorder='big', signed=False)
    if value == 0:
        return _write_byte(0)
    total_write = 0
    # initial bits
    bits = __count_unsigned_bits(value)
    initial_bits = bits % VALUE_BITS
    if initial_bits > 0:
        bits -= initial_bits
        total_write += _write_byte(CONTINUE_MASK | (value >> bits))
    # other 7 bits
    while bits > VALUE_BITS:
        bits -= VALUE_BITS
        total_write += _write_byte(CONTINUE_MASK | ((value >> bits) & VALUE_MASK))
    total_write += _write_byte(value & VALUE_MASK)
    return total_write


def __write_big_int_signed(outfile: BinaryFile, value: int):
    _write_byte: Callable[[int], int] = lambda _byte: write_int(outfile, _byte, 1, byteorder='big', signed=False)
    if value == 0:
        return _write_byte(0)
    # remove negative sign
    sign_byte = 0
    if value < 0:
        sign_byte = SIGN_MASK
        value = -value
    # just first 6 bits
    if value <= INITIAL_MASK:
        return _write_byte(sign_byte | value)
    # more than 6 bits
    bits = __count_unsigned_bits(value)
    bits -= bits % VALUE_BITS
    total_write = _write_byte(CONTINUE_MASK | sign_byte | (value >> bits))
    # write the rest 7 bits
    while bits > VALUE_BITS:
        bits -= VALUE_BITS
        total_write += _write_byte(CONTINUE_MASK | ((value >> bits) & VALUE_MASK))
    # write last 7 bits
    total_write += _write_byte(value & VALUE_MASK)
    return total_write


def write_big_int(outfile: BinaryFile, value: int, signed=True):
    if signed:
        return __write_big_int_signed(outfile, value)
    return __write_big_int_unsigned(outfile, value)


# read, write bytes
def read_method_bytes(infile: BinaryFile, read_size: Callable[[BinaryFile], int]):
    return infile.read(read_size(infile))


def write_method_bytes(outfile: BinaryFile, buffer: BufferType, write_size: Callable[[BinaryFile, int], int]):
    total = write_size(outfile, len(buffer))
    return total + outfile.write(buffer)


def bits_mask(width: int):
    return (1 << width) - 1


def from_bytes(buffer: bytes):
    return int.from_bytes(buffer, byteorder='big', signed=False)


def to_bytes(value: int, size: int):
    return value.to_bytes(size, byteorder='big', signed=False)


class FileWrapper:
    __slots__ = '_file'

    def __init__(self, file: AnyFile):
        self._file = file

    @property
    def file(self):
        return self._file

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()

    # read, write int
    def read_int(self, size: int, byteorder: str, signed: bool):
        return read_int(self._file, size, byteorder=byteorder, signed=signed)

    def write_int(self, value, size: int, byteorder: str, signed: bool):
        return write_int(self._file, value, size, byteorder=byteorder, signed=signed)

    # simple read, write int
    def read_unsigned_int(self, size: int):
        return read_unsigned_int(self._file, size)

    def write_unsigned_int(self, value: int, size: int):
        return write_unsigned_int(self._file, value, size)

    # read, write big int
    def read_big_int(self, signed=True):
        return read_big_int(self._file, signed=signed)

    def write_big_int(self, value: int, signed=True):
        return write_big_int(self._file, value, signed=signed)

    # read, write bytes
    def read_bytes(self, size: int):
        return self._file.read(size)

    def write_bytes(self, buffer: bytes):
        return self._file.write(buffer)

    @staticmethod
    def open(name, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        file = open(name, mode=mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline,
                    closefd=closefd, opener=opener)
        return FileWrapper(file)


_BITS_IO_SIZE = 8


def read_bits(buffer: bytes, data_bits: int):
    if data_bits == 8:
        yield from buffer
    if data_bits % 8 == 0:
        data_size = data_bits // 8
        max_index = lower_bound(len(buffer), data_size)
        index = 0
        while index < max_index:
            yield from_bytes(buffer[index: index + data_size])
    else:
        data_size = ceil_module(data_bits, 8)
        raise BaseException('incomplete code')


class BitsIO:
    __slots__ = '_buffer', '_index', '_data_bits', '_read_bits', '_read_value'

    def __init__(self, buffer: bytes, bits: int):
        self._buffer = buffer
        self._index = 0
        self._data_bits = bits
        self._read_bits = 0
        self._read_value = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._read_bits < self._data_bits:
            if self._index >= len(self._buffer):
                raise StopIteration
            new_read_bits = (len(self._buffer) - self._index) * 8
            self._read_bits += new_read_bits
            self._read_value = (self._read_value << new_read_bits) | from_bytes(
                self._buffer[self._index: self._index + _BITS_IO_SIZE])
            self._index += _BITS_IO_SIZE
            if self._read_bits < self._data_bits:
                raise StopIteration
        self._read_bits -= self._data_bits
        value = self._read_value >> self._read_bits
        self._read_value &= bits_mask(self._read_bits)
        return value

    def remaining(self):
        return self._read_value
