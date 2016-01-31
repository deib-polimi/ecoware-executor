#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import vm
import db
from db import get_connection
from container import Container


_topology = {} # id->vm

_ports = {}

def init():
  global _topology, _ports
  conn = get_connection()
  try:
    for row in conn.execute('select * from vm'):
      new_vm = vm.Vm(row[0], row[1], row[2], row[3], row[4], row[5])
      for subrow in conn.execute('select * from container where vm_id = ?', (new_vm.id,)):
        docker = Container(subrow[0], new_vm, subrow[2], subrow[3], subrow[4])
        new_vm.containers.append(docker)
        logging.debug('container loaded={} for vm={}'.format(docker, new_vm.id))
      _topology[new_vm.id] = new_vm
      if new_vm.host in ['localhost', '127.0.0.1']:
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

def create_vm(name, cpu_cores, mem_units, host, port):
  global _topology, _ports
  if port == -1:
    port = get_next_docker_port()
  id = None
  new_vm = vm.Vm(id, name, cpu_cores, mem_units, host, port)
  if host in ('localhost', '127.0.0.1'):
    new_vm.start()
    _ports[new_vm.docker_port] = new_vm
  id = db.insert_vm(new_vm)
  new_vm.id = id
  _topology[new_vm.id] = new_vm
  return new_vm

def delete_vm(id):
  global _topology, _ports
  vm2remove = _topology[id]
  if vm2remove.host in ['localhost', '127.0.0.1']:
    vm2remove.delete()
    del _ports[vm2remove.docker_port]
  db.delete_vm(id)
  del _topology[id]

def stop_vm(id):
  vm2stop = _topology[id]
  vm2stop.stop()

def start_vm(id):
  vm2start = _topology[id]
  vm2start.start()

def run_container(vm_id, name, cpuset, mem_units):
  container_vm = _topology[vm_id]
  id = None
  new_container = Container(id, container_vm, name, cpuset, mem_units)
  new_container.run()
  id = db.insert_container(new_container)
  new_container.id = id
  container_vm.containers.append(new_container)
  return new_container

def stop_container(id):
  for vm in _topology.values():
    for container in vm.containers:
      if container.id == id:
        container.stop()
        return
  raise Exception('Container id={} not found'.format(id))

def start_container(id):
  for vm in _topology.values():
    for container in vm.containers:
      if container.id == id:
        container.start()
        return
  raise Exception('Container id={} not found'.format(id))

def delete_container(id):
  for vm in _topology.values():
    container2delete = None
    for container in vm.containers:
      if container.id == id:
        container.delete()
        db.delete_container(id)
        container2delete = container
    if not container2delete is None:
      vm.containers.remove(container2delete)
      return
  raise Exception('Container id={} not found'.format(id))

def update_container(id, cpuset, mem_units):
  for vm in _topology.values():
    for container in vm.containers:
      if container.id == id:
        if not vm.host  in ['localhost', '127.0.0.1']:
          raise Exception('Container update can not be run on remote host')
        container.update(cpuset, mem_units)
        db.update_container(container)
        return container
  raise Exception('Container id={} not found'.format(id))

def get_host_topology():
  host_map = {}
  for vm in _topology.values():
    if not vm.host in host_map:
      host_map[vm.host] = {}
    host_map[vm.host][vm.name] = {}
    for container in vm.containers:
      host_map[vm.host][vm.name][container.name] = {
        'cpuset': map(int, container.cpuset.split(',')),
        'mem_units': container.mem_units,
        'scale_hooks': ['touch.sh']
      }
  logging.debug('host_map={}'.format(host_map))
  return host_map

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  init()
  get_host_topology()