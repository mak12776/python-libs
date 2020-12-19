import marshal
from os.path import join
from typing import Callable, Dict

from library import io

MARSHAL_VERSION = 4


class CacheFolder:
    __slots__ = '_root_path', '_container_name'

    def __init__(self, root_path, container_name='container.bin'):
        self._root_path = root_path
        self._container_name = container_name

    def __read_container__(self):
        path = join(self._root_path, self._container_name)
        with open(path, 'rb') as file:
            data_len = io.read_size(file)

    def __write_container__(self, data_dict: Dict):
        path = join(self._root_path, self._container_name)
        with open(path, 'wb') as file:
            io.write_size(file, len(data_dict))
            for key, value in data_dict.items():
                pass

    def cached_func(self, func: Callable, *args, **kwargs):
        dump_string = marshal.dumps(func, MARSHAL_VERSION)
