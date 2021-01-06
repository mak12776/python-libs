import secrets
import sys
from collections import defaultdict
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Callable, Union, Tuple, Dict

from sortedcontainers import SortedList

from library.math import ceil_module
from library.sio import AnyFile, FileWrapper, BitsIO
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


DataType = Union[int, bytes]


@dataclass(init=True, repr=True, eq=False)
class DataCount:
    __slots__ = 'data', 'count'
    data: Union[int, bytes]
    count: int

    def format(self, width):
        if isinstance(self.data, int):
            return f'{self.data:{width}<b}: {self.count}'
        return f'{self.data}: {self.count}'


size_settings = {
    'byteorder': 'big',
    'signed': False,
}


def _from_bytes(value: bytes):
    return int.from_bytes(value, byteorder='big', signed=False)


def _from_bytes_and_bits(value: bytes):
    return int.from_bytes(value, byteorder='big', signed=False), len(value) * 8


def _mask(width: int):
    return (1 << width) - 1


def _print_bits_size(name: str, bits: int, size: int, file: AnyFile):
    if bits % 8 == 0:
        return print(f'{name}: {bits} bits ({size} bytes)', file=file)
    return print(f'{name}: {bits} bits (<= {size} bytes)', file=file)


class Method(IntEnum):
    UNDEFINED = auto()
    INT = auto()
    BYTE = auto()


class SegmentedBuffer:
    __slots__ = ('buffer_size', 'buffer_bits',
                 'data_bits', 'data_size',
                 'method', 'sorted_data_count',
                 'remaining_bits', 'remaining_size', 'remaining')

    def __init__(self):
        self.buffer_bits: int = 0
        self.buffer_size: int = 0

        self.data_bits: int = 0
        self.data_size: int = 0

        self.method: Method = Method.UNDEFINED
        self.sorted_data_count: SortedList[DataCount] = SortedList()

        self.remaining_bits: int = 0
        self.remaining_size: int = 0
        self.remaining = None

    # check & print values
    def check_values(self, file: AnyFile = sys.stderr):
        max_data = _mask(self.data_bits)
        for data_count in self.sorted_data_count:
            if data_count.data > max_data:
                print(f'!\tinvalid data: {data_count.data:0>b}', file=file)

    def print_values(self, file: AnyFile = sys.stdout):
        _print_bits_size('buffer', self.buffer_bits, self.buffer_size, file=file)
        _print_bits_size('data', self.data_bits, self.data_size, file=file)

        if self.method == Method.INT:
            def print_data_count(item: DataCount):
                return print(f'-\t{item.data:0>{self.data_bits}b}: {item.count}', file=file)
        else:
            raise ValueError(f'unsupported method: {self.method}')

        for data_count in self.sorted_data_count:
            print_data_count(data_count)

        _print_bits_size('remaining', self.remaining_bits, self.remaining_size, file=file)
        if self.method == Method.INT:
            print(f'-\t{self.remaining:0>{self.remaining_bits}b}')

    # read, write methods
    def _read_method(self, wrapper: FileWrapper):
        self.method = Method(wrapper.read_int(1, **size_settings))

    def _write_method(self, wrapper: FileWrapper):
        wrapper.write_int(self.method.value, 1, **size_settings)

    def _read_sorted_data_count(self, wrapper: FileWrapper, size_of_size: int):
        length = wrapper.read_int(size_of_size, **size_settings)
        self.sorted_data_count = SortedList()
        if self.method == Method.INT:
            for step in range(length):
                data = wrapper.read_int(self.data_size, **size_settings)
                count = wrapper.read_int(size_of_size, **size_settings)
                self.sorted_data_count.add(DataCount(data, count))
        else:
            raise ValueError(f'unsupported method: {self.method}')
        return SortedList()

    def _write_sorted_data_count(self, wrapper: FileWrapper, size_of_size: int):
        wrapper.write_int(len(self.sorted_data_count), size_of_size)
        if self.method == Method.INT:
            for data_count in self.sorted_data_count:
                wrapper.write_int(data_count.data, self.data_size, **size_settings)
                wrapper.write_int(data_count.count, size_of_size, **size_settings)
        else:
            raise ValueError(f'unsupported method: {self.method}')

    def _read_remaining(self, wrapper: FileWrapper):
        if self.method == Method.INT:
            self.remaining = wrapper.read_int(self.remaining_size, **size_settings)
        else:
            raise ValueError(f'unsupported method: {self.method}')

    def _write_remaining(self, wrapper: FileWrapper):
        if self.method == Method.INT:
            wrapper.write_int(self.remaining, self.remaining_size, **size_settings)
        else:
            raise ValueError(f'unsupported method: {self.method}')

    def read(self, wrapper: FileWrapper):
        size_of_size = wrapper.read_int(1, byteorder='big', signed=False)
        self.buffer_size = wrapper.read_int(size_of_size, **size_settings)
        self.buffer_bits = wrapper.read_int(size_of_size, **size_settings)
        self.data_size = wrapper.read_int(size_of_size, **size_settings)
        self.data_bits = wrapper.read_int(size_of_size, **size_settings)
        # read sorted count list
        self._read_method(wrapper)
        self._read_sorted_data_count(wrapper, size_of_size)
        # read remaining
        self.remaining_size = wrapper.read_int(size_of_size, **size_settings)
        self.remaining_bits = wrapper.read_int(size_of_size, **size_settings)
        self._read_remaining(wrapper)

    def write(self, wrapper: FileWrapper, size_of_size: int = 4):
        wrapper.write_int(size_of_size, 1, byteorder='big', signed=False)
        wrapper.write_int(self.buffer_size, size_of_size, **size_settings)
        wrapper.write_int(self.buffer_bits, size_of_size, **size_settings)
        wrapper.write_int(self.data_size, size_of_size, **size_settings)
        wrapper.write_int(self.data_bits, size_of_size, **size_settings)
        # write sorted count list
        self._write_method(wrapper)
        self._write_sorted_data_count(wrapper, size_of_size)
        # write remaining
        wrapper.write_int(self.remaining_size, size_of_size, **size_settings)
        wrapper.write_int(self.remaining_bits, size_of_size, **size_settings)
        self._write_remaining(wrapper)

    @staticmethod
    def static_read(wrapper: FileWrapper):
        instance = SegmentedBuffer()
        instance.read(wrapper)
        return instance

    @staticmethod
    def static_write(wrapper: FileWrapper, instance: 'SegmentedBuffer', size_of_size: int = 4):
        return instance.write(wrapper, size_of_size=size_of_size)

    # scan & sort data count
    def _scan_data_count(self, buffer: bytes):
        if self.method == Method.BYTE:
            if self.data_bits % 8 == 0:
                max_index = self.buffer_size - self.remaining_size
                count_dict = defaultdict(lambda: 1)
                for index in range(0, max_index, self.data_size):
                    count_dict[buffer[index:index + self.data_size]] += 1
                return count_dict, buffer[max_index:]
            else:
                raise ValueError(f'{self.data_bits} data bits is not supported in BYTE method')
        elif self.method == Method.INT:
            count_dict = defaultdict(lambda: 0)
            if self.data_bits == 8:
                for value in buffer:
                    count_dict[value] += 1
                return count_dict, 0
            elif self.data_bits % 8 == 0:
                max_index = self.data_size - self.remaining_size
                for index in range(0, max_index, self.data_size):
                    count_dict[_from_bytes(buffer[index:index + self.data_size])] += 1
                return count_dict, _from_bytes(buffer[max_index:])
            else:
                bits_io = BitsIO(buffer, self.data_bits)
                for value in bits_io:
                    count_dict[value] += 1
                return count_dict, bits_io.remaining()

    @staticmethod
    def _sort_count_dict(count_dict: Dict):
        return SortedList((DataCount(key, value) for key, value in count_dict.items()), key=lambda item: item.count)

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

    def convert(self, data_bits: int):
        if self.data_bits % data_bits != 0:
            raise ValueError()

        result = SegmentedBuffer()
        result.buffer_size = self.buffer_size
        result.buffer_bits = self.buffer_bits

        result.data_bits = data_bits
        result.data_size = get_bytes_per_bits(data_bits)

        result.remaining_bits = result.buffer_bits % result.data_bits
        result.remaining_size = get_bytes_per_bits(result.remaining_bits)

        raise BaseException('incomplete code!')

    @staticmethod
    def scan_buffer(data_bits: int, buffer: bytes, method: Method = Method.INT):
        if data_bits <= 1:
            raise ValueError(f'invalid data bits: {data_bits}')
        elif data_bits > 1024:
            raise ValueError(f'data bits is too big: {data_bits}')

        result = SegmentedBuffer()
        result.buffer_size = len(buffer)
        result.buffer_bits = result.buffer_size * 8

        result.data_bits = data_bits
        result.data_size = get_bytes_per_bits(data_bits)

        result.remaining_bits = result.buffer_bits % result.data_bits
        result.remaining_size = get_bytes_per_bits(result.remaining_bits)

        result.method = method
        count_dict, result.remaining = result._scan_data_count(buffer)
        result.sorted_data_count = SegmentedBuffer._sort_count_dict(count_dict)
        return result
