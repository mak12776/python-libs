# allocating memory as much as needed.
import logging
import sys

from PIL import ImageGrab

logging.basicConfig(stream=sys.stdout, format='%(levelname)s: %(message)s', level=logging.DEBUG)

screen = ImageGrab.grab()
print('size:', screen.size)
print('', screen.category)
