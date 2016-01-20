#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG)

import SimpleHTTPServer
import SocketServer
import json
import topologyManager
import traceback

from collections import OrderedDict
from traceback import print_exc
from sys import argv


from translator import Translator
import executor


class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    body = ''
    if self.path == '/':
      self.path = '/www/index.html'
    elif self.path.startswith('/vm'):

    elif self.path.startswith('/api/'):
       return self.routing('get')
    else:
      self.path = '/www' + self.path
    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
    

  def do_POST(self):
    return self.routing('post')

if __name__ == '__main__':
  listen_ip = '0.0.0.0'
  if len(argv) >= 2:
    port = int(argv[1])
  else:
    port = 8000
  server = SocketServer.TCPServer((listen_ip, port), HttpHandler)
  print 'server has started at {0}:{1}'.format(listen_ip, port)
  server.serve_forever()