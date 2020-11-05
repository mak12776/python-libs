import io
import os
import typing
from io import RawIOBase
from typing import Union

BinaryFile = typing.Union[typing.BinaryIO, io.RawIOBase]
TextFile = typing.Union[typing.TextIO, io.TextIOBase]


def get_file_size(file_or_name: Union[BinaryFile, str]):
    if isinstance(file_or_name, str):
        return os.stat(file_or_name).st_size
    elif isinstance(file_or_name, RawIOBase):
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


def read_int(infile: io.RawIOBase, size: int, byteorder='big', signed=False):
    buffer = infile.read(size)
    if len(buffer) != size:
        signed = 'signed' if signed else 'unsigned'
        raise EOFError(f'while reading {size} byte {signed} int')
    return int.from_bytes(buffer, byteorder, signed=signed)


def write_int(outfile: io.RawIOBase, value: int, size: int, byteorder='big', signed=False):
    return outfile.write(value.to_bytes(size, byteorder, signed=signed))


class FunctionCache:
    __slots__ = 'parent_directory'

    def __init__(self, parent_directory: str):
        self.parent_directory = parent_directory
