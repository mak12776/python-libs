# allocating memory as much as needed.

# with open('library/sio.py', mode='rb') as infile:
#     text = infile.read()
#
# node = ast.parse(text, mode='exec')
# read_write_functions = []
#
# for item in node.body:
#     if isinstance(item, ast.FunctionDef):
#         if re.match('(?:read|write)_(?!(?:file|file_name))', item.name):
#             read_write_functions.append(item)
# print(ast.dump(read_write_functions[0], indent=4))
