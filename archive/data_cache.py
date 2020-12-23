import json
from os import path
from typing import Tuple, Callable, Any

from library.sio import BinaryFile

ReadWrite = Tuple[Callable[[BinaryFile], Any], Callable[[Any, BinaryFile], None]]

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
        data_name_format: Callable[[int], str] = lambda file_index: f'{file_index}.bin'
        try:
            index = info_data['titles'][title]
            just_read = True
        except KeyError:
            index = info_data['titles'][title] = info_data['max_index'] = info_data['max_index'] + 1
            just_read = False
        if just_read:
            file_path = path.join(self.dir_name, data_name_format(index))
            with open(file_path, 'rb') as infile:
                return read_write[0](infile)
        else:
            data = function(*args, **kwargs)
            self.save_info_data(info_data)
            file_path = path.join(self.dir_name, data_name_format(index))
            with open(file_path, 'wb') as outfile:
                read_write[1](data, outfile)
            return data
