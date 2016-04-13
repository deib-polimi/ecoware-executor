#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG)

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import json
import time
import sys
import traceback
import copy
from sys import argv

import topology

class HttpHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    start = time.time()
    response = {}
    try:
      if self.path.startswith('/api/allocation'):
        allocation = topology.get_allocation()
        response = copy.deepcopy(allocation)
      elif self.path.startswith('/api/inspect'):
        response = topology.inspect()
      elif self.path.startswith('/api/topology'):
        response = topology.get_topology()
      else:
        self.send_error(404)
        return
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

  def do_POST(self):
    start = time.time()
    try:
      post_data_string = self.rfile.read(int(self.headers['Content-Length']))
      logging.debug('POST data ' + post_data_string)
      data = json.loads(post_data_string)
      if self.path.startswith('/api/run/tier_hooks'):
        topology.run_tier_hooks(data)
        response = {}
      else:
        self.send_error(404)
        return
    except Exception as e: 
      response = {}
      response['error'] = repr(e)
      traceback.print_exc(file=sys.stdout)
    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    logging.debug(response)
    self.wfile.write(json.dumps(response))

  def do_PUT(self):
    start = time.time()
    try:
      data_string = self.rfile.read(int(self.headers['Content-Length']))
      logging.debug('PUT data ' + data_string)
      data = json.loads(data_string)
      if self.path.startswith('/api/topology'):
        topology.set_topology(data)
        response = {}
      elif self.path.startswith('/api/execute'):
        topology.execute(data)
        response = {}
      elif self.path.startswith('/api/translate'):
        actions = topology.translate(data)
        response = {
          'actions': actions
        }
      elif self.path.startswith('/api/cpuset/release'):
        topology.release_cpuset_by_tiers(data)
        response = {}
      elif self.path.startswith('/api/docker/run'):
        topology.run(data)
        response = {}
      elif self.path.startswith('/api/docker/update'):
        topology.update(data)
        response = {}
      else:
        self.send_error(404)
        return
    except Exception as e: 
      response = {}
      response['error'] = repr(e)
      traceback.print_exc(file=sys.stdout)
    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    logging.debug(response)
    self.wfile.write(json.dumps(response))

  def do_DELETE(self):
    start = time.time()
    try:
      data_string = self.rfile.read(int(self.headers['Content-Length']))
      logging.debug('DELETE data ' + data_string)
      data = json.loads(data_string)
      if self.path.startswith('/api/docker'):
        topology.remove(data)
        response = {}
      else:
        self.send_error(404)
        return
    except Exception as e: 
      response = {}
      response['error'] = repr(e)
      traceback.print_exc(file=sys.stdout)
    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    logging.debug(response)
    self.wfile.write(json.dumps(response))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
  listen_ip = '0.0.0.0'
  if len(argv) >= 2:
    port = int(argv[1])
  else:
    port = 8000

  server = ThreadedHTTPServer((listen_ip, port), HttpHandler)
  print 'server has started at {0}:{1}'.format(listen_ip, port)
  server.serve_forever()