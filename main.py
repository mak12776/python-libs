# allocating memory as much as needed.
from py_libs.math import ceil_module
from py_libs.misc import generate_password
from py_libs.table import TableSetting, Table


class Info:
    __slots__ = ('buffer_bits', 'buffer_size',
                 'data_bits', 'data_size',
                 'remaining_bits', 'remaining_size',
                 'possible_data_number', 'total_data_number')


def get_bytes_per_bits(bits: int):
    return ceil_module(bits, 8)


def compute_info(buffer_bits: int, data_bits: int):
    info = Info()

    info.buffer_bits = buffer_bits
    info.buffer_size = get_bytes_per_bits(buffer_bits)

    info.data_bits = data_bits
    info.data_size = get_bytes_per_bits(data_bits)

    info.remaining_bits = buffer_bits % data_bits
    info.remaining_size = get_bytes_per_bits(info.remaining_bits)

    info.total_data_number = buffer_bits // data_bits
    info.possible_data_number = 2 ** data_bits

    # worst case
    # maximum data count = total_data_number
    # minimum data count = 0
    # maximum data difference = 0

    # best case
    # minimum data count = ceil_module(total_data_number, possible_data_number)
    # maximum data count = floor_module(total_data_number, possible_data_number)
    # maximum data difference = 1

    return info


def print_info(info: Info, table_settings: TableSetting = None):
    table_settings = table_settings or TableSetting(vertical_margin=1, title_align='<', row_align='>')
    table = Table(table_settings)

    table.set_titles('buffer bits', 'buffer size',
                     'data bits', 'remaining bits',
                     'possible data number', 'total data number')

    table.add_row(*map(str, [info.buffer_bits, info.buffer_size,
                             info.data_bits, info.remaining_bits,
                             info.possible_data_number, info.total_data_number]))
    table.print()


print(generate_password())
