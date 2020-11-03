import re
import sys

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


def run_main(func):
    sys.exit(func(sys.argv) or 0)


def get_program_name(default='main'):
    return sys.argv[0] if sys.argv else default


program_name = get_program_name()


def printf(fmt: str, *args, **kwargs):
    print(fmt.format(*args), **kwargs)


def printf_error(fmt: str, *args, **kwargs):
    printf(f'error: {fmt.format(*args)}', **kwargs)


def quoted(string: str, symbol: str = '"'):
    return symbol + string.replace(symbol, '\\' + symbol) + symbol


def single_quoted(string: str, symbol: str = '\''):
    return symbol + string.replace(symbol, '\\' + symbol) + symbol
