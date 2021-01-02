# allocating memory as much as needed.
from library.compression import _BitReader

ba = bytearray(b'\x34\x35\x37')
bits_reader = _BitReader(ba, 4)

print(bits_reader.read_bits())
print(bits_reader.read_bits())

print(bits_reader.read_bits())
print(bits_reader.read_bits())

print(bits_reader.read_bits())
print(bits_reader.read_bits())
