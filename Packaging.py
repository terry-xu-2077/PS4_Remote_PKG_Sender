import os

if __name__ == '__main__':
    '''
    -F, --onefile Py代码只有一个文件
    -D, --onedir Py代码放在一个目录中（默认是这个）
    -K, --tk 包含TCL/TK
    -d, --debug 生成debug模式的exe文件
    -w, --windowed, --noconsole 窗体exe文件(Windows Only)
    -c, --nowindowed, --console 控制台exe文件(Windows Only)
    -o DIR, --out=DIR 设置spec文件输出的目录，默认在PyInstaller同目录
    --icon=<FILE.ICO> 加入图标（Windows Only）
    -v FILE, --version=FILE 加入版本信息文件
    --upx-dir, 压缩可执行程序
    
    pipenv shell 进入虚拟环境
    pipenv run python 进入虚拟环境中的python
    
    
    '''
    from PyInstaller.__main__ import run
    opts = ['PS4-PKG-Sender.py', '-F', '-w', '--icon=app.ico']
    run(['PS4-PKG-Sender.spec'])
