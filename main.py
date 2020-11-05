# allocating memory as much as needed.
import logging
import math
import sys
from collections import defaultdict
from typing import Union

from py_libs.io import get_file_size
from py_libs.misc import generate_password
from py_libs.table import Table, TableSetting
from py_libs.utils import to_machine_size, to_human_size

logging.basicConfig(stream=sys.stdout, format='%(levelname)s: %(message)s', level=logging.DEBUG)

file_size = get_file_size('music_for_programming_49-julien_mier.mp3')


def compute_info(size: Union[str, int], max_data_width=32, table_settings: TableSetting = None):
    if isinstance(size, str):
        size = to_machine_size(size)
    bits = size * 8

    table_settings = table_settings or TableSetting(vertical_margin=1, title_align='<', row_align='>')
    table = Table(9, table_settings)

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


print(generate_password())

# test_buffer = get_buffer(':10 MB', logging.root)
#
# stop_watch = StopWatch(True)
# count_data_width_first(test_buffer, 16)
# stop_watch.lap()
# count_data_width_second(test_buffer, 16)
# stop_watch.lap()
# stop_watch.print()

# print_info("70 MB", max_data_width=128)
# info = scan_buffer('music_for_programming_49-julien_mier.mp3', 8)
# print_info(info)
