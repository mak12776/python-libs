import io
import typing

BinaryFile = typing.Union[typing.BinaryIO, io.RawIOBase]
TextFile = typing.Union[typing.TextIO, io.TextIOBase]


def get_file_size(file: BinaryFile):
    current = file.tell()
    file.seek(0, io.SEEK_END)
    size = file.tell()
    file.seek(current, io.SEEK_SET)
    return size


def read_file(file: BinaryFile, name: str) -> bytearray:
    size = get_file_size(file)
    buffer = bytearray(size)
    read_number = file.readinto(buffer)
    if read_number != size:
        raise EOFError(f'while reading: {name}')
    return buffer


def read_file_name(name: str):
    with open(name, 'rb', buffering=0) as infile:
        return read_file(infile, name)


def read_int(infile: io.RawIOBase, size: int, byteorder='big', signed=False):
    buffer = infile.read(size)
    if len(buffer) != size:
        signed = 'signed' if signed else 'unsigned'
        raise EOFError(f'while reading {size} byte {signed} int')
    return int.from_bytes(buffer, byteorder, signed=signed)


def write_int(outfile: io.RawIOBase, value: int, size: int, byteorder='big', signed=False):
    return outfile.write(value.to_bytes(size, byteorder, signed=signed))
