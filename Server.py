import threading
import time
import requests
from twisted.internet import reactor, endpoints
from twisted.web import static, server

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
