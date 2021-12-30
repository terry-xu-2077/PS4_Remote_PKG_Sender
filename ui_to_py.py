import base64

py_file = '''import base64
ui_data = base64.b64decode('{}')
ui_icon = base64.b64decode('{}')
'''

with open('./res/appUI.ui','rb') as f:
    ui_data = f.read()
    f.close()

with open('./res/favicon.png','rb') as f:
    ui_icon = f.read()
    f.close()

with open('ui_res_base64.py', 'wt') as f:
    base64_data = base64.b64encode(ui_data).decode()
    base64_icon = base64.b64encode(ui_icon).decode()
    f.write(py_file.format(base64_data,base64_icon))
    f.close()