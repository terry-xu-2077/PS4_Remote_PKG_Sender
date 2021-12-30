import json
import subprocess
import threading
import time
import os
import requests
from twisted.web import resource
from twisted.internet import reactor, endpoints
from twisted.web import static, server
from MyPage import get_index_html

class PkgServer():
    __server_td = None
    __devNull = open(os.devnull,'w')
    def __init__(self,port,RES_PATH):
        self.port = port
        self.running = False
        self.__nodejs = RES_PATH + '/node.exe'
        self.__server_js = RES_PATH + '/SERVER.JS'

    def start(self):
        self.__server_td = threading.Thread(target=self.__server)
        self.__server_td.start()
        self.running = self.__server_td.is_alive()
        return self.running

    def reset_port(self,newport):
        self.port = newport
        if self.running:
            self.stop()
        self.start()

    def is_ready(self):
        i = 0
        while True:
            if i == 2:
                return False
            req = requests.get('http://127.0.0.1:{}/ready'.format(self.port))
            print(req.text)
            if req.text == 'SERVE:OK':
                return True
            i += 0.2
            time.sleep(0.2)

    def stop(self):
        if self.running:
            self.__server_process.kill()
            self.running = self.__server_td.is_alive()
        return self.running

    def exist(self):
        if self.__server_td != None:
            return self.__server_td.is_alive()
        else:
            return False

    def update(self,treedata):
        try:
            pkgJson = json.dumps({'infolist':treedata}).encode('utf-8')
            req = requests.post('http://127.0.0.1:{}/pkglist'.format(self.port),data=pkgJson)
            if req.text == 'UPDATE:list':
                return True
            else:
                return False
        except:
            return False

    def send(self,info):
        try:
            pkgJson = json.dumps({'info':info}).encode('utf-8')
            req = requests.post('http://127.0.0.1:{}/pkginfo'.format(self.port),data=pkgJson)
            print(req.text)
            if req.text == 'UPDATE:OK':
                return True
            else:
                return False
        except:
            return False

    def __server(self):
        self.__server_process = subprocess.Popen(
            [self.__nodejs,self.__server_js, '-p', str(self.port)],
            stdout=subprocess.PIPE,
        )

class FilesServer():
    fileType = 'application/octet-stream'
    def __init__(self,port):
        super(FilesServer, self).__init__()
        self.port = port
        self.__Files = static.File('')
        self.__endpoint = None
        self.__td_server = None
        self.running = False

    def update(self,files):
        self.clear_files()
        self.__Files.tree_data = files
        try:
            for f in files:
                self.__Files.putChild(f[5].encode('utf-8'), static.File(f[-1], self.fileType))
            return True
        except Exception as e:
            print(e)
            return False

    def reset_port(self,newport):
        self.port = newport
        if self.running:
            self.stop()
        self.start()

    def is_ready(self):
        i = 0
        while True:
            if i == 2:
                return False
            req = requests.get('http://127.0.0.1:{}'.format(self.port))
            if req.text:
                return True
            i += 0.2
            time.sleep(0.2)

    def clear_files(self):
        self.__Files.children.clear()

    def remove_files(self,files):
        if not isinstance(files, list):
            files = [files]
        for f in files:
            self.__Files.children.pop(f.encode('utf-8'))

    def stop(self):
        try:
            reactor.stop()
            self.__td_server.join()
            self.running = False
        except:
            pass

    def start(self):
        try:
            self.__td_server = threading.Thread(target=self.__run)
            self.__td_server.start()
            self.running = True
        except Exception as e:
            print(e)
            self.running = False

    def exist(self):
        if self.__td_server != None:
            return self.__td_server.is_alive()
        else:
            return False

    def __run(self):
        self.endpoint = endpoints.TCP4ServerEndpoint(reactor, int(self.port))
        self.endpoint.listen(server.Site(self.__Files))
        reactor.run(installSignalHandlers=0)


if __name__ == '__main__':
    pass