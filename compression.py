import io
import secrets
from collections import defaultdict
from typing import Callable, Union, Tuple

from sortedcontainers import SortedList

from library import math
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


class DataCount:
    __slots__ = 'data', 'count'

    def __init__(self, data: DataType, count: int):
        self.data = data
        self.count = count


class SegmentedBuffer:
    __slots__ = ('buffer_size', 'buffer_bits',
                 'data_bits', 'data_size', 'sorted_counts',
                 'remaining_bits', 'remaining_size', 'remaining')

    def __init__(self):
        self.buffer_size: int = 0
        self.buffer_bits: int = 0

        self.data_bits: int = 0
        self.data_size: int = 0

        self.sorted_counts: SortedList[DataCount] = SortedList()

        self.remaining_bits: int = 0
        self.remaining_size: int = 0

        self.remaining = None

    def _count_bytes(self, buffer: bytes):
        max_index = self.buffer_size - self.remaining_size
        count = defaultdict(lambda: 1)

        for index in range(0, max_index, self.data_size):
            count[buffer[index:index + self.data_size]] += 1

        self.sorted_counts = SortedList((DataCount(key, value) for key, value in count), key=lambda item: item.count)

    def save_to(self, file: io.RawIOBase):
        pass

    def count_buffer(self, buffer: bytes, data_bits: int):
        self.buffer_size = len(buffer)
        self.buffer_bits = self.buffer_size * 8

        self.data_bits = data_bits
        self.data_size = get_bytes_per_bits(data_bits)

        self.remaining_bits = self.buffer_bits // self.data_bits
        self.remaining_size = get_bytes_per_bits(self.remaining_bits)

        if data_bits % 8 == 0:
            self._count_bytes(buffer)
        else:
            raise ValueError(f'unsupported data bits: {data_bits}')
