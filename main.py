# allocating memory as much as needed.
import ast
from sys import exit, argv


def main(*args):
    node = ast.parse('10 + 30')


if __name__ == '__main__':
    exit(main(argv))
