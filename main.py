# allocating memory as much as needed.
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

# huffman.calculate_bytes('music_for_programming_49-julien_mier.mp3', 2)
file_bits = 695619664
for bits_number in range(2, 20):
    print(f'{file_bits:>10} / {bits_number:2} = {file_bits / bits_number:.2f}')
