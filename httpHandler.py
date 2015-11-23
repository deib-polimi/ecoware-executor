#!/usr/bin/python

import SimpleHTTPServer
import SocketServer

class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path == '/':
      self.path = '/www/index.html'
    else:
      self.path = '/www' + self.path

    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

if (__name__ == '__main__'):
  listen_ip = '0.0.0.0'
  port = 8080
  server = SocketServer.TCPServer((listen_ip, port), HttpHandler)
  print 'server has started at {0}:{1}'.format(listen_ip, port)
  server.serve_forever()
  