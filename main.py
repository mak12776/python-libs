# allocating memory as much as needed.
from sys import exit, argv

import requests


def main(*args):
    requests.get('https://microcorruption.com')


if __name__ == '__main__':
    exit(main(argv))
