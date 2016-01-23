#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import vm
from db import get_connection, insert_vm


_topology = {}
_ports = {}

def init():
  global _topology, _ports
  conn = get_connection()
  try:
    for row in conn.execute('select * from vm'):
      new_vm = vm.Vm(row[0], row[1], row[2], row[3], row[4])
      _topology[new_vm.name] = new_vm
      _ports[new_vm.docker_port] = new_vm
      logging.debug('vm loaded={}'.format(new_vm))
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
  new_vm = vm.Vm(id, name, cpu_cores, mem_units, port)
  new_vm.start()
  id = insert_vm(new_vm)
  new_vm.id = id
  _topology[new_vm.name] = new_vm
  _ports[new_vm.docker_port] = new_vm
  return new_vm