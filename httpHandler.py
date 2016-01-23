#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG)

import SimpleHTTPServer
import SocketServer
import json
import time
from sys import argv

import topologyManager
from vm import Vm

class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path == '/':
      self.path = '/www/index.html'
    elif self.path.startswith('/api/vm'):
      vms = topologyManager.get_vms()
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      body = sorted(map(lambda x: x.__dict__, vms), key=id)
      self.wfile.write(json.dumps(body))
      return
    else:
      self.path = '/www' + self.path
    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

  def do_POST(self):
    start = time.time()
    post_data_string = self.rfile.read(int(self.headers['Content-Length']))
    post_data = json.loads(post_data_string)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    vm = topologyManager.create_vm(post_data['name'], post_data['cpu_cores'], post_data['mem_units'])
    response = post_data
    response['id'] = vm.id
    response['docker_port'] = vm.docker_port
    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.wfile.write(json.dumps(response))
    return

  def do_DELETE(self):
    start = time.time()
    args = self.path.split('/')
    id = int(args[-1])
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    topologyManager.delete_vm(id)
    response = {
      'time': '{0:.2f}'.format(time.time() - start)
    }
    self.wfile.write(json.dumps(response))
    return

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