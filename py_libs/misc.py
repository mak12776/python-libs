import string
from random import choice


def generate_password(*, chars=None, width=32):
    if chars is None:
        chars = string.ascii_letters + string.digits + '@#$&?!~'
    return ''.join(choice(chars) for i in range(width))