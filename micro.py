import re
from collections import deque
from enum import IntEnum, auto
from typing import Callable


class ErrorEnum(IntEnum):
    INVALID_STATE = auto()
    INVALID_DUMP = auto()
    INVALID_DIS = auto()

    EXTRA_STATE = auto()
    EXTRA_DUMP = auto()
    EXTRA_DIS = auto()

    INVALID_HEADER = auto()
    UNKNOWN_HEADER = auto()
    HEADERS_NOT_FOUND = auto()


class LexerError(Exception):
    __slots__ = 'error', 'line'

    def __init__(self, error: ErrorEnum, line: str = None):
        self.error = error
        self.line = line

    def __str__(self):
        return f'{self.__class__.__name__}({self.error.name}, {self.line!r})'


_blanks = ' \t\r\n'
_prefix = '#='


class NextLine:
    __slots__ = '_next', '_deque'

    def __init__(self, next_line: Callable[[], str]):
        self._next = next_line
        self._deque = deque()

    def push(self, other):
        self._deque.append(other)

    def __call__(self):
        if self._deque:
            return self._deque.pop()
        return self._next()

    def has_next(self):
        if self._deque:
            return True
        line = self._next()
        if line:
            self._deque.append(line)
            return True
        return False


_state_patterns = [
    "pc  0000  sp  0000  sr  0000  cg  0000",
    "r04 0000  r05 0000  r06 0000  r07 0000",
    "r08 0000  r09 0000  r10 0000  r11 0000",
    "r12 0000  r13 0000  r14 0000  r15 0000"
]

for _index in range(len(_state_patterns)):
    _state_patterns[_index] = _state_patterns[_index].replace('0000', r'(\d{4})')


def read_state(next_line: NextLine):
    registers = [0] * 16
    for index in range(len(_state_patterns)):
        line = next_line()
        if not line:
            raise LexerError(ErrorEnum.INVALID_STATE)
        striped_line = line.strip(_blanks)
        match = re.fullmatch(_state_patterns[index], striped_line)
        if not match:
            raise LexerError(ErrorEnum.INVALID_STATE, line)
        for j_index, number in enumerate(match.groups()):
            registers[index + j_index] = int(number)
    return registers


def read_empty_lines(next_line: NextLine):
    while True:
        line = next_line()
        if len(line) == 0:
            return
        striped_line = line.strip(_blanks)
        if striped_line:
            next_line.push(line)
            return


dump_pattern = r'([\da-f]{4}): {3}((?:[\da-f]{4} ){8}|\*)'


def read_dump(next_line: NextLine):
    result = bytearray()
    while True:
        line = next_line()
        if len(line) == 0:
            if len(result) != 0:
                return result
            raise LexerError(ErrorEnum.INVALID_DUMP)
        striped_line = line.strip(_blanks)
        match = re.match(dump_pattern, striped_line)
        if match is None:
            if len(result) != 0:
                return result
            raise LexerError(ErrorEnum.INVALID_DUMP)

        print(match.groups())


class MicroProblem:
    __slots__ = 'state', 'dis', 'dump'

    def __init__(self):
        self.state = self.dis = self.dump = None

    def is_valid(self):
        return self.state is not None and self.dis is not None or self.dump is not None


def read_lines(next_line: NextLine):
    result = MicroProblem()
    while True:
        read_empty_lines(next_line)

        line = next_line()
        if not line:
            if result.is_valid():
                break
            raise LexerError(ErrorEnum.HEADERS_NOT_FOUND)

        striped_line = line.strip(_blanks)
        if not striped_line.startswith(_prefix):
            raise LexerError(ErrorEnum.INVALID_HEADER, line)
        header = striped_line[len(_prefix):].strip(_blanks)

        read_empty_lines(next_line)

        if header == 'state':
            if result.state is not None:
                raise LexerError(ErrorEnum.EXTRA_STATE)
            result.state = read_state(next_line)
        elif header == 'dump':
            if result.dump is not None:
                raise LexerError(ErrorEnum.EXTRA_DUMP)
            result.dump = read_dump(next_line)
        elif header == 'dis':
            if result.dis is not None:
                raise LexerError(ErrorEnum.EXTRA_DIS)
            print('DIS:')
        else:
            raise LexerError(ErrorEnum.UNKNOWN_HEADER, line)


def main(*args):
    with open(r'D:\Codes\micro-test\01-tutorial.txt', 'rt') as text_file:
        read_lines(NextLine(text_file.readline))
