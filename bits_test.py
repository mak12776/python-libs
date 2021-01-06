def mask(width: int):
    return (1 << width) - 1


def _from_bytes(buffer: bytes):
    return int.from_bytes(buffer, byteorder='big', signed=False)

