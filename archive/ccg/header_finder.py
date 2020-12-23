# first locating the "fmt.h" inside the "scl" folder
from collections import deque
from os import path, walk
from typing import Callable

# file searcher
from library.sio import read_file_name

scl_root_path = '..\\cpp-libs\\cpp-libs\\scl'
header_name = 'fmt.h'


def search_files(discover: Callable[[str], bool], root: str):
    for root, dirs, files in walk(root):
        for name in files:
            if discover(name):
                yield path.join(root, name)


def strip_if_exist(string: str, starts: str, end: str):
    if string.startswith(starts) and string.endswith(end):
        return string[len(starts): -len(end)]
    return None


def search_fmt_header():
    header_path = list(search_files(lambda s: s == header_name, scl_root_path))
    if len(header_path) > 1:
        raise ValueError(f'more than one "fmt.h" files found: {", ".join(header_path)}')
    return header_path[0]


# Mark searcher

class Mark:
    __slots__ = 'name', 'checks'

    def __init__(self, name, checks=None):
        self.name = name
        self.checks = set() if checks is None else set(checks)

    def __repr__(self):
        checks_string = ' '.join(map(lambda s: s.upper(), self.checks))
        return f'Mark({self.name}, {checks_string})'

    def __eq__(self, other) -> bool:
        return isinstance(other, Mark) and self.name == other.name and self.checks == other.checks


def set_stat(name: str, stat: str):
    for item in marks:
        if item.name == name:
            item.checks.add(stat)


default_marks = ('start', 'end')
function_names = ['get_line_valist', 'format_valist']

marks = deque(Mark(name) for name in function_names)
true_marks = deque(Mark(name, default_marks) for name in function_names)
marks_index = deque((name, deque()) for name in function_names)


class MainError(Exception):
    pass


def main():
    fmt_path = search_fmt_header()
    print(f'header path found: "{fmt_path}"')

    buffer = read_file_name(fmt_path).decode('ascii')
    lines = buffer.splitlines(False)

    for num, striped_line in enumerate(map(lambda s: s.strip('\t'), lines), 1):
        striped_text = strip_if_exist(striped_line, '//#[', ']')
        if isinstance(striped_text, str):
            name, stat = striped_text.split(' ')
            set_stat(name, stat)

    if true_marks != marks:
        raise MainError(f'marks does not match, searched marks: {marks}')
    print('marks have been found!')

    # now we need write "finite-stat machine"
