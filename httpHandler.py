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
    self.send_response(200)
    self.send_header('Content-type','text/html')

    return self.base_do_GET()

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

  def base_do_GET(self):
      """Serve a GET request."""
      f = self.send_head()
      if f:
          self.copyfile(f, self.wfile)
          f.close()

  def send_head(self):
      """Common code for GET and HEAD commands.

      This sends the response code and MIME headers.

      Return value is either a file object (which has to be copied
      to the outputfile by the caller unless the command was HEAD,
      and must be closed by the caller under all circumstances), or
      None, in which case the caller has nothing further to do.

      """
      path = self.translate_path(self.path)
      f = None
      if os.path.isdir(path):
          for index in "index.html", "index.htm":
              index = os.path.join(path, index)
              if os.path.exists(index):
                  path = index
                  break
          else:
              return self.list_directory(path)
      ctype = self.guess_type(path)
      if ctype.startswith('text/'):
          mode = 'r'
      else:
          mode = 'rb'
      try:
          f = open(path, mode)
      except IOError:
          self.send_error(404, "File not found")
          return None
      self.send_response(200)
      self.send_header("Content-type", ctype)
      self.end_headers()
      return f

  def list_directory(self, path):
      """Helper to produce a directory listing (absent index.html).

      Return value is either a file object, or None (indicating an
      error).  In either case, the headers are sent, making the
      interface the same as for send_head().

      """
      try:
          list = os.listdir(path)
      except os.error:
          self.send_error(404, "No permission to list directory")
          return None
      list.sort(lambda a, b: cmp(a.lower(), b.lower()))
      f = StringIO()
      f.write("<title>Directory listing for %s</title>\n" % self.path)
      f.write("<h2>Directory listing for %s</h2>\n" % self.path)
      f.write("<hr>\n<ul>\n")
      for name in list:
          fullname = os.path.join(path, name)
          displayname = linkname = name = cgi.escape(name)
          # Append / for directories or @ for symbolic links
          if os.path.isdir(fullname):
              displayname = name + "/"
              linkname = name + "/"
          if os.path.islink(fullname):
              displayname = name + "@"
              # Note: a link to a directory displays with @ and links with /
          f.write('<li><a href="%s">%s</a>\n' % (linkname, displayname))
      f.write("</ul>\n<hr>\n")
      f.seek(0)
      self.send_response(200)
      self.send_header("Content-type", "text/html")
      self.end_headers()
      return f

  def translate_path(self, path):
      """Translate a /-separated PATH to the local filename syntax.

      Components that mean special things to the local file system
      (e.g. drive or directory names) are ignored.  (XXX They should
      probably be diagnosed.)

      """
      path = posixpath.normpath(urllib.unquote(path))
      words = path.split('/')
      words = filter(None, words)
      path = os.getcwd()
      for word in words:
          drive, word = os.path.splitdrive(word)
          head, word = os.path.split(word)
          if word in (os.curdir, os.pardir): continue
          path = os.path.join(path, word)
      return path

  def copyfile(self, source, outputfile):
      """Copy all data between two file objects.

      The SOURCE argument is a file object open for reading
      (or anything with a read() method) and the DESTINATION
      argument is a file object open for writing (or
      anything with a write() method).

      The only reason for overriding this would be to change
      the block size or perhaps to replace newlines by CRLF
      -- note however that this the default server uses this
      to copy binary data as well.

      """
      shutil.copyfileobj(source, outputfile)

  def guess_type(self, path):
      """Guess the type of a file.

      Argument is a PATH (a filename).

      Return value is a string of the form type/subtype,
      usable for a MIME Content-type header.

      The default implementation looks the file's extension
      up in the table self.extensions_map, using text/plain
      as a default; however it would be permissible (if
      slow) to look inside the data to make a better guess.

      """

      base, ext = posixpath.splitext(path)
      if self.extensions_map.has_key(ext):
          return self.extensions_map[ext]
      ext = ext.lower()
      if self.extensions_map.has_key(ext):
          return self.extensions_map[ext]
      else:
          return self.extensions_map['']

  extensions_map = mimetypes.types_map.copy()
  extensions_map.update({
      '': 'application/octet-stream', # Default
      '.py': 'text/plain',
      '.c': 'text/plain',
      '.h': 'text/plain',
      })

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