from collections import deque
from itertools import chain
from sys import stdout
from typing import Iterable, Sequence

TableRow = Sequence[str]


class TableSetting:
    __slots__ = 'min_len', 'empty_len', 'row_algin', 'title_align', \
                'junction_sep', 'horizontal_sep', 'vertical_sep'

    def __init__(self,
                 min_len: int = 0, empty_len: int = 1, row_align: str = '<', title_align: str = '<',
                 junction_sep: str = '+', horizontal_sep: str = '-', vertical_sep: str = '|'):
        self.min_len = min_len
        self.empty_len = empty_len
        self.row_algin = row_align
        self.title_align = title_align

        self.junction_sep = junction_sep
        self.horizontal_sep = horizontal_sep
        self.vertical_sep = vertical_sep


class Table:
    __slots__ = 'columns_number', 'titles', 'rows'

    def __init__(self, columns_number: int, titles: TableRow = None, rows: Iterable[TableRow] = None):
        self.columns_number = columns_number
        self.titles = list() if titles is None else list(titles)
        if rows is not None:
            for index, row in enumerate(rows):
                if len(row) != self.columns_number:
                    raise ValueError(f'invalid number of columns in row {index}')
            self.rows = deque(rows)
        else:
            self.rows = deque()

    def set_titles(self, *args: str):
        if len(args) != self.columns_number:
            raise ValueError(f'invalid number of columns: {args}')
        self.titles = list(args)

    def add_row(self, *args: str):
        if len(args) != self.columns_number:
            raise ValueError(f'invalid number of columns: {args}')
        self.rows.append(args)

    def print_ext(self,
                  min_len: int = 0, empty_len: int = 1, row_align: str = '<', title_align: str = '<',
                  junction_sep: str = '+', horizontal_sep: str = '-', vertical_sep: str = '|',
                  file=stdout, flush: bool = True):

        if len(vertical_sep) != len(junction_sep):
            raise ValueError('length of vertical_sep & junction_sep is different.')

        max_columns_len = [min_len] * self.columns_number
        for row in chain([self.titles], self.rows):
            for index, column in enumerate(row):
                if len(column) > max_columns_len[index]:
                    max_columns_len[index] = len(column)
        for index in range(self.columns_number):
            max_columns_len[index] += empty_len

        horizontal_line = junction_sep.join(
            horizontal_sep * max_columns_len[index] for index in range(self.columns_number)
        )
        title_line = vertical_sep.join(f'{{:{title_align}{_len}}}' for _len in max_columns_len)
        row_line = vertical_sep.join(f'{{:{row_align}{_len}}}' for _len in max_columns_len)

        def _print(string):
            print(string, file=file, flush=flush)

        _print(title_line.format(*self.titles))
        _print(horizontal_line)
        for row in self.rows:
            _print(row_line.format(*row))

    def print(self, setting: TableSetting = None, file=stdout, flush: bool = True):
        setting = setting or TableSetting()
        self.print_ext(
            min_len=setting.min_len, empty_len=setting.empty_len,
            row_align=setting.row_algin, title_align=setting.title_align,

            junction_sep=setting.junction_sep,
            horizontal_sep=setting.horizontal_sep,
            vertical_sep=setting.vertical_sep,

            file=file, flush=flush)
