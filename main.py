# allocating memory as much as needed.
import logging
import os
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

print(f'Hello {-100:+}')

os.mkdir('.data')
