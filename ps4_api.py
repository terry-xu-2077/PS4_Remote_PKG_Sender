import json
from urllib.parse import quote
import requests


class PS4_API():
    server_url = ''
    ps4_url = ''
    error_code = {
        2157510677:'重复安装',
        2157510681:'任务不存在'
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
