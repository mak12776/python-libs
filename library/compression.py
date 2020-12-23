import secrets
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Union, Tuple

from sortedcontainers import SortedList

from library import math
from library.sio import FileWrapper
from library.utils import to_machine_size, StopWatch

RandBytes = Callable[[int], bytes]
BufferInfo = Union[bytes, str, int, Tuple[RandBytes, int]]

_stop_watch = StopWatch()


def get_buffer(buffer_info: BufferInfo):
    if isinstance(buffer_info, bytes):
        return buffer_info
    elif isinstance(buffer_info, int):
        return secrets.token_bytes(buffer_info)
    elif isinstance(buffer_info, str):
        if buffer_info.startswith(':'):
            return secrets.token_bytes(to_machine_size(buffer_info[1:]))
        with open(buffer_info, 'rb') as file:
            return file.read()
    elif isinstance(buffer_info, tuple):
        randbytes, size = buffer_info
        return randbytes(size)
    else:
        raise TypeError(f'invalid type for buffer_info: {type(buffer_info)}')


def get_bytes_per_bits(bits: int):
    return math.upper_bound(bits, 8)


DataType = int


@dataclass(init=True, repr=True, eq=False)
class DataCount:
    __slots__ = 'data', 'count'
    data: bytes
    count: int


int_settings = {
    'byteorder': 'big',
    'signed': False,
}


class SegmentedBuffer:
    __slots__ = ('buffer_size', 'buffer_bits',
                 'data_bits', 'data_size', 'sorted_counts',
                 'remaining_bits', 'remaining_size', 'remaining')

    def __init__(self):
        self.buffer_bits: int = 0
        self.buffer_size: int = 0

        self.data_bits: int = 0
        self.data_size: int = 0

        self.sorted_counts: SortedList[DataCount] = SortedList()

        self.remaining_bits: int = 0
        self.remaining_size: int = 0

        self.remaining = None

    def _count_bytes(self, buffer: bytes):
        max_index = self.buffer_size - self.remaining_size
        count_dict = defaultdict(lambda: 1)
        for index in range(0, max_index, self.data_size):
            count_dict[buffer[index:index + self.data_size]] += 1
        return count_dict

    @staticmethod
    def _sort_count_dict(count_dict):
        return SortedList((DataCount(key, value) for key, value in count_dict), key=lambda item: item.count)

    def read(self, wrapper: FileWrapper):
        size = wrapper.read_int(1, byteorder='big', signed=False)
        self.buffer_size = wrapper.read_int(size, **int_settings)
        self.buffer_bits = wrapper.read_int(size, **int_settings)
        self.data_size = wrapper.read_int(size, **int_settings)
        self.data_bits = wrapper.read_int(size, **int_settings)
        # read sorted count list
        self.remaining_size = wrapper.read_int(size, **int_settings)
        self.remaining_bits = wrapper.read_int(size, **int_settings)
        # read remaining

    def write(self, wrapper: FileWrapper, size: int = 4):
        wrapper.write_int(size, 1, byteorder='big', signed=False)
        wrapper.write_int(self.buffer_size, size, **int_settings)
        wrapper.write_int(self.buffer_bits, size, **int_settings)
        wrapper.write_int(self.data_size, size, **int_settings)
        wrapper.write_int(self.data_bits, size, **int_settings)
        # write sorted count list
        wrapper.write_int(self.remaining_size, size, **int_settings)
        wrapper.write_int(self.remaining_bits, size, **int_settings)
        # write remaining

    @staticmethod
    def static_read(wrapper: FileWrapper):
        instance = SegmentedBuffer()
        instance.read(wrapper)
        return instance

    @staticmethod
    def static_write(wrapper: FileWrapper, instance: 'SegmentedBuffer', size: int = 4):
        return instance.write(wrapper, size=size)

    def scan_buffer(self, buffer: bytes, data_bits: int):
        self.buffer_size = len(buffer)
        self.buffer_bits = self.buffer_size * 8

        self.data_bits = data_bits
        self.data_size = get_bytes_per_bits(data_bits)

        self.remaining_bits = self.buffer_bits // self.data_bits
        self.remaining_size = get_bytes_per_bits(self.remaining_bits)
