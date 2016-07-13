# HTTP Server for tests.

import os
import sys
import json
import cPickle
import BaseHTTPServer
import SocketServer
import urlparse

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    homedir = ''
    handlers = {}
    known_content = {   '.htm':   'text/html',   '.html':  'text/html', 
                        '.css':   'text/css',    '.js':    'text/javascript',
                        '.jpg': 'image/jpeg',    '.png': 'image/png'}

    def _set_headers(self, content_type):
        self.send_response(200)
        self.send_header('Content-type', ''+content_type)
        self.end_headers()

    def do_HEAD(self):
        self._set_headers('html')

    def do_GET(self):
        path = urlparse.urlparse(self.path).path
        fname, fext = os.path.splitext(path)
        if fext in MyHandler.known_content:
            self._set_headers(MyHandler.known_content[fext])
            try:
                fullname = os.path.join(os.path.join(MyHandler.homedir, os.path.basename(os.path.dirname(path))), os.path.basename(path))
                with open(unicode(fullname), "rb") as f:
                    self.wfile.write(f.read())
            except:
                pass
        else:
            print 'Unknown request:', path

    def do_POST(self):
        action = urlparse.urlparse(self.path).path
        size = int(self.headers['Content-Length'])
        if size > 0:
            content = json.loads(self.rfile.read(size))
        else:
            content = ''
        self.send_response(200)
        self.end_headers()
        if action in MyHandler.handlers:
            self.wfile.write(MyHandler.handlers[action](content))
        else:
            self.wfile.write('')

class MyServer(object):
    def __init__(self, homedir, port):
        MyHandler.homedir = homedir
        self._port = port
        self._httpd = SocketServer.TCPServer(("", port), MyHandler)

    def run(self):
        self._httpd.serve_forever()

    def set_handler(self, action, handler):
        MyHandler.handlers['/'+action] = handler



class Images(object):
    def __init__(self, path):
        self._path = path
        self._masks = {}
        self._filename = os.path.join(path, 'masks.pkl')
        if os.path.isfile(self._filename):
            with open(self._filename, 'rb') as f:
                self._masks = cPickle.load(f)

        self._images = []
        self._next_index = 0
        self._scan()


    def set(self, image_name, points):
        self._masks[image_name] = points
        with open(self._filename, 'wb') as f:
            cPickle.dump(self._masks, f)

    def next(self):
        while self._next_index < len(self._images):
            curr_name = self._images[self._next_index]
            if curr_name not in self._masks:
                return curr_name
            self._next_index += 1
        return ''

    def _scan(self):
        exts = ['.jpg', '.jpeg', '.png']
        for root, dirs, files in os.walk(self._path):
            for filename in files:
                fname, fext = os.path.splitext(filename)
                if fext in exts:
                    self._images.append(os.path.relpath(os.path.join(root, filename), self._path))
        self._next_index = 0
        


def main():
    root = os.getcwd()
    port = 8123 if len(sys.argv) == 1 else int(sys.argv[1])


    images = Images(root)

    server = MyServer(root, port)
    server.set_handler('next', lambda x: images.next())
    server.set_handler('set_mask', lambda info: images.set(info['name'], info['points']))


    print 'running....'
    print '\t Root: ', root
    print '\t Port: ', port
    server.run()


if __name__ == '__main__':
    main()
