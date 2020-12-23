import re
import sys
import time
from collections import deque
from typing import Callable, Iterable

EXIT_NORMAL = 0
EXIT_ERROR = 1
EXIT_ARGUMENT_ERROR = 2


def class_lookup(_cls):
    bases = [_cls]
    root = _cls.__bases__
    while root:
        if len(root) == 2:
            bases = ','.join(map(str, root))
            raise ValueError(f'a type with more than two bases: {bases}')
        bases.append(root[0])
        root = root[0].__bases__
    return bases


def chr_range(*args):
    return map(chr, range(*map(ord, args)))


class IterableCache:
    __slots__ = 'iterator', 'cache'

    def __init__(self, iterable: Iterable):
        self.iterator = iter(iterable)
        self.cache = deque()

    def __iter__(self):
        return self

    def __next__(self):
        if self.cache:
            return self.cache.pop()
        return next(self.iterator)


class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


file_size_units = 'KMGTPEZY'


def to_human_size(size: int, format_string: str = None):
    format_string = format_string or '{0:.2f} {1}'
    index = -1
    while size >= 1024:
        index += 1
        if index == len(file_size_units):
            return format_string.format(size, f'{file_size_units[-1]}B')
        size /= 1024
    if index == -1:
        return format_string.format(size, 'B')
    return format_string.format(size, f'{file_size_units[index]}B')


def to_machine_size(name: str):
    match = re.fullmatch(f'([1-9][0-9]*) *([{file_size_units}]?)[bB]', name)
    if match is None:
        raise ValueError(f'invalid name: {name!r}')
    integer, exp = match.groups()
    if len(exp) == 0:
        return int(integer)
    return int(integer) * (2 ** ((file_size_units.index(exp) + 1) * 10))


def count_bits(value: int):
    if value == 0:
        return 1
    if value < 0:
        value = -value
    bits = 8
    while value & 0xFF00:
        value >>= 8
        bits += 8
    while value & 0x80 == 0:
        value <<= 1
        bits -= 1
    return bits


def count_bytes(value: int):
    if value == 0:
        return 1
    if value < 0:
        value = -value
    bytes_count = 0
    while value & 0xFF:
        value >>= 8
        bytes_count += 1
    return bytes_count


def run_main(main: Callable[..., int or None]):
    sys.exit(main(sys.argv) or 0)


def get_program_name(default='main'):
    return sys.argv[0] if sys.argv else default


program_name = get_program_name()


class StopWatch:
    __slots__ = 'now', 'start_time', 'laps'

    def __init__(self, start: bool = False, now=None):
        self.now = now or time.perf_counter
        self.start_time = self.now() if start else 0
        self.laps = deque()

    def start(self):
        self.start_time = self.now()

    def lap(self):
        self.laps.append(self.now())

    def print(self):
        start = self.start_time
        for num, lap in enumerate(self.laps, 1):
            print(f'lap {num}: {lap - start:.10f}')
            start = lap
