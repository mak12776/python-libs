import secrets
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
    data: Union[int, bytes]
    count: int

    def format(self, width):
        if isinstance(self.data, int):
            return f'{self.data:{width}<b}: {self.count}'
        return f'{self.data}: {self.count}'


int_settings = {
    'byteorder': 'big',
    'signed': False,
}
DEFAULT_INT_SIZE = 4


def _from_bytes(value: bytes):
    return int.from_bytes(value, byteorder='big', signed=False)


def _from_bytes_and_bits(_bytes: bytes):
    return int.from_bytes(bytes, byteorder='big', signed=False), len(_bytes) * 8


def _mask(width: int):
    return (1 << width) - 1


def _print_bits_size(name, bits, size):
    if bits % 8 == 0:
        return print(f'{name}: {bits} bits ({size} bytes)')
    return print(f'{name}: {bits} bits (<= {size} bytes)')


_method_values = {
    'ints': 0,
    'bytes': 1,
}


class SegmentedBuffer:
    __slots__ = ('buffer_size', 'buffer_bits',
                 'data_bits', 'data_size', 'method', 'sorted_data_count_list',
                 'remaining_bits', 'remaining_size', 'remaining')

    def __init__(self):
        self.buffer_bits: int = 0
        self.buffer_size: int = 0

        self.data_bits: int = 0
        self.data_size: int = 0

        self.method: str = ''
        self.sorted_data_count_list: SortedList[DataCount] = SortedList()

        self.remaining_bits: int = 0
        self.remaining_size: int = 0
        self.remaining = None

    @staticmethod
    def _read_method(wrapper: FileWrapper):
        read_value = wrapper.read_int(1, **int_settings)
        for key, value in _method_values.items():
            if value == read_value:
                return key
        raise ValueError(f'unknown method: {read_value}')

    @staticmethod
    def _write_method(wrapper: FileWrapper, method: str):
        wrapper.write_int(_method_values[method], 1, **int_settings)

    def read(self, wrapper: FileWrapper):
        int_size = wrapper.read_int(1, byteorder='big', signed=False)
        self.buffer_size = wrapper.read_int(int_size, **int_settings)
        self.buffer_bits = wrapper.read_int(int_size, **int_settings)
        self.data_size = wrapper.read_int(int_size, **int_settings)
        self.data_bits = wrapper.read_int(int_size, **int_settings)
        # read sorted count list
        self.method = SegmentedBuffer._read_method(wrapper)

        for data_count in self.sorted_data_count_list:
            pass
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
        SegmentedBuffer._write_method(wrapper, self.method)
        if self.method == 'ints':
            for data_count in self.sorted_data_count_list:
                wrapper.write_int(data_count.data, self.data_size, **int_settings)
                wrapper.write_int(data_count.count, int_size, **int_settings)
        else:
            raise ValueError(f'unsupported method: {self.method}')
        # write remaining
        wrapper.write_int(self.remaining_size, int_size, **int_settings)
        wrapper.write_int(self.remaining_bits, int_size, **int_settings)
        if self.method == 'ints':
            wrapper.write_int(self.remaining, self.remaining_size, **int_settings)
        else:
            raise ValueError(f'unsupported method: {self.method}')

    def check_values(self):
        max_data = _mask(self.data_bits)
        for data_count in self.sorted_data_count_list:
            if data_count.data > max_data:
                print(f'!\tinvalid data: {data_count.data:0>b}')

    def print_values(self):
        _print_bits_size('buffer', self.buffer_bits, self.buffer_size)
        _print_bits_size('data', self.data_bits, self.data_size)

        if self.method == 'ints':
            def print_data_count(item: DataCount):
                return print(f'-\t{item.data:0>{self.data_bits}b}: {item.count}')
        else:
            raise ValueError(f'unsupported method: {self.method}')

        for data_count in self.sorted_data_count_list:
            print_data_count(data_count)
        _print_bits_size('remaining', self.remaining_bits, self.remaining_size)
        if self.method == 'ints':
            print(f'-\t{self.remaining:0>{self.remaining_bits}b}')

    def _count_bytes(self, buffer: bytes):
        if self.data_bits % 8 == 0:
            max_index = self.buffer_size - self.remaining_size
            count_dict = defaultdict(lambda: 1)
            for index in range(0, max_index, self.data_size):
                count_dict[buffer[index:index + self.data_size]] += 1
            return count_dict, buffer[max_index:]
        else:
            raise ValueError(f'{self.data_bits} data bits is not supported in `bytes` method')

    def _count_ints(self, buffer: bytes):
        count_dict = defaultdict(lambda: 0)
        if self.data_bits == 8:
            for value in buffer:
                count_dict[value] += 1
            return count_dict, 0
        elif self.data_bits % 8 == 0:
            max_index = self.buffer_size - self.remaining_size
            for index in range(0, max_index, self.data_size):
                count_dict[_from_bytes(buffer[index:index + self.data_size])] += 1
            return count_dict, _from_bytes(buffer[max_index:])
        else:
            if self.buffer_bits < self.data_bits:
                return count_dict, _from_bytes(buffer)
            full_read_bits = self.data_size * 8
            residual_size = self.buffer_size % self.data_size
            # read first data bits
            read_value = _from_bytes(buffer[0: 0 + self.data_size])
            residual_bits = full_read_bits
            while residual_bits >= self.data_bits:
                residual_bits -= self.data_bits
                count_dict[read_value >> residual_bits] += 1
                read_value &= _mask(residual_bits)
            # read rest data bits
            max_index = self.buffer_size - residual_size
            index = self.data_size
            while index < max_index:
                # save value
                necessary_bits = self.data_bits - residual_bits
                saved_value = read_value << necessary_bits
                # read next
                read_value = _from_bytes(buffer[index: index + self.data_size])
                residual_bits = full_read_bits - necessary_bits
                count_dict[saved_value | (read_value >> residual_bits)] += 1
                read_value &= _mask(residual_bits)
                # remaining bits
                while residual_bits >= self.data_bits:
                    residual_bits -= self.data_bits
                    count_dict[read_value >> residual_bits] += 1
                    read_value &= _mask(residual_bits)
                # inc index
                index += self.data_size
            if residual_size:
                full_read_bits = self.remaining_size * 8
                read_value = (read_value << full_read_bits) | _from_bytes(buffer[max_index:])
                residual_bits += full_read_bits
                while residual_bits >= self.data_bits:
                    residual_bits -= self.data_bits
                    count_dict[read_value >> residual_bits] += 1
                    read_value &= _mask(residual_bits)
            return count_dict, read_value

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

    @staticmethod
    def static_read(wrapper: FileWrapper):
        instance = SegmentedBuffer()
        instance.read(wrapper)
        return instance

    @staticmethod
    def static_write(wrapper: FileWrapper, instance: 'SegmentedBuffer', size: int = 4):
        return instance.write(wrapper, int_size=size)

    def scan_buffer(self, data_bits: int, buffer: bytes, method: str = 'ints'):
        self.buffer_size = len(buffer)
        self.buffer_bits = self.buffer_size * 8

        self.data_bits = data_bits
        self.data_size = get_bytes_per_bits(data_bits)

        self.remaining_bits = self.buffer_bits % self.data_bits
        self.remaining_size = get_bytes_per_bits(self.remaining_bits)

        if method == 'ints':
            count_dict, self.remaining = self._count_ints(buffer)
        elif method == 'bytes':
            count_dict, self.remaining = self._count_bytes(buffer)
        else:
            raise ValueError(f'unknown method: {method}')
        self.method = method
        self.sorted_data_count_list = SegmentedBuffer._sort_count_dict(count_dict)
