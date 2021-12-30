import socket
import threading
import time
import requests
import json
import csv
import os
from urllib.parse import quote
import sys

debug = False
# 生成资源文件目录访问路径
def get_resource_path(resource_path):
    if getattr(sys, 'frozen', False):  # 是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, resource_path)

def myPrint(*args):
    if debug: print(*args)

class myDict(dict):
    def __init__(self,lang):
        super(myDict, self).__init__(lang)
    def __getitem__(self, key):
        if self.get(key) != None or self.get(key) == '':
            return self.get(key)
        return key

class PS4_API():
    server_url = ''
    ps4_url = ''
    error_code = {
        2157510677:'Has been installed',
        2157510681:'Task does not exist'
    }

    @staticmethod
    def json_parse(text):
        try:
            info = json.loads(text,strict=False)
        except:
            info = eval(text)
        return info

    @staticmethod
    def request(url, data) -> dict:
        data = json.dumps(data)
        try:
            req = requests.post(PS4_API.ps4_url + url, data=data.encode('utf-8'), timeout=2)
            return PS4_API.json_parse(req.text.strip())
        except Exception as err:
            return {'PS4-Request-Error': err}

    @staticmethod
    def install_pkg(files):
        data = {
            "type":"direct",
            "packages":[]
        }
        if not isinstance(files, list):
            files = [files]
        for f in files:
            data['packages'].append(quote(PS4_API.server_url + '/' + quote(f)))
        return PS4_API.request('/api/install', data)

    @staticmethod
    def get_task_progress(task_id):
        return PS4_API.request('/api/get_task_progress', {"task_id": task_id})

    @staticmethod
    def unregister_task(task_id):
        return PS4_API.request('/api/unregister_task', {"task_id": task_id})

    @staticmethod
    def is_exists(title_id):
        return PS4_API.request('/api/is_exists', {"title_id": title_id})

    @staticmethod
    def is_readly():
        req = PS4_API.request('', {})
        try:
            if req["status"] == "fail":
                return True
            else:
                return False
        except:
            return False

    @staticmethod
    def set_ps4_url(ps4_ip):
        PS4_API.ps4_url = 'http://{}:12800'.format(ps4_ip)

class myJson(dict):
    def __init__(self, json_file=None, data=None):
        self.json_file = json_file
        json_data = {}
        if data != None:
            json_data = data
        if json_file != None:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    json_data = json.loads(f.read())
                    f.close()
        super(myJson, self).__init__(json_data)

    def save(self, file=None):
        if file != None:
            self.json_file = file
        with open(self.json_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self, indent=4,ensure_ascii=False))
            f.close()

    def __getitem__(self, key):
        return self.get(key)

def get_host_ip():
    addrs = socket.getaddrinfo(socket.gethostname(), None)
    ip_list = []
    for item in addrs:
        ip = item[-1]
        if len(ip) == 2:
            ip_list.append(ip[0])
    ip_list.reverse()
    return ip_list

def ps4_get_ip(host):
    scanner = ps4_ip_scanner(host,myPrint)
    scanner.start()
    scanner.join()
    return scanner.ps4_ip

def ps4_check_ip(ip):
    try:
        sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建套接字 ？
        sc.settimeout(0.2)
        result = sc.connect_ex((ip, 12800))
        sc.close()
        if result == 0:
            return True
        else:
            return False
    except:
        return False

class ps4_ip_scanner(threading.Thread):
    def __init__(self, host,callback):
        threading.Thread.__init__(self)
        self.host = host
        self.callback = callback
        self.finished = threading.Event()
        self.flag = True
        self.delay = 1

    def run(self):
        self.ps4_ip = self.__scanner()

    def __scanner(self):
        time.sleep(self.delay)
        myPrint('Scan:',self.host)
        net = self.host[:self.host.rfind('.') + 1] + '{}'
        self.callback('Scanning')
        for i in range(1, 256):
            if self.flag:
                ip = net.format(i)
                if ps4_check_ip(ip):
                    self.callback(ip)
                    myPrint('Scan finish:', ip)
                    return ip
            else:
                myPrint('Scan stop:',self.host)
                return ''
        self.callback('No find')
        return ''

    def stop(self):
        self.flag = False

def save_csv_data(data_list, fileName):
    with open(fileName, 'w', encoding='utf_8_sig',newline="") as f:
        csv_file = csv.writer(f)
        csv_file.writerows(data_list)
        f.close()

def read_csv_data(fileName):
    data_list = []
    try:
        with open(fileName, 'r', encoding='utf-8') as f:
            csv_file = csv.reader(f)
            for data in csv_file:
                data_list.append(data)
            f.close()
    except:
        pass
    return data_list

def format_size(size):
    a = size/1048576
    if len(str(a).split('.')[0]) <4:
        return '{} MB'.format(round(a,2))
    else:
        return '{} GB'.format(round(a/1024, 2))

def format_task_info(info,format_text):
    # '{} / {} (Remaining {} minute, Speed: {}MB/S)'
    sec = info.get('rest_sec')
    length = info.get('length')
    trans = info.get('transferred')
    m,s = divmod(sec,60)
    speed = round((length - trans) / 1024 / 1024 / sec,2)
    text = format_text.format(
        format_size(trans),
        format_size(length),
        m,s,
        speed
    )
    return text

# if __name__ == '__main__':
