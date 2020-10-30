import logging
import random
import secrets
import string
from collections import defaultdict, deque
from typing import Union, Callable

from py_libs import print_separator


def search_function(name):
    print(name)


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


def calculate_huffman_bits(buffer_size: int, data_width: int,
                           randbytes: Callable[[int], bytes] = None,
                           logger: logging.Logger = None):
    randbytes = randbytes or secrets.token_bytes
    logger = logger or logging.root

    logger.info('generating bytes...')
    buffer = randbytes(buffer_size)

    logger.info('counting data...')
    counts = defaultdict(lambda: 0)
    max_index = buffer_size - (buffer_size % data_width)
    for index in range(0, max_index, data_width):
        counts[buffer[index: index + data_width]] += 1
    remaining = buffer[max_index:]

    data_type_number = len(counts)
    possible_data_type_number = 2 ** (data_width * 8)
    data_type_fraction = data_type_number / possible_data_type_number

    logger.info('sorting...')
    data_count_list = list(DataCount(key, value) for key, value in counts.items())
    data_count_list.sort(key=lambda _data_count: _data_count.count)

    logger.info('converting to deque...')
    data_count_list = deque(data_count_list)

    logger.info('pairing...')
    while len(data_count_list) != 1:
        pair = Pair(data_count_list.popleft(), data_count_list.popleft())
        index = 0
        for index, temp in enumerate(data_count_list):
            if pair.count <= temp.count:
                break
        data_count_list.insert(index, pair)

    root = data_count_list[0]

    logger.info('setting codecs...')

    root.codec = ''
    stack = deque([root])

    while len(stack) != 0:
        size = len(stack)
        for index in range(size):
            node = stack.popleft()
            if isinstance(node, Pair):
                node.left.codec = node.codec + '1'
                node.right.codec = node.codec + '0'
                stack.append(node.left)
                stack.append(node.right)

    logger.info('extracting data count...')
    final_data_count_list = deque()
    stack = deque([root])
    while len(stack) != 0:
        size = len(stack)
        for index in range(size):
            node = stack.popleft()
            if isinstance(node, Pair):
                stack.append(node.left)
                stack.append(node.right)
            elif isinstance(node, DataCount):
                final_data_count_list.append(node)

    compressed_bits = 0
    logger.info('calculating total bits...')
    for data_count in final_data_count_list:
        compressed_bits += data_count.count * len(data_count.codec)

    total_bytes = max_index
    total_bits = max_index * 8
    compressed_bits_fraction = compressed_bits / total_bits
    compressed_bits_diff = compressed_bits - total_bits

    # print info
    remaining_format = ' '.join(f'{value:0<2x}' for value in remaining)

    print_separator(title='results', char='~')
    print(f'buffer size: {buffer_size} byte[s] ({buffer_size * 8} bits)')
    print(f'total size: {total_bytes} byte[s] ({total_bits} bits)')
    print(f'data width: {data_width} byte[s] ({data_width * 8} bits)')
    print(f'remaining: [{remaining_format}] {len(remaining)} ({len(remaining) * 8} byte[s] bits)')

    print(f'data type number: {data_type_number} / {possible_data_type_number} ({data_type_fraction:.4f})')

    print(f'total bits: {compressed_bits} / {max_index * 8}'
          f' ({compressed_bits_fraction:.4f}) ({compressed_bits_diff} bits)')

    # print_separator(title='final result', char='~')
    # for item in final_data_count_list:
    #     print(item)


def shuffle_str(s: str):
    ls = list(s)
    default_random.shuffle(ls)
    return ''.join(ls)


def calculate(values_or_count: Union[str, int], buffer_size: int, data_width: int):
    values = default_values[:values_or_count] if isinstance(values_or_count, int) else values_or_count
    values_count = len(set(values))

    buffer_init = default_random.randbytes
    buffer_slice = bytes.__getitem__

    buffer = buffer_init(values_count)

    count = defaultdict(lambda: 0)
    max_index = buffer_size - (buffer_size % data_width)
    for index in range(0, max_index, data_width):
        count[buffer_slice(buffer, slice(index, index + data_width))] += 1

    remaining = buffer_slice(buffer, slice(max_index, None))

    count_list = sorted(deque((key, value) for key, value in count.items()), key=lambda t: t[1])

    print(count_list)
    print(repr(remaining))
