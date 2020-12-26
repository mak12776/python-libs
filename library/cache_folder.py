import dataclasses
import marshal
from enum import IntEnum, auto
from itertools import count
from os.path import join
from typing import Callable, Dict, Tuple

from traitlets import Any

from library.sio import FileWrapper, read_int, BufferType

MARSHAL_VERSION = 4
ENCODING = 'utf-8'

size_settings = {
    'size': 4,
    'byteorder': 'big',
    'signed': False,
}

data_type_settings = {
    'size': 1,
    'byteorder': 'big',
    'signed': False,
}

file_index_settings = {
    'size': 8,
    'byteorder': 'big',
    'signed': False,
}


class DataType(IntEnum):
    FUNCTION = auto()
    TITLE = auto()
    GET_REQUEST = auto()


@dataclasses.dataclass(init=True, repr=True, eq=False)
class ReadWriteWrapper:
    __slots__ = 'read', 'write'
    read: Callable[[FileWrapper], Any]
    write: Callable[[FileWrapper, Any], int]


KeyType = Tuple[DataType, bytes]


class CacheFolder:
    __slots__ = '_root_path', '_container_name'

    def __init__(self, root_path, container_name='container.bin'):
        self._root_path = root_path
        self._container_name = container_name

    def __read_container(self):
        path = join(self._root_path, self._container_name)
        data_dict = {}
        with FileWrapper.open(path, 'rb') as wrapper:
            data_size = wrapper.read_int(**size_settings)  # data size
            for step in data_size:
                data_type = DataType(read_int(**data_type_settings))  # data type
                data = wrapper.read_big_bytes()  # data
                file_index = wrapper.read_int(**file_index_settings)  # file index
                # update data_dict
                data_dict[(data_type, data)] = file_index
        return data_dict

    def __write_container(self, data_dict: Dict):
        path = join(self._root_path, self._container_name)
        with FileWrapper.open(path, 'wb') as wrapper:
            total = wrapper.write_int(len(data_dict), **size_settings)  # data size
            for key, value in data_dict.items():
                total += wrapper.write_int(key[0], **data_type_settings)  # data type
                total += wrapper.write_big_bytes(key[1])  # data
                total += wrapper.write_big_bytes(value)  # file index
        return total

    def __format_path(self, index: int):
        return join(self._root_path, f'{hex(index)[2:]}.data')

    def __read_file_index(self, index: int):
        path = self.__format_path(index)
        with open(path, 'rb') as infile:
            return infile.read()

    def __write_file_index(self, index: int, buffer: BufferType):
        path = self.__format_path(index)
        with open(path, 'wb') as outfile:
            return outfile.write(buffer)

    def __read_file_index_call_back(self, index: int, rw: ReadWriteWrapper):
        path = self.__format_path(index)
        with FileWrapper.open(path, 'rb') as wrapper:
            return rw.read(wrapper)

    def __write_file_index_call_back(self, index: int, rw: ReadWriteWrapper, instance: Any):
        path = self.__format_path(index)
        with FileWrapper.open(path, 'rb') as wrapper:
            return rw.write(wrapper, instance)

    @staticmethod
    def __search_new_index(data_dict: Dict):
        for data_index, index in zip(data_dict.values(), count()):
            if data_index != index:
                return index
        return 0

    def __write_new_index_and_container(self, data_dict: Dict, key: KeyType, buffer: BufferType):
        new_index = data_dict[key] = CacheFolder.__search_new_index(data_dict)
        self.__write_file_index(new_index, buffer)
        self.__write_container(data_dict)

    def __write_new_index_and_container_call_back(self, data_dict: Dict, key: KeyType, rw: ReadWriteWrapper, instance):
        new_index = data_dict[key] = CacheFolder.__search_new_index(data_dict)
        self.__write_file_index_call_back(new_index, rw, instance)
        self.__write_container(data_dict)

    def cached_call(self, rw: ReadWriteWrapper = None):
        def __decorator(func: Callable):
            def __wrapper(*args, **kwargs):
                func_codes = marshal.dumps(func, MARSHAL_VERSION)
                data_dict = self.__read_container()
                key = (DataType.FUNCTION, func_codes)
                try:
                    index = data_dict[key]
                except KeyError:
                    instance = func(*args, **kwargs)
                    if isinstance(instance, (bytes, bytearray)):
                        self.__write_new_index_and_container(data_dict, key, instance)
                    elif ReadWriteWrapper is None:
                        raise ValueError('for non-bytes return values you need to pass `rw` argument')
                    else:
                        self.__write_new_index_and_container_call_back(data_dict, key, rw, instance)
                    return instance
                return self.__read_file_index_call_back(index, rw)

            return __wrapper

        return __decorator

    def cache_title(self, title: str, buffer: BufferType):
        data_dict = self.__read_container()
        key = (DataType.TITLE, title.encode(ENCODING))
        self.__write_new_index_and_container(data_dict, key, buffer)
