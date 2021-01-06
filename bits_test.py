def mask(width: int):
    return (1 << width) - 1


def _from_bytes(buffer: bytes):
    return int.from_bytes(buffer, byteorder='big', signed=False)


def read_bits(buffer: bytes, data_bits: int):
    index = 0
    while index < len(buffer):
        read_value = buffer[index:index + _BITS_IO_SIZE]
        index += _BITS_IO_SIZE
