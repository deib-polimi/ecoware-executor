#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG)

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import BaseHTTPServer
import threading
import json
import time
import sys
import traceback
import mimetypes
import posixpath
import urllib
import os
import shutil
from sets import Set
from sys import argv

import docker

CPU_NUMBER = 8

used_cpus = Set()

topology = {}

def get_cpuset(cpu_cores):
  cpuset = []
  if CPU_NUMBER - len(used_cpus) < cpu_cores:
    raise Exception('Not enough CPU_CORES')
  for i in range(0, CPU_NUMBER):
    if not i in used_cpus:
      used_cpus.add(i)
      cpuset.append(i)
      if len(cpuset) == cpu_cores:
        return cpuset
  return cpuset

def release_cpuset(cpuset_arr):
  for i in cpuset_arr:
    used_cpus.discard(i)

class HttpHandler(BaseHTTPRequestHandler):

  def execute(self, plan):
    for tier in plan:
      cpu_cores = plan[tier]['cpu_cores']
      mem_units = plan[tier]['mem_units']

      if tier in topology:
        cpuset = topology[tier]
        release_cpuset(cpuset)

      cpuset = get_cpuset(cpu_cores)
      topology[tier] = cpuset

      print tier, cpu_cores, cpuset, mem_units
      docker.update_container(tier, cpuset, mem_units)

  def do_POST(self):
    start = time.time()
    if self.path.startswith('/api/executor'):
      try:
        post_data_string = self.rfile.read(int(self.headers['Content-Length']))
        plan = json.loads(post_data_string)

        self.execute(plan)

        response = {}
      except Exception as e: 
        response = {}
        response['error'] = repr(e)
        traceback.print_exc(file=sys.stdout)
    response['time'] = '{0:.2f}'.format(time.time() - start)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    print response
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