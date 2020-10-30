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


def run_main(func):
    sys.exit(func(sys.argv) or 0)


def get_program_name(default='main'):
    return sys.argv[0] if sys.argv else default


program_name = get_program_name()


def printf(fmt: str, *args, **kwargs):
    print(fmt.format(*args), **kwargs)


def printf_error(fmt: str, *args, **kwargs):
    printf(f'error: {fmt.format(*args)}', **kwargs)


def print_separator(title: str = None, char: str = '-', width: int = 80, end: str = '\n'):
    if title is None:
        print(char * width, end=end)
    else:
        width -= len(title) + 2
        left_width, right_width = width // 2, (width // 2) + (width % 2)
        print((left_width * char) + f' {title} ' + (right_width * char), end=end)


def quoted(string: str, symbol: str = '"'):
    return symbol + string.replace(symbol, '\\' + symbol) + symbol


def single_quoted(string: str, symbol: str = '\''):
    return symbol + string.replace(symbol, '\\' + symbol) + symbol
