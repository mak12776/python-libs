# first locating the "fmt.h" inside the "scl" folder
from collections import deque
import os
from typing import Callable
import py_libs


def search_files(discover: Callable[[str], bool], root: str):
    for root, dirs, files in os.walk(root):
        for name in files:
            if discover(name):
                yield os.path.join(root, name)


def strip_if_exist(string: str, starts: str, end: str):
    if string.startswith(starts) and string.endswith(end):
        return string[len(starts): -len(end)]
    return None


class Mark:
    __slots__ = '_name', '_checks'

    def __init__(self, name, checks=None):
        self._name = name
        self._checks = set() if checks is None else set(checks)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def checks(self):
        return self._checks

    def __str__(self):
        return f'Mark({self._name}, {",".join(self._checks)}'

    def __repr__(self):
        checks_string = ' '.join(map(lambda s: s.upper(), self._checks))
        return f'Mark({self._name}, {checks_string})'

    def __eq__(self, other) -> bool:
        return isinstance(other, Mark) and self._name == other._name and self._checks == other._checks


def set_stat(name: str, stat: str):
    for item in marks:
        if item.name == name:
            item.checks.add(stat)


scl_root_path = '..\\cpp-libs\\cpp-libs\\scl'
header_name = 'fmt.h'

default_marks = ('start', 'end')
function_names = ['get_line_valist', 'format_valist']

marks = deque(Mark(name) for name in function_names)
true_marks = deque(Mark(name, default_marks) for name in function_names)
marks_index = deque((name, deque()) for name in function_names)


class MainError(Exception):
    pass


def main():
    result = list(search_files(lambda s: s == header_name, scl_root_path))
    if len(result) > 1:
        raise MainError(f'more than one "fmt.h" files found: {",".join(result)}')
    fmt_path = result[0]
    print(f'format path found: "{fmt_path}"')

    buffer = py_libs.read_file_name(fmt_path, False).decode('ascii')
    lines = buffer.splitlines(False)

    for num, striped_line in enumerate(map(lambda s: s.strip('\t'), lines), 1):
        striped_text = strip_if_exist(striped_line, '//#[', ']')
        if isinstance(striped_text, str):
            name, stat = striped_text.split(' ')
            set_stat(name, stat)

    if true_marks != marks:
        raise MainError(f'marks does not match, searched marks: {marks}')
    print('marks have been found!')
