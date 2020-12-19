# allocating memory as much as needed.
import marshal
from enum import unique, IntFlag
from io import BytesIO, SEEK_SET
from sys import exit, argv

from library import io

cache_folder = 'cache'


def funny_function(a, b, c, d=10, *args, hello=10):
    """
    it's some funny function
    :param func:
    :return:
    """
    a_new = 600

    def a_new_funny_function(some_num):
        if cache_folder == 10:
            return None

    return a_new_funny_function


@unique
class CodeFlags(IntFlag):
    ARBITRARY_NUMBER_OF_POSITIONAL_ARGUMENTS_FLAG = 0x04
    ARBITRARY_KEYWORD_ARGUMENTS_FLAG = 0x08
    GENERATOR_FUNCTION_FLAG = 0x02
    FUTURE_DIVISION_FLAG = 0x2000


def dump_func_info(func):
    code_object = func.__code__
    print('code object:', code_object)
    print('-' * 20)
    print('function name:', code_object.co_name)
    print('positional-only arguments + default values argument count:', code_object.co_argcount)
    print('positional-only arguments count:', code_object.co_posonlyargcount)
    print('keyword-only arguments count:', code_object.co_kwonlyargcount)
    print('number of local variables:', code_object.co_nlocals)
    print('names of local variables:', code_object.co_varnames)
    print('names of free variables:', code_object.co_freevars)
    print('names of local variables that are referenced by nested function:', code_object.co_cellvars)
    print('sequence of byte code instructions:', code_object.co_code)
    print('literals used by bytecode:', code_object.co_consts)
    print('names used by bytecode:', code_object.co_names)
    print('code file name:', code_object.co_filename)
    print('first line number of function:', code_object.co_firstlineno)
    print('mapping from bytecode offsets to line numbers:', code_object.co_lnotab)
    print('required stack size:', code_object.co_stacksize)
    print('flags:', CodeFlags(code_object.co_flags))
    print('-' * 10)
    func = funny_function
    # ---
    func_dump = marshal.dumps(func.__code__, 4)
    func_copy = marshal.loads(func_dump)
    print('marshal dumps:', func_dump)
    print('marshal loads:', func_copy)
    print('function code:', func.__code__)
    print('hash:', hash(func_dump))
    print('func_copy hash:')
    print('func_copy == func:', func_copy == func)


def slow_bits_count(num: int):
    if num == 0:
        return 1
    if num < 0:
        return len(bin(num)) - 3
    return len(bin(num)) - 2


def main(*args):
    for num in range(-0xFFFF, 0xFFFF + 1):
        buffer = BytesIO()
        io.write_big_int(buffer, num)
        buffer.seek(0, SEEK_SET)
        num_copy = io.read_big_int(buffer)
        if num != num_copy:
            buffer_hex = ''.join(hex(value) for value in buffer.getvalue())
            print('buffer:', buffer_hex)
            print(f'value error: {num}, {bin(num)} != {num_copy}')
            return
    print('all success.')


if __name__ == '__main__':
    exit(main(argv))
