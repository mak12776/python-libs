# allocating memory as much as needed.
import logging
import secrets
import sys
from random import Random
from typing import Callable

import huffman

default_seed = 10
default_random = Random(default_seed)
randbytes: Callable[[int], bytes] = secrets.token_bytes

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

buffer_size = (2 ** 20) * 20  # 20 MB
with open('music_for_programming_49-julien_mier.mp3', 'rb') as infile:
    huffman.calculate_huffman_bits(infile.read(), 1)
