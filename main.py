# allocating memory as much as needed.
import logging
import sys

import huffman

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

huffman.calculate_bytes(':10 KB', 8)
