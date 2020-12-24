import secrets
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Union, Tuple, Dict

from sortedcontainers import SortedList

from library.math import ceil_module
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
    return ceil_module(bits, 8)


DataType = int


@dataclass(init=True, repr=True, eq=False)
class DataCount:
    __slots__ = 'data', 'count'
    data: int
    count: int


int_settings = {
    'byteorder': 'big',
    'signed': False,
}
DEFAULT_INT_SIZE = 4


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

    def dump_values(self):
        return f'buffer: {self.buffer_bits} bits ({self.buffer_size} bytes)\n' + \
               f'data: {self.data_bits} bits ({self.data_size} bytes)\n' + \
               f'remaining: {self.remaining_bits} bits ({self.remaining_size} bytes)\n'

    def print_values(self, file=sys.stdout):
        print(self.dump_values(), file=file)

    def _count_bytes(self, buffer: bytes):
        max_index = self.buffer_size - self.remaining_size
        count_dict = defaultdict(lambda: 1)
        for index in range(0, max_index, self.data_size):
            count_dict[buffer[index:index + self.data_size]] += 1
        return count_dict

    def _count_ints(self, buffer: bytes):
        if self.data_bits == 8:
            count_dict = defaultdict(lambda: 1)
            for value in buffer:
                count_dict[value] += 1
        else:
            max_index = self.buffer_size - self.remaining_size
            count_dict = defaultdict(lambda: 1)
            for index in range(0, max_index, self.data_size):
                count_dict[int.from_bytes(buffer[index:index + self.data_size], byteorder='big', signed=False)] += 1
        return count_dict

    @staticmethod
    def _sort_count_dict(count_dict: Dict):
        return SortedList((DataCount(key, value) for key, value in count_dict.items()), key=lambda item: item.count)

    @staticmethod
    def _read_sorted_count(wrapper: FileWrapper, int_size: int):
        length = wrapper.read_int(int_size, **int_settings)
        result = SortedList()
        for step in range(length):
            raise BaseException('incomplete code')
        return result

    def read(self, wrapper: FileWrapper):
        int_size = wrapper.read_int(1, byteorder='big', signed=False)
        self.buffer_size = wrapper.read_int(int_size, **int_settings)
        self.buffer_bits = wrapper.read_int(int_size, **int_settings)
        self.data_size = wrapper.read_int(int_size, **int_settings)
        self.data_bits = wrapper.read_int(int_size, **int_settings)
        # read sorted count list

        # read remaining
        self.remaining_size = wrapper.read_int(int_size, **int_settings)
        self.remaining_bits = wrapper.read_int(int_size, **int_settings)

    def write(self, wrapper: FileWrapper, int_size: int = 4):
        wrapper.write_int(int_size, 1, byteorder='big', signed=False)
        wrapper.write_int(self.buffer_size, int_size, **int_settings)
        wrapper.write_int(self.buffer_bits, int_size, **int_settings)
        wrapper.write_int(self.data_size, int_size, **int_settings)
        wrapper.write_int(self.data_bits, int_size, **int_settings)
        # write sorted count list

        # write remaining
        wrapper.write_int(self.remaining_size, int_size, **int_settings)
        wrapper.write_int(self.remaining_bits, int_size, **int_settings)

    @staticmethod
    def static_read(wrapper: FileWrapper):
        instance = SegmentedBuffer()
        instance.read(wrapper)
        return instance

    @staticmethod
    def static_write(wrapper: FileWrapper, instance: 'SegmentedBuffer', size: int = 4):
        return instance.write(wrapper, int_size=size)

    def scan_buffer(self, data_bits: int, buffer: bytes, method: str):
        self.buffer_size = len(buffer)
        self.buffer_bits = self.buffer_size * 8

        self.data_bits = data_bits
        self.data_size = get_bytes_per_bits(data_bits)

        self.remaining_bits = self.buffer_bits % self.data_bits
        self.remaining_size = get_bytes_per_bits(self.remaining_bits)

        if data_bits % 8 == 0:
            if method == 'ints':
                count_dict = self._count_ints(buffer)
            elif method == 'bytes':
                count_dict = self._count_bytes(buffer)
            else:
                raise ValueError
        else:
            raise BaseException('incomplete error')
        self.sorted_counts = SegmentedBuffer._sort_count_dict(count_dict)
