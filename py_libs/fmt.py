import sys


def printf(string: str, *args, **kwargs):
    print(string.format(*args, **kwargs))


def format_separator(title: str = None, char: str = '-', width: int = 80):
    if title is None:
        return char * width
    else:
        width -= len(title)
        left_width, right_width = width // 2, (width // 2) + (width % 2)
        return f'{left_width * char} {title} {right_width * char}'


def print_separator(title: str = None, char: str = '-', width: int = 80, end: str = '\n', file=sys.stdout):
    print(format_separator(title, char, width), end=end, file=file)
