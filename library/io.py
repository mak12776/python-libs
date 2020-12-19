import io
import os
import typing
from ctypes import c_size_t, sizeof
from typing import Union

from library.utils import count_bits

BinaryFile = typing.Union[typing.BinaryIO, io.RawIOBase]
TextFile = typing.Union[typing.TextIO, io.TextIOBase]


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


def read_int(infile: BinaryFile, size: int, byteorder='big', signed=False):
    buffer = infile.read(size)
    if len(buffer) != size:
        signed = 'signed' if signed else 'unsigned'
        raise EOFError(f'while reading {size} byte {signed} int')
    return int.from_bytes(buffer, byteorder, signed=signed)


def write_int(outfile: BinaryFile, value: int, size: int, byteorder='big', signed=False):
    return outfile.write(value.to_bytes(size, byteorder, signed=signed))


SIZE_OF_SIZE = sizeof(c_size_t)


def read_size(infile: BinaryFile):
    return read_int(infile, SIZE_OF_SIZE, byteorder='big', signed=False)


def write_size(outfile: BinaryFile, value: int):
    return write_int(outfile, value, SIZE_OF_SIZE, byteorder='big', signed=False)


BIG_INT_INITIAL_MASK = 0b0011_1111
BIG_INT_SIGN_MASK = 0b0100_0000
BIG_INT_VALUE_MASK = 0b0111_1111
BIG_INT_CONTINUE_MASK = 0b1000_0000
BIG_INT_INITIAL_BITS = 6
BIG_INT_VALUE_BITS = 7


def read_big_int(infile: BinaryFile):
    byte = read_int(infile, 1, byteorder='big', signed=False)
    is_negative = bool(byte & BIG_INT_SIGN_MASK)
    value = byte & BIG_INT_INITIAL_MASK
    while byte & BIG_INT_CONTINUE_MASK:
        byte = read_int(infile, 1, byteorder='big', signed=False)
        value = (value << BIG_INT_VALUE_BITS) | (byte & BIG_INT_VALUE_MASK)
    return -value if is_negative else value


def write_big_int(outfile: BinaryFile, value: int):
    if value == 0:
        return write_int(outfile, 0, 1, byteorder='big', signed=False)
    byte = 0
    if value < 0:
        byte |= BIG_INT_SIGN_MASK
        value = -value
    # just initial bits
    if value <= BIG_INT_INITIAL_MASK:
        byte |= value
        return write_int(outfile, byte, 1, byteorder='big', signed=False)
    byte |= BIG_INT_CONTINUE_MASK
    # write first byte
    bits = count_bits(value)
    first_bits = bits % BIG_INT_VALUE_BITS
    if first_bits > 0:
        bits -= first_bits
        byte |= value >> bits
    total_write = write_int(outfile, byte, 1, byteorder='big', signed=False)
    # write the rest
    while bits > BIG_INT_VALUE_BITS:
        bits -= BIG_INT_VALUE_BITS
        byte = BIG_INT_CONTINUE_MASK | ((value >> bits) & BIG_INT_VALUE_MASK)
        total_write += write_int(outfile, byte, 1, byteorder='big', signed=False)
    byte = value & BIG_INT_VALUE_MASK
    total_write += write_int(outfile, byte, 1, byteorder='big', signed=False)
    return total_write


class FileWrapper:
    __slots__ = '_file'

    def __init__(self, file):
        self._file = file

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()

    def read_int(self, size: int, byteorder: str = 'big', signed: bool = False):
        return read_int(self._file, size, byteorder=byteorder, signed=signed)

    def write_int(self, value, size: int, byteorder='big', signed: bool = False):
        return write_int(self._file, value, size, byteorder=byteorder, signed=signed)

    @staticmethod
    def open(self, name, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True,
             opener=None):
        file = open(name, mode=mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline,
                    opener=opener)
        return FileWrapper(file)
