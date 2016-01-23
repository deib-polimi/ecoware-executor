#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from vm import Vm
from db import get_connection, insert_vm


_topology = {}
_ports = {}

def init():
  global _topology, _ports
  conn = get_connection()
  try:
    for row in conn.execute('select * from vm'):
      vm = Vm(row[0], row[1], row[2], row[3], row[4])
      _topology[vm.name] = vm
      _ports[vm.docker_port] = vm
      logging.debug('vm loaded={}'.format(vm))
    logging.debug('vm loaded={}'.format(_topology))
  finally:
    conn.close()

def get_vms():
  global _topology
  return _topology.values()

def get_next_docker_port():
  global _ports
  port = 5000
  while port in _ports:
    port += 1
  return port 

def create_vm(name, cpu_cores, mem_units):
  global _topology, _ports
  port = get_next_docker_port()
  id = None
  vm = Vm(id, name, cpu_cores, mem_units, port)
  id = insert_vm(vm)
  vm.id = id
  _topology[vm.name] = vm
  _ports[vm.docker_port] = vm
  return vm

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  init()