from random import choice
from string import ascii_letters, digits

from library.utils import chr_range

_symbols = set(chr_range(' ', '~')) - set(ascii_letters + digits)


def generate_password(*, chars=None, width=32, append_letters=False, append_digits=False, append_symbols=False):
    if chars is None:
        chars = set(ascii_letters + digits + '@#_#!')
    if append_letters:
        chars.update(ascii_letters)
    if append_digits:
        chars.update(digits)
    if append_symbols:
        chars.update(_symbols)
    return ''.join(choice(list(chars)) for i in range(width))


def print_password(*, chars=None, width=32):
    print(generate_password(chars=chars, width=width))
