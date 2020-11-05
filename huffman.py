import logging
import secrets
from collections import defaultdict, deque
from typing import Union, Callable, Tuple, Dict, MutableSequence

from sortedcontainers import SortedList

from py_libs.fmt import print_separator, printf, single_quoted
from py_libs.math import min_max_average
from py_libs.utils import to_machine_size, to_human_size


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


class Bits:
    __slots__ = 'value', 'size'

    def __init__(self, value: int, size: int):
        self.value = value
        self.size = size


DataType = Union[int, bytes]
CountDict = Dict[DataType, int]

size_of_size = 4


class SegmentedBuffer:
    __slots__ = 'count_dict', 'remaining'

    def __init__(self, count_dict: CountDict, remaining: bytes):
        self.count_dict = count_dict
        self.remaining = remaining


class HuffmanInfo:
    __slots__ = 'buffer', 'data_bits', 'segmented_buffer', 'codec_list'

    def __init__(self, buffer: bytes, data_bits: int,
                 segmented_buffer: SegmentedBuffer, codec_list: MutableSequence[DataCount]):
        self.buffer = buffer
        self.data_bits = data_bits
        self.segmented_buffer = segmented_buffer
        self.codec_list = codec_list


default_read_size = 4


def convert_count_dict(source: CountDict, data_bits: int, target_bits: int):
    pass


def count_data_width(buffer: bytes, data_bits: int):
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


Codec = int


def codec_len(codec: Codec):
    return len(f'{codec:b}') - 1


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


def scan_buffer(buffer_info: BufferInfo, data_bits: int, logger: logging.Logger = None):
    logger = logger or logging.root
    buffer = get_buffer(buffer_info, logger)

    logger.info('counting data...')
    data_count_dict, remaining = count_data_width(buffer, data_bits)

    logger.info('sorting...')
    data_count_list = SortedList(
        (DataCount(key, value) for key, value in data_count_dict.items()), key=lambda item: item.count)

    logger.info('pairing...')
    root = pair_counts(data_count_list)

    logger.info('setting codecs...')
    set_tree_codecs(root)

    logger.info('extracting data count...')
    codec_list = extract_data_count(root)

    assert len(codec_list) == len(data_count_dict), f'{len(codec_list)} != {len(data_count_dict)}'

    segmented_buffer = SegmentedBuffer(data_count_dict, remaining)
    return HuffmanInfo(buffer, data_bits, segmented_buffer, codec_list)


def print_info(info: HuffmanInfo):
    buffer_bits = len(info.buffer) * 8
    scanned_bits = buffer_bits - (buffer_bits % info.data_bits)
    remaining_bits = len(info.segmented_buffer.remaining) * 8
    remaining_format = ' '.join(f'w{value:0<2x}' for value in info.segmented_buffer.remaining)

    possible_data_number = 256 ** info.data_bits
    unique_data_number = len(info.codec_list)
    unique_data_percentage = (unique_data_number / possible_data_number) * 100

    min_count, max_count, average_count = min_max_average(
        map(lambda item: item.count, info.codec_list))

    # codecs
    codecs_bits = 0
    for data_count in info.codec_list:
        codecs_bits += data_count.count * codec_len(data_count.codec)
    codecs_percentage = (codecs_bits / buffer_bits) * 100
    codecs_diff = codecs_bits - buffer_bits

    # dict
    dict_bits = info.data_bits * unique_data_number
    dict_percentage = (dict_bits / buffer_bits) * 100
    dict_diff = dict_bits - buffer_bits

    # total
    total_bits = codecs_bits + dict_bits
    total_percentage = (total_bits / buffer_bits) * 100
    total_diff = total_bits - buffer_bits

    # print info

    print_separator(title='buffer info', char='~')
    print(f'buffer: {buffer_bits:,} bits ({to_human_size(len(info.buffer))})')
    print(f'data: {info.data_bits:,} bits')
    print(f'scanned: {scanned_bits:,} bits')
    print(f'remaining: {remaining_bits:,} bites [{remaining_format}]')

    print_separator(title='compressing info', char='~')
    print(f'unique data number: {unique_data_number:,} / {possible_data_number:,} ({unique_data_percentage:.2f}%)')
    print(f'count info: >= {min_count}, <= {max_count}, ~ {average_count:.2f}')
    printf('{0}: {1:,} bits ({2:.2f}%) ({3:+,} bits)', 'codecs', codecs_bits, codecs_percentage, codecs_diff)
    printf('{0}: {1:,} bits ({2:.2f}%) ({3:+,} bits)', 'dict', dict_bits, dict_percentage, dict_diff)
    printf('{0}: {1:,} bits ({2:.2f}%) ({3:+,} bits)', 'total', total_bits, total_percentage, total_diff)

# ================= OLD CODES =================

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
