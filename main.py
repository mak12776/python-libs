# allocating memory as much as needed.
import logging
import sys

import huffman

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

buffer_size = (2 ** 10) * 20  # 30 KB
huffman.calculate_huffman_bits(buffer_size, 30)
