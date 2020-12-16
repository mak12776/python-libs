# allocating memory as much as needed.
import re
from os import path

folder_contents = [
    'dump.txt',
    'state.txt',
    'dis.txt'
]

root_folder = r"D:\Codes\micro-test\Tutorial 10P"

file_path = path.join(root_folder, "dump.txt")

with open(file_path, "rb") as file:
    buffer = file.read()

lines = buffer.splitlines()
addr_values = []
for index in range(len(lines)):
    m = re.match(b'([0-9a-f]{4}): {3}(\\*|(?:[0-9a-f]{4} ){8})', lines[index])
    if m is None:
        print(f'ERROR: {lines[index]!r} => didn\'t match pattern')
    first = int(m.group(1), 16)
    if m.group(2) == b'*':
        second = 'zero'
    else:
        second = []
        for item in filter(lambda s: s, m.group(2).split(b' ')):
            second.append(item[:2])
            second.append(item[2:])
        second = tuple(map(lambda s: int(s, 16), second))
    addr_values.append((int(m.group(1), 16), second))

hex_digits = '[0-9a-f]{4}'

state_lines = [
    "pc  0000  sp  0000  sr  0000  cg  0000".replace('0000', hex_digits),
    "r04 0000  r05 0000  r06 0000  r07 0000".replace('0000', hex_digits),
    r"08 0000  r09 0000  r10 0000  r11 0000".replace('0000', hex_digits),
    "r12 0000  r13 0000  r14 0000  r15 0000".replace('0000', hex_digits),
]

file_path = path.join(root_folder, "state.txt")

with open(file_path, "rb") as file:
    buffer = file.read()

print(buffer.splitlines())
