#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG)

import SimpleHTTPServer
import SocketServer
import json
import time
import sys
import traceback
from sys import argv

import topologyManager
import simple_executor
import simple_topology
import monolitic_topology
from vm import Vm

class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    start = time.time()
    if self.path == '/':
      self.path = '/www/index.html'
    elif self.path.startswith('/docker'):
      self.path = '/www/docker.html'
    elif self.path.startswith('/vm'):
      self.path = '/www/vm.html'
    elif self.path.startswith('/monolitic'):
      self.path = '/www/monolitic.html'
    elif self.path.startswith('/api/vm'):
      vms = topologyManager.get_vms()
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      response = sorted(map(lambda x: x.dict(), vms), key=id)
      self.wfile.write(json.dumps(response))
      return
    elif self.path.startswith('/api/topology'):
      topology = topologyManager.get_topology()
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(topology))
      return
    elif self.path.startswith('/api/simple/allocation'):
      try:
        response = simple_topology.get_allocation()
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)
      response['time'] = '{0:.2f}'.format(time.time() - start)
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(response))
      print 'response time {0:.2f}'.format(time.time() - start)
      return
    elif self.path.startswith('/api/monolitic/allocation'):
      try:
        response = monolitic_topology.get_allocation()
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)
      response['time'] = '{0:.2f}'.format(time.time() - start)
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(response))
      print 'response time {0:.2f}'.format(time.time() - start)
      return
    elif self.path.startswith('/api/allocation'):
      topology = topologyManager.get_allocation()
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(topology))
      return
    elif self.path.startswith('/api/simple/topology'):
      topology = simple_topology.get_topology()
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(topology))
      return
    elif self.path.startswith('/api/monolitic/topology'):
      topology = monolitic_topology.get_topology()
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(topology))
      return
    else:
      self.path = '/www' + self.path
    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

  def do_POST(self):
    start = time.time()
    args = self.path.split('/')
    if self.path.startswith('/api/simple/executor'):
      try:
        post_data_string = self.rfile.read(int(self.headers['Content-Length']))
        post_data = json.loads(post_data_string)
        post_data.pop("time", None)
        simple_topology.execute(post_data)
        new_allocation = simple_topology.get_allocation()
        response = new_allocation      
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)

    elif args[-1] == 'stop':
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
      container = topologyManager.run_container(vm_id, post_data['name'], post_data['cpuset'], post_data['mem_units'])
      response = post_data
      response['mem'] = container.mem
      response['id'] = container.id
      response['vm'] = container.vm.dict_flat()
    elif self.path.startswith('/api/simple/topology'):
      post_data_string = self.rfile.read(int(self.headers['Content-Length']))
      post_data = json.loads(post_data_string)
      simple_topology.set_topology(post_data)
      response = {}
    elif self.path.startswith('/api/monolitic/topology'):
      post_data_string = self.rfile.read(int(self.headers['Content-Length']))
      post_data = json.loads(post_data_string)
      monolitic_topology.set_topology(post_data)
      response = {}
    elif args[-1] == 'topology':
      post_data = json.loads(post_data_string)
      topologyManager.set_topology(post_data)
      response = {}
    elif args[-1] == 'plan':
      post_data_string = self.rfile.read(int(self.headers['Content-Length']))
      post_data = json.loads(post_data_string)
      topologyManager.execute(post_data)
      response = {}
    else:
      post_data_string = self.rfile.read(int(self.headers['Content-Length']))
      post_data = json.loads(post_data_string)
      host = post_data.get('host')
      vm = topologyManager.create_vm(post_data['name'], post_data['cpu_cores'], post_data['mem_units'], host)
      response = post_data
      response['mem'] = vm.mem
      response['id'] = vm.id
      response['docker_port'] = vm.docker_port
    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    print response
    self.wfile.write(json.dumps(response))

  def do_DELETE(self):
    start = time.time()
    args = self.path.split('/')
    id = int(args[-1])
    if args[-2] == 'container':
      topologyManager.delete_container(id)
    else:
      topologyManager.delete_vm(id)  

    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    
    response = {
      'time': '{0:.2f}'.format(time.time() - start)
    }
    self.wfile.write(json.dumps(response))
    return

  def do_PUT(self):
    start = time.time()
    args = self.path.split('/')
    container_id = int(args[-1])
    put_data_string = self.rfile.read(int(self.headers['Content-Length']))
    put_data = json.loads(put_data_string)
    cpuset = put_data['cpuset']
    mem = put_data['mem_units']
    container = topologyManager.update_container(container_id, cpuset, mem)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    
    response = {
      'id': container.id,
      'cpuset': container.cpuset,
      'mem_units': container.mem_units,
      'mem': container.mem,
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