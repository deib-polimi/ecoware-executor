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
    elif self.path.startswith('/docker'):
      args = self.path.split('/')
      self.path = '/www/docker.html'
    elif self.path.startswith('/api/vm'):
      vms = topologyManager.get_vms()
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      response = sorted(map(lambda x: x.dict(), vms), key=id)
      self.wfile.write(json.dumps(response))
      return
    else:
      self.path = '/www' + self.path
    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

  def do_POST(self):
    start = time.time()
    args = self.path.split('/')
    if args[-1] == 'stop':
      if args[-3] == 'container':
        container_id = int(args[-2])
        topologyManager.stop_container(container_id)
      else:
        id = int(args[-2])
        topologyManager.stop_vm(id)
      response = {}
    elif args[-1] == 'start':
      if args[-3] == 'container':
        container_id = int(args[-2])
        topologyManager.start_container(container_id)
      else:
        id = int(args[-2])
        topologyManager.start_vm(id)
      response = {}
    elif args[-1] == 'container':
      post_data_string = self.rfile.read(int(self.headers['Content-Length']))
      post_data = json.loads(post_data_string)
      vm_id = int(args[-2])
      container = topologyManager.create_container(vm_id, post_data['name'], post_data['cpuset'], post_data['mem_units'])
      response = post_data
      response['mem'] = container.mem
      response['id'] = container.id
    else:
      post_data_string = self.rfile.read(int(self.headers['Content-Length']))
      post_data = json.loads(post_data_string)
      vm = topologyManager.create_vm(post_data['name'], post_data['cpu_cores'], post_data['mem_units'])
      response = post_data
      response['mem'] = vm.mem
      response['id'] = vm.id
      response['docker_port'] = vm.docker_port
    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(response))

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