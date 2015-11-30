#!/usr/bin/python

import SimpleHTTPServer
import SocketServer
import json
import topologyManager
import traceback
from traceback import print_exc
from sys import argv
from translator import Translator

class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    body = ''
    if self.path == '/':
      self.path = '/www/index.html'
    elif self.path.startswith('/api/'):
       return self.routing('get')
    else:
      self.path = '/www' + self.path
    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
    

  def do_POST(self):
    return self.routing('post')

  def routing(self, method):

    body = ''
    try:
      if method == 'get':
        if self.path == '/api/topology':
          body = json.dumps(topologyManager.get_current())
      elif method == 'post':
        post_data_string = self.rfile.read(int(self.headers['Content-Length']))
        post_data = json.loads(post_data_string)

        translator = Translator()
        actions = translator.translate(post_data, topologyManager.get_current())
        if self.path == '/api/plan/translate':
          string_actions = map(lambda x: x.__str__(), actions)
          body = json.dumps(string_actions)
        elif self.path == '/api/plan/preview':
          preview = topologyManager.preview(actions)
          body = json.dumps(preview)
        elif self.path == '/api/plan/execute':
          new_topology = topologyManager.execute(actions)
          body = json.dumps(new_topology)
      self.send_response(200)
      self.send_header('Content-Type', 'application/json')
      self.end_headers()
      self.wfile.write(body)
    except:
      traceback.print_exc()
      self.send_response(500)
      self.end_headers()

if (__name__ == '__main__'):
  listen_ip = '0.0.0.0'
  if len(argv) >= 2:
    port = int(argv[1])
  else:
    port = 8000
  server = SocketServer.TCPServer((listen_ip, port), HttpHandler)
  print 'server has started at {0}:{1}'.format(listen_ip, port)
  server.serve_forever()
  