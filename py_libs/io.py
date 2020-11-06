import io
import json
import os
import typing
from collections import namedtuple
from io import RawIOBase
from os import path
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


ReadWrite = namedtuple('ReadWrite', ['read', 'write'])

data_cache_json_setting = {
    'allow_nan': False,
    'separators': (',', ':')
}

data_cache_name = '.cache_info'


class DataCache:
    __slots__ = 'dir_name'

    def __init__(self, dir_name: str):
        self.dir_name = dir_name

    def load_info_data(self):
        info_path = path.join(self.dir_name, data_cache_name)
        try:
            with open(info_path, 'rt') as infile:
                return json.load(infile)
        except FileNotFoundError:
            return {'titles': {}, 'max_index': -1}

    def save_info_data(self, cache_data):
        info_path = path.join(self.dir_name, data_cache_name)
        with open(info_path, 'wt') as outfile:
            json.dump(cache_data, outfile, **data_cache_json_setting)

    def cached_function(self, title: str, read_write: ReadWrite, function, *args, **kwargs):
        info_data = self.load_info_data()
        index_format = '0>10'
        try:
            index = info_data['titles'][title]
            just_read = True
        except KeyError:
            index = info_data['titles'][title] = info_data['max_index'] = info_data['max_index'] + 1
            just_read = False
        if just_read:
            file_path = path.join(self.dir_name, f'{index:{index_format}}')
            with open(file_path, 'rb') as infile:
                return read_write.read(infile)
        else:
            data = function(*args, **kwargs)
            self.save_info_data(info_data)
            file_path = path.join(self.dir_name, f'{index:{index_format}}')
            with open(file_path, 'wb') as outfile:
                read_write.write(data, outfile)
            return data
