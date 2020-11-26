from collections import deque
from itertools import chain
from sys import stdout
from typing import Iterable, Sequence

TableRow = Sequence[str]


class TableSetting:
    __slots__ = 'min_len', 'vertical_margin', 'row_algin', 'title_align', \
                'junction_sep', 'horizontal_sep', 'vertical_sep'

    def __init__(self,
                 min_len: int = 0, vertical_margin: int = 1, row_align: str = '<', title_align: str = '<',
                 junction_sep: str = '+', horizontal_sep: str = '-', vertical_sep: str = '|'):
        self.min_len = min_len
        self.vertical_margin = vertical_margin
        self.row_algin = row_align
        self.title_align = title_align

        self.junction_sep = junction_sep
        self.horizontal_sep = horizontal_sep
        self.vertical_sep = vertical_sep


class Table:
    __slots__ = 'settings', 'titles', 'rows'

    def __init__(self, settings: TableSetting = None, titles: TableRow = None, rows: Iterable[TableRow] = None):
        self.settings = settings or TableSetting()
        self.titles = list() if titles is None else list(titles)
        self.rows = deque() if rows is None else deque(rows)

    def set_titles(self, *args: str):
        self.titles = list(args)

    def add_row(self, *args: str):
        self.rows.append(args)

    def print_ext(self,
                  min_len: int = 0, vertical_margin: int = 0, row_align: str = '<', title_align: str = '<',
                  junction_sep: str = '+', horizontal_sep: str = '-', vertical_sep: str = '|',
                  file=stdout, flush: bool = True):

        if len(vertical_sep) != len(junction_sep):
            raise ValueError('length of vertical_sep & junction_sep is different.')

        max_columns_number = 0
        for row in chain([self.titles], self.rows):
            max_columns_number = max(max_columns_number, len(row))

        if max_columns_number == 0:
            return

        max_columns_len = [min_len] * max_columns_number
        for row in chain([self.titles], self.rows):
            for index, column in enumerate(row):
                if len(column) > max_columns_len[index]:
                    max_columns_len[index] = len(column)

        junction_sep = f'{horizontal_sep * vertical_margin}{junction_sep}{horizontal_sep * vertical_margin}'
        _vertical_width = vertical_margin * len(horizontal_sep)
        vertical_sep = f'{" " * _vertical_width}{vertical_sep}{" " * _vertical_width}'

        title_line = vertical_sep.join(f'{{:{title_align}{_len}}}' for _len in max_columns_len)
        horizontal_line = junction_sep.join(
            horizontal_sep * max_columns_len[index] for index in range(max_columns_number))
        row_line = vertical_sep.join(f'{{:{row_align}{_len}}}' for _len in max_columns_len)

        def _print(string):
            print(string, file=file, flush=flush)

        _print(title_line.format(*self.titles))
        _print(horizontal_line)
        for row in self.rows:
            _print(row_line.format(*row))

    def print(self, setting: TableSetting = None, file=stdout, flush: bool = True):
        setting = setting or self.settings
        self.print_ext(
            min_len=setting.min_len, vertical_margin=setting.vertical_margin,
            row_align=setting.row_algin, title_align=setting.title_align,

            junction_sep=setting.junction_sep,
            horizontal_sep=setting.horizontal_sep,
            vertical_sep=setting.vertical_sep,

            file=file, flush=flush)
