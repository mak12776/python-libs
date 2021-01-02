import re
import sys
import time
from collections import deque
from typing import Callable, Iterable, Any

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
_default_time_func = time.perf_counter
_default_time_format = '.10f'


class StopWatch:
    __slots__ = '_now', '_start_time', '_laps', '_format'

    def __init__(self, start: bool = False, now: Callable[[], Any] = None, time_format: str = None):
        self._now = now or _default_time_func
        self._start_time = self._now() if start else 0
        self._laps = deque()
        self._format = time_format or _default_time_format

    def start(self):
        self._start_time = self._now()

    def lap(self):
        self._laps.append(self._now())

    @property
    def laps(self):
        return self._laps

    @property
    def differences(self):
        last = self._start_time
        result = list()
        for _next in self._laps:
            result.append(_next - last)
            last = _next
        return result

    def print(self, file=sys.stdout):
        start = self._start_time
        for num, lap in enumerate(self._laps, 1):
            print(f'lap {num}: {lap - start:{self._format}}', file=file)
            start = lap


class StopWatchLogger:
    __slots__ = '_now', '_start_time', '_laps', '_format'

    def __init__(self, start: bool = False, now: Callable[[], Any] = None, time_format: str = None):
        self._now = now or _default_time_func
        self._start_time = now() if start else 0
        self._laps = deque()
        self._format = time_format or _default_time_format

    def start(self):
        self._start_time = self._now()

    def lap(self, message: str):
        self._laps.append((self._now(), message))

    @property
    def laps(self):
        return self._laps

    @property
    def differences(self):
        last = self._start_time
        result = list()
        for _next in self._laps:
            result.append(_next - last)
            last = _next
        return result

    def print(self, file=sys.stdout):
        start = self._start_time
        for num, (lap, log) in enumerate(self._laps, 1):
            print(f'{lap - start:{self._format}}: {log}', file=file)
            start = lap
