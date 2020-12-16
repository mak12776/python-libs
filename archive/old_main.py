import base64
import hashlib
import marshal
import math
from collections import defaultdict
from io import RawIOBase
from typing import Union

import numpy

from library.io import get_file_size
from library.table import TableSetting, Table
from library.utils import to_machine_size, to_human_size

file_size = get_file_size('music_for_programming_49-julien_mier.mp3')


def compute_info(size: Union[str, int], max_data_width=32, table_settings: TableSetting = None):
    if isinstance(size, str):
        size = to_machine_size(size)
    bits = size * 8

    table_settings = table_settings or TableSetting(vertical_margin=1, title_align='<', row_align='>')
    table = Table(table_settings)

    table.set_titles('data bits', 'scanned', 'remaining', 'total count',
                     'possible data number', 'max unique data number', 'max dict size',
                     'max data diff', 'max data diff bits')
    for data_bits in range(2, max_data_width + 1):
        scanned_bits = bits - (bits % data_bits)
        remaining_bits = bits % data_bits
        total_count = scanned_bits // data_bits

        possible_data_number = 2 ** data_bits

        max_unique_data_number = min(possible_data_number, total_count)
        max_dict_size = max_unique_data_number * data_bits

        max_data_diff = possible_data_number - max_unique_data_number
        max_data_diff_bits = math.ceil(math.log2(max_data_diff)) if max_data_diff else 0

        table.add_row(f'{data_bits}', f'{scanned_bits:,}', f'{remaining_bits:,}', f'{total_count:,}',
                      f'2 ^ {data_bits:,}', f'{max_unique_data_number:,}', f'{max_dict_size:,}',
                      f'{max_data_diff}', f'{max_data_diff_bits}')

    table.print()
    print(f'for file size: {to_human_size(size)} ({bits:,} bits)')


class DataCount:
    __slots__ = 'data', 'count'

    def __init__(self, data, count):
        self.data = data
        self.count = count

    def __eq__(self, other: 'DataCount'):
        return self.data == other.data

    def __lt__(self, other: 'DataCount'):
        return self.data < other.data


def count_data_width_first(buffer: bytes, data_bits: int):
    if data_bits <= 0:
        raise ValueError(f'invalid data bits: {data_bits}')
    if data_bits % 8 == 0:
        data_bits //= 8
        buffer_view = memoryview(buffer)
        max_index = len(buffer) - (len(buffer) % data_bits)
        counts = defaultdict(lambda: 0)
        for index in range(0, max_index, data_bits):
            counts[buffer_view[index:index + data_bits]] += 1
        remaining = buffer_view[max_index:]
        return counts, remaining
    raise BaseException(f'incomplete code for data_bits: {data_bits}')


def count_data_width_second(buffer: bytes, data_bits: int):
    if data_bits <= 0:
        raise ValueError(f'invalid data bits: {data_bits}')
    if data_bits % 8 == 0:
        data_bits //= 8
        max_index = len(buffer) - (len(buffer) % data_bits)
        counts = defaultdict(lambda: 0)
        for index in range(0, max_index, data_bits):
            counts[buffer[index:index + data_bits]] += 1
        remaining = buffer[max_index:]
        return counts, remaining
    raise BaseException(f'incomplete code for data_bits: {data_bits}')


def hash_bytes(name, buffer: bytes):
    h = hashlib.new(name, buffer)
    h.update(buffer)
    return h.digest()


def get_function_title(func):
    buffer = marshal.dumps(func.__code__)
    digest = base64.b64encode(hash_bytes('sha256', buffer)).decode('ascii')
    return f'{func.__name__}:{digest}:{len(buffer)}'


def simple_function(size: int):
    numbers = numpy.ndarray((size,), numpy.int32)
    for index in range(size):
        numbers[index] = index
    for index in range(size):
        numbers[index] *= 100
    return numbers


number_size = 8


def read_numbers(file: RawIOBase):
    return numpy.frombuffer(file.read(), numpy.int32)


def write_numbers(numbers: numpy.ndarray, file: RawIOBase):
    file.write(numbers.tobytes())

# read_write = (read_numbers, write_numbers)
# title = get_function_title(simple_function)
#
# stop_watch = StopWatch(True)
# result = DataCache('.data').cached_function(title, read_write, simple_function, 20_000_000)
# stop_watch.lap()
#
# stop_watch.print()


# test_buffer = get_buffer(':10 MB', logging.root)
# stop_watch = StopWatch(True)
# count_data_width_first(test_buffer, 16)
# stop_watch.lap()
# count_data_width_second(test_buffer, 16)
# stop_watch.lap()
# stop_watch.print()

# print_info("70 MB", max_data_width=128)
# info = scan_buffer('music_for_programming_49-julien_mier.mp3', 8)
# print_info(info)

# class Info:
#     __slots__ = ('buffer_bits', 'buffer_size',
#                  'data_bits', 'data_size',
#                  'remaining_bits', 'remaining_size',
#                  'possible_data_number', 'total_data_number')
#
#
# def get_bytes_per_bits(bits: int):
#     return ceil_module(bits, 8)
#
#
# def compute_info(buffer_bits: int, data_bits: int):
#     info = Info()
#
#     info.buffer_bits = buffer_bits
#     info.buffer_size = get_bytes_per_bits(buffer_bits)
#
#     info.data_bits = data_bits
#     info.data_size = get_bytes_per_bits(data_bits)
#
#     info.remaining_bits = buffer_bits % data_bits
#     info.remaining_size = get_bytes_per_bits(info.remaining_bits)
#
#     info.total_data_number = buffer_bits // data_bits
#     info.possible_data_number = 2 ** data_bits
#
#     # worst case
#     # maximum data count = total_data_number
#     # minimum data count = 0
#     # maximum data difference = 0
#
#     # best case
#     # minimum data count = ceil_module(total_data_number, possible_data_number)
#     # maximum data count = floor_module(total_data_number, possible_data_number)
#     # maximum data difference = 1
#
#     return info
#
#
# def print_info(info: Info, table_settings: TableSetting = None):
#     table_settings = table_settings or TableSetting(vertical_margin=1, title_align='<', row_align='>')
#     table = Table(table_settings)
#
#     table.set_titles('buffer bits', 'buffer size',
#                      'data bits', 'remaining bits',
#                      'possible data number', 'total data number')
#
#     table.add_row(*map(str, [info.buffer_bits, info.buffer_size,
#                              info.data_bits, info.remaining_bits,
#                              info.possible_data_number, info.total_data_number]))
#     table.print()
