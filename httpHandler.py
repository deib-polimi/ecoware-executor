#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG)

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import SimpleHTTPServer
import threading
import json
import time
import sys
import traceback
from sys import argv

import topologyManager
import simple_executor
import simple_topology
import monolitic_topology
import docker
from vm import Vm

class HttpHandler(BaseHTTPRequestHandler):
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
    elif self.path.startswith('/api/monolitic/executor'):
      try:
        post_data_string = self.rfile.read(int(self.headers['Content-Length']))
        post_data = json.loads(post_data_string)
        post_data.pop("time", None)
        new_allocation = monolitic_topology.execute(post_data)
        response = new_allocation
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)
    elif self.path.startswith('/api/monolitic/translator'):
      try:
        post_data_string = self.rfile.read(int(self.headers['Content-Length']))
        post_data = json.loads(post_data_string)
        post_data.pop("time", None)
        actions = monolitic_topology.translate(post_data)
        string_actions = map(lambda x: x.__str__(), actions)
        response = {
          'actions': string_actions
        }
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)
    elif self.path.startswith('/api/docker/stop'):
      try:
        post_data_string = self.rfile.read(int(self.headers['Content-Length']))
        post_data = json.loads(post_data_string)
        container_name = post_data['name']
        docker.stop_container(container_name)
        response = {}
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)
    elif self.path.startswith('/api/docker/run'):
      try:
        post_data_string = self.rfile.read(int(self.headers['Content-Length']))
        post_data = json.loads(post_data_string)
        container_name = post_data['name']
        cpuset = post_data['cpuset']
        mem_units = post_data['mem_units']
        info = monolitic_topology.get_topology()['app']['tiers'][container_name]
        docker.run_container(container_name, cpuset, mem_units, info)
        response = {}
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)
    elif self.path.startswith('/api/docker/start'):
      try:
        post_data_string = self.rfile.read(int(self.headers['Content-Length']))
        post_data = json.loads(post_data_string)
        container_name = post_data['name']
        docker.start_container(container_name)
        response = {}
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)
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
    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    print response
    self.wfile.write(json.dumps(response))

  def do_DELETE(self):
    start = time.time()
    if self.path.startswith('/api/docker'):
      try:
        args = self.path.split('/')
        container_name = args[-1]
        docker.delete_container(container_name)
        response = {}
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)

    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(response))

  def do_PUT(self):
    start = time.time()
    if self.path.startswith('/api/docker'):
      try:
        args = self.path.split('/')
        container_name = args[-1]
        put_data_string = self.rfile.read(int(self.headers['Content-Length']))
        put_data = json.loads(put_data_string)
        cpuset = put_data['cpuset']
        mem_units = put_data['mem_units']
        docker.update_container(container_name, cpuset, mem_units)
        response = {
          'name': container_name,
          'cpuset': cpuset,
          'mem_units': mem_units
        }
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)

    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(response))
    return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
  logging.getLogger('requests').setLevel(logging.WARNING)
  logging.getLogger('botocore').setLevel(logging.WARNING)
  topologyManager.init()
  listen_ip = '0.0.0.0'
  if len(argv) >= 2:
    port = int(argv[1])
  else:
    port = 8000

  server = ThreadedHTTPServer((listen_ip, port), HttpHandler)
  print 'server has started at {0}:{1}'.format(listen_ip, port)
  server.serve_forever()