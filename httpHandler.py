#!/usr/bin/python

import SimpleHTTPServer
import SocketServer
import json
from sys import argv
from translator import Translator
from topologyManager import TopologyManager

class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path == '/':
      self.path = '/www/index.html'
    else:
      self.path = '/www' + self.path

    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

  def do_POST(self):
    self.data_string = self.rfile.read(int(self.headers['Content-Length']))

    self.send_response(200)
    self.end_headers()

    data = json.loads(self.data_string)
    print data
    translator = Translator()
    topologyManager = TopologyManager()
    actions = translator.translate(data, topologyManager.get_current())
    
    self.wfile.write(json.dumps(actions))
    return


if (__name__ == '__main__'):
  listen_ip = '0.0.0.0'
  if len(argv) >= 2:
    port = int(argv[1])
  else:
    port = 8000
  server = SocketServer.TCPServer((listen_ip, port), HttpHandler)
  print 'server has started at {0}:{1}'.format(listen_ip, port)
  server.serve_forever()
  