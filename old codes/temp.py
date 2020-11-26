from collections import deque, defaultdict
from random import choice
from typing import List, Dict

from py_libs.fmt import single_quoted
from py_libs.utils import chr_range


def print_title(title: str, max_length: int = 80):
    max_length - len(title)
    print(f'{title}')


class Node:
    __slots__ = 'count', 'depth', 'codec'

    def __init__(self, count: int, depth: int):
        self.count = count
        self.depth = depth
        self.codec = ''


class DataCount(Node):
    __slots__ = 'data'

    def __init__(self, data, count):
        super().__init__(count, 0)
        self.data = data

    def __repr__(self):
        return f'DataCount({self.depth}, {single_quoted(self.codec)}, {single_quoted(self.data)}, {self.count})'


class Pair(Node):
    __slots__ = 'first', 'second', 'count'

    def __init__(self, first: Node, second: Node):
        if first.depth > second.depth:
            set_tree_depth(second, first.depth)
        elif first.depth < second.depth:
            set_tree_depth(first, second.depth)
        super(Pair, self).__init__(first.count + second.count, first.depth + 1)
        self.first = first
        self.second = second

    def __repr__(self):
        return f'Pair({self.depth})'


def set_tree_depth(root: 'Node', depth: int):
    stack = deque([root])
    while len(stack) != 0:
        size = len(stack)
        for index in range(size):
            node = stack.popleft()
            node.depth = depth
            if isinstance(node, Pair):
                stack.append(node.first)
                stack.append(node.second)
        depth -= 1


def print_size(string: str) -> int:
    length = len(string)
    print(string)
    return length


def node_format(node: Node):
    if isinstance(node, DataCount):
        return f'{node.count} {single_quoted(node.data)} [{node.depth}]'
    elif isinstance(node, Pair):
        return f'{node.count} [{node.depth}]'
    else:
        raise ValueError(f'unknown type: {type(node)}')


def format_node(node: Node, junction: str):
    if isinstance(node, Pair):
        return f'{junction} {node_format(node)} {junction}'
    return f'{junction}-- {node_format(node)}'


def print_tree(root: Node, junction: str = '+', vertical: str = '|'):
    stack = deque()
    line_prefix = ''
    while isinstance(root, Pair):
        text = format_node(root, junction)
        print(line_prefix + text)

        stack.append(root)
        root = root.first

        line_prefix += (len(text) - 1) * ' '
    print(stack)
    raise BaseException('incomplete code')


print_title('generating values...')
chars_list = deque(chr_range('A', 'Z'))
width = 10_00
_data = ''.join(choice(chars_list) for i in range(width))

print_title('counting data...')
counts_dict: Dict[str, int] = defaultdict(lambda: 0)
for ch in _data:
    counts_dict[ch] += 1

print_title('sorting...')
counts: List[Node] = sorted(list(DataCount(key, value) for key, value in counts_dict.items()),
                            key=lambda item: item.count)

print_title('pairing data counts...')
while len(counts) != 1:
    counts.append(Pair(counts.pop(0), counts.pop(0)))
    counts.sort(key=lambda item: item.count)


def set_tree_codec(root: Node):
    if isinstance(root, DataCount):
        root.codec = '1'
        return
    root.codec = ''
    stack = deque([root])
    while len(stack) != 0:
        size = len(stack)
        for step in range(size):
            node = stack.pop()
            if isinstance(node, Pair):
                node.first.codec = node.codec + '1'
                node.second.codec = node.codec + '0'
                stack.append(node.first)
                stack.append(node.second)


print_title('setting node codecs...')
set_tree_codec(counts[0])


def extract_data_count(root: Node):
    stack = deque([root])
    while len(stack) != 0:
        node = stack.pop()
        if isinstance(node, DataCount):
            yield node
        elif isinstance(node, Pair):
            stack.append(node.first)
            stack.append(node.second)


print_title('extracting data count...')
data_count_list = deque(extract_data_count(counts[0]))

print_title('everything done.')

for item in data_count_list:
    print(item)
