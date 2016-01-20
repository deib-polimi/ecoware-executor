#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG)

import SimpleHTTPServer
import SocketServer
import json
from sys import argv

import topologyManager

class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path == '/':
      self.path = '/www/index.html'
    elif self.path.startswith('/api/vm'):
      vms = topologyManager.get_vms()
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      body = map(lambda x: x.__dict__, vms)
      self.wfile.write(json.dumps(body))
      return
    elif self.path.startswith('/api/'):
      return self.routing('get')
    else:
      self.path = '/www' + self.path
    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
    

  def do_POST(self):
    return self.routing('post')

if __name__ == '__main__':
  topologyManager.init()
  listen_ip = '0.0.0.0'
  if len(argv) >= 2:
    port = int(argv[1])
  else:
    port = 8000

  server = SocketServer.TCPServer((listen_ip, port), HttpHandler)
  print 'server has started at {0}:{1}'.format(listen_ip, port)
  server.serve_forever()