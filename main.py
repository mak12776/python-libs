# allocating memory as much as needed.
import logging
import sys
from random import Random
from typing import Callable

import huffman

default_seed = 10
default_random = Random(default_seed)
randbytes: Callable[[int], bytes] = lambda size: bytes(default_random.randrange(256) for _ in range(size))

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

buffer_size = (2 ** 20) * 20  # 20 MB
huffman.calculate_huffman_bits(buffer_size, 5, randbytes=randbytes)
