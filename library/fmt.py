import sys


def quoted(string: str, symbol: str = '"'):
    string = string.replace(symbol, f'\\{symbol}')
    return f'{symbol}{string}{symbol}'


def single_quoted(string: str):
    return quoted(string, symbol="'")


def printf(string: str, *args, **kwargs):
    print(string.format(*args, **kwargs))


def printf_error(fmt: str, *args, **kwargs):
    printf(f'error: {fmt.format(*args)}', **kwargs)


def format_separator(title: str = None, char: str = '-', width: int = 80):
    if title is None:
        return char * width
    else:
        width -= len(title)
        left_width, right_width = width // 2, (width // 2) + (width % 2)
        return f'{left_width * char} {title} {right_width * char}'


def print_separator(title: str = None, char: str = '-', width: int = 80, end: str = '\n', file=sys.stdout):
    print(format_separator(title, char, width), end=end, file=file)
