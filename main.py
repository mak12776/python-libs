import py_libs as libs

with open('main.py', 'rb', buffering=0) as file:
    buffer = libs.read_file(file)

print(buffer)