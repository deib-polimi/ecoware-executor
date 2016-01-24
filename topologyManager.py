#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import vm
import db
from db import get_connection
from container import Container


_topology = {}
_ports = {}

def init():
  global _topology, _ports
  conn = get_connection()
  try:
    for row in conn.execute('select * from vm'):
      new_vm = vm.Vm(row[0], row[1], row[2], row[3], row[4])
      for subrow in conn.execute('select * from container where vm_id = ?', (new_vm.id,)):
        docker = Container(subrow[0], new_vm, subrow[2], subrow[3], subrow[4])
        new_vm.containers.append(docker)
        logging.debug('container loaded={} for vm={}'.format(docker, new_vm.id))
      _topology[new_vm.id] = new_vm
      _ports[new_vm.docker_port] = new_vm
      logging.debug('vm loaded={}'.format(new_vm))
    logging.debug('topology loaded={}'.format(_topology))
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
  id = db.insert_vm(new_vm)
  new_vm.id = id
  _topology[new_vm.id] = new_vm
  _ports[new_vm.docker_port] = new_vm
  return new_vm

def delete_vm(id):
  global _topology, _ports
  vm2remove = _topology[id]
  vm2remove.delete()
  db.delete_vm(id)
  del _topology[id]
  del _ports[vm2remove.docker_port]

def stop_vm(id):
  vm2stop = _topology[id]
  vm2stop.stop()

def start_vm(id):
  vm2start = _topology[id]
  vm2start.start()

def create_container(vm_id, name, cpuset, mem_units):
  container_vm = _topology[vm_id]
  id = None
  new_container = Container(id, container_vm, name, cpuset, mem_units)
  new_container.start()
  id = db.insert_container(new_container)
  new_container.id = id
  container_vm.containers.append(new_container)
  return new_container