import logging
import random
import secrets
import string
from collections import defaultdict, deque
from typing import Union, Callable, Tuple

from sortedcontainers import SortedList

from py_libs import print_separator, single_quoted, to_machine_size

default_values = (string.digits + string.ascii_uppercase).encode('ascii')
default_random = random.SystemRandom()


class Node:
    __slots__ = 'count', 'codec'

    def __init__(self, count: int):
        self.count = count
        self.codec = None


class DataCount(Node):
    __slots__ = 'data'

    def __init__(self, data, count: int):
        super().__init__(count)
        self.data = data

    def __repr__(self):
        return f'DataCount: {self.data.hex()}, {self.count}: {self.codec}'


class Pair(Node):
    __slots__ = 'left', 'right'

    def __init__(self, left: Node, right: Node):
        super().__init__(left.count + right.count)
        self.left = left
        self.right = right

    def __repr__(self):
        return f'Pair: {self.count}: {self.codec}'


class Tree:
    __slots__ = 'root'

    def __init__(self, root: Node):
        self.root = root


def count_data_width(buffer: bytes, data_width: int):
    max_index = len(buffer) - (len(buffer) % data_width)
    counts = defaultdict(lambda: 0)
    for index in range(0, max_index, data_width):
        counts[buffer[index:index + data_width]] += 1
    remaining = buffer[max_index:]
    return counts, remaining


def set_tree_codecs(root: Node, initial=1):
    root.codec = initial
    stack = deque([root])
    while len(stack) != 0:
        size = len(stack)
        for index in range(size):
            node = stack.popleft()
            if isinstance(node, Pair):
                node.left.codec = (node.codec << 1) | 1
                node.right.codec = (node.codec << 1)
                stack.append(node.left)
                stack.append(node.right)


def format_codec(codec: int):
    return f'{codec:b}'[1:]


RandBytes = Callable[[int], bytes]
BufferInfo = Union[bytes, str, int, Tuple[RandBytes, int]]
data_folder_name = '.data'


def get_buffer(buffer_info: BufferInfo, logger: logging.Logger):
    if isinstance(buffer_info, bytes):
        return buffer_info
    elif isinstance(buffer_info, int):
        logger.info('generating random bytes...')
        return secrets.token_bytes(buffer_info)
    elif isinstance(buffer_info, str):
        if buffer_info.startswith(':'):
            logger.info('generating random bytes...')
            return secrets.token_bytes(to_machine_size(buffer_info[1:]))
        logger.info(f'reading file {single_quoted(buffer_info)}...')
        with open(buffer_info, 'rb') as file:
            return file.read()
    elif isinstance(buffer_info, tuple):
        logger.info('generating custom random bytes...')
        randbytes, size = buffer_info
        return randbytes(size)
    else:
        raise TypeError(f'invalid type: {type(buffer_info)}')


def pair_counts(data_count_list: SortedList):
    while len(data_count_list) != 1:
        pair = Pair(data_count_list.pop(0), data_count_list.pop(0))
        data_count_list.add(pair)
    return data_count_list[0]


def extract_data_count(node: Node):
    stack = deque()
    result = deque()
    while isinstance(node, Pair):
        stack.append(node)
        node = node.right
    result.append(node)
    while len(stack) != 0:
        node = stack.pop().left
        while isinstance(node, Pair):
            stack.append(node)
            node = node.right
        result.append(node)
    return result


def print_size(title: str, size: int):
    print(f'{title}: {size} byte(s)')


def print_percentage(title: str, value: int, total: int):
    print(f'{title}: {value} / {total} ({value / total:.2f}%)')


Number = Union[float, int]


class MinMaxAverage:
    __slots__ = 'min', 'max', 'average'

    def __init__(self, min_value: Number, max_value: Number, average: Number):
        self.min = min_value
        self.max = max_value
        self.average = average


def min_max_average(numbers):
    iterable = iter(numbers)
    try:
        min_value = max_value = average = next(iterable)
    except StopIteration:
        return None
    total = 1
    for value in iterable:
        if value > max_value:
            max_value = value
        if value < min_value:
            min_value = value
        average += value
        total += 1
    return min_value, max_value, (average / total)


def calculate_huffman_bits(buffer_info: BufferInfo, data_width: int, logger: logging.Logger = None):
    logger = logger or logging.root
    buffer = get_buffer(buffer_info, logger)

    logger.info('counting data...')
    counts, remaining = count_data_width(buffer, data_width)

    logger.info('sorting...')
    data_count_list = SortedList((DataCount(key, value) for key, value in counts.items()), key=lambda item: item.count)

    logger.info('pairing...')
    root = pair_counts(data_count_list)

    logger.info('setting codecs...')
    set_tree_codecs(root)

    logger.info('extracting data count...')
    final_data_count_list = extract_data_count(root)

    assert len(final_data_count_list) == len(counts)

    logger.info('calculating total bits...')
    codecs_bits = 0
    for data_count in final_data_count_list:
        codecs_bits += data_count.count * len(format_codec(data_count.codec))

    # calculate information

    min_count, max_count, average_count = min_max_average(map(lambda item: item.count, final_data_count_list))

    buffer_size = len(buffer)
    buffer_bits = buffer_size * 8

    unique_data_number = len(counts)
    possible_data_number = 2 ** (data_width * 8)
    unique_data_percentage = (unique_data_number / possible_data_number) * 100

    scanned_size = buffer_size - (buffer_size % data_width)
    scanned_bits = scanned_size * 8

    # codecs
    codecs_percentage = (codecs_bits / scanned_bits) * 100

    # dict
    dict_bits = (data_width * 8) * unique_data_number
    dict_percentage = (dict_bits / scanned_bits) * 100

    # total
    total_bits = dict_bits + codecs_bits
    total_percentage = (total_bits)

    remaining_format = ' '.join(f'{value:0<2x}' for value in remaining)

    # print info

    print_separator(title='buffer info', char='~')
    print(f'buffer size: {buffer_size} byte(s) ({buffer_size * 8} bits)')
    print(f'data width: {data_width} byte(s) ({data_width * 8} bits)')
    print(f'scanned size: {scanned_size} byte(s) ({scanned_bits} bits)')
    print(f'remaining: {len(remaining)} byte(s) ({len(remaining) * 8} bits) [{remaining_format}]')
    print(f'minimum count: {min_count}, maximum count: {max_count}, average count: {average_count:.1f}')

    print_separator(title='compressing info', char='~')
    print(f'unique data number: {unique_data_number} / {possible_data_number} ({unique_data_percentage:.2f}%)')
    print(f'codecs bits: {codecs_bits} / {buffer_bits} ({codecs_percentage:.2f}%)'
          f' ({codecs_bits - scanned_bits:+} bits)')
    print(f'dict bits: {dict_bits} / {buffer_bits} ({dict_percentage:.2f}%) ({dict_bits - scanned_bits:+})')

    # print_separator(title='final result', char='~')
    # for item in final_data_count_list:
    #     print(item)

# ================= OLD CODES =================

#
# def calculate(values_or_count: Union[str, int], buffer_size: int, data_width: int):
#     values = default_values[:values_or_count] if isinstance(values_or_count, int) else values_or_count
#     values_count = len(set(values))
#
#     buffer_init = default_random.randbytes
#     buffer_slice = bytes.__getitem__
#
#     buffer = buffer_init(values_count)
#
#     count = defaultdict(lambda: 0)
#     max_index = buffer_size - (buffer_size % data_width)
#     for index in range(0, max_index, data_width):
#         count[buffer_slice(buffer, slice(index, index + data_width))] += 1
#
#     remaining = buffer_slice(buffer, slice(max_index, None))
#
#     count_list = sorted(deque((key, value) for key, value in count.items()), key=lambda t: t[1])
#
#     print(count_list)
#     print(repr(remaining))
