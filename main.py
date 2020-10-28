# allocating memory as much as needed.
from collections import deque, defaultdict
from random import choice
from typing import List, Dict

from py_libs import chr_range, single_quoted

chars_list = deque(chr_range('A', 'Z'))
width = 10_00
_data = ''.join(choice(chars_list) for i in range(width))

print('counting data...')
counts_dict: Dict[str, int] = defaultdict(lambda: 0)
for ch in _data:
    counts_dict[ch] += 1


class Node:
    __slots__ = 'count'

    def __init__(self, count: int):
        self.count = count


class DataCount(Node):
    __slots__ = 'data'

    def __init__(self, data, count):
        super().__init__(count)
        self.data = data

    def __repr__(self):
        return f'DataCount({single_quoted(self.data)}, {self.count})'


class Pair(Node):
    __slots__ = 'first', 'second', 'count'

    def __init__(self, first: Node, second: Node):
        super(Pair, self).__init__(first.count + second.count)
        self.first = first
        self.second = second

    def __repr__(self):
        return f'Pair({self.first}, {self.second}, {self.count})'


print('sorting...')
counts: List[Node] = sorted(list(DataCount(key, value) for key, value in counts_dict.items()),
                            key=lambda item: item.count)

print('pairing data counts..')
while len(counts) != 1:
    counts.append(Pair(counts.pop(-1), counts.pop(-1)))
    counts.sort(key=lambda item: item.count)

root = counts[0]
