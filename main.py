# allocating memory as much as needed.
from library.compression import SegmentedBuffer

buff = SegmentedBuffer()
read_buffer = (0b1110_0011_0111_1001).to_bytes(2, 'big', signed=False)

buff.scan_buffer(3, read_buffer)
buff.print_values()
