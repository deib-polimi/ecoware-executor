#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import collections
from sets import Set

import vm
import db
from db import get_connection
from container import Container
from tier import Tier


_topology = {} # id->vm
_tiers = {}
_ports = {}

def init():
  global _topology, _ports, _tiers
  conn = get_connection()
  try:
    for row in conn.execute('select * from tier'):

      tier_hooks = []
      for subrow in conn.execute('select * from tier_hook where tier_id = ?', (row[0],)):
        tier_hooks.append(subrow[2])

      depends_on = []
      for subrow in conn.execute('select * from dependency where from_tier_id = ?', (row[0],)):
        depends_on.append(subrow[2])
      
      new_tier = Tier(row[0], row[1], row[2], depends_on, tier_hooks)
      _tiers[row[1]] = new_tier
    for row in conn.execute('select * from vm'):
      new_vm = vm.Vm(row[0], row[1], row[2], row[3], row[4], row[5])
      for subrow in conn.execute('select * from container where vm_id = ?', (new_vm.id,)):
        scale_hooks = []
        for hook_row in conn.execute('select * from scale_hook where container_id = ?', (subrow[0],)):
          scale_hooks.append(hook_row[2])

        cpuset = map(int, subrow[3].split(','))
        docker = Container(subrow[0], new_vm, subrow[2], cpuset, subrow[4], scale_hooks)
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
  if not port or port == -1:
    port = get_next_docker_port()
  if not host:
    host = 'localhost'
  id = None
  new_vm = vm.Vm(id, name, cpu_cores, mem_units, host, port)
  if host in ('localhost', '127.0.0.1'):
    host = 'localhost'
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

def run_container(vm_id, name, cpuset, mem_units, scale_hooks):
  container_vm = _topology[vm_id]
  id = None
  new_container = Container(id, container_vm, name, cpuset, mem_units, scale_hooks)
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

def update_container(id, cpuset, mem_units, scale_hooks):
  for vm in _topology.values():
    for container in vm.containers:
      if container.id == id:
        if not vm.host  in ['localhost', '127.0.0.1']:
          raise Exception('Container update can not be run on remote host')
        container.update(cpuset, mem_units, scale_hooks)
        db.update_container(container)
        return container
  raise Exception('Container id={} not found'.format(id))

def get_allocation():
  new_topology = {}
  for vm in _topology.values():
    new_topology[vm.name] = collections.OrderedDict()
    new_topology[vm.name]['host'] = vm.host
    new_topology[vm.name]['docker_port'] = vm.docker_port
    new_topology[vm.name]['cpu_cores'] = vm.cpu_cores
    new_topology[vm.name]['mem_units'] = vm.mem_units
    containers = {}
    for container in vm.containers:
      new_topology[vm.name]['containers'] = containers
      containers[container.name] = collections.OrderedDict()
      containers[container.name]['cpuset'] = ','.join(map(str, container.cpuset))
      containers[container.name]['mem_units'] = container.mem_units
      containers[container.name]['scale_hooks'] = []
      for scale_hook in container.scale_hooks:
        containers[container.name]['scale_hooks'].append(scale_hook)
  return new_topology

def get_topology():
  result = {}
  app = collections.OrderedDict()
  result['app'] = app
  app['name'] = 'Ecoware'
  tiers = collections.OrderedDict()
  app['tiers'] = tiers
  for tier_name in _tiers:
    ex_tier = _tiers[tier_name]
    tier = collections.OrderedDict()
    tiers[tier_name] = tier
    tier['image'] = ex_tier.image
    if ex_tier.depends_on:
      tier['depends_on'] = ex_tier.depends_on
    if ex_tier.tier_hooks:
      tier['tier_hooks'] = ex_tier.tier_hooks
  return result

def _map_topology_by_name():
  new_topology = {}
  for vm in _topology.values():
    new_topology[vm.name] = vm
  return new_topology

def _map_containers_by_name(containers):
  new_map = {}
  for container in containers:
    new_map[container.name] = container
  return new_map

def set_topology(data):
  tiers = data['app']['tiers']
  _parse_tiers(tiers)

def execute(data):
  changed_containers = _execute_plan(data)
  _process_tier_hooks(changed_containers)

def _process_tier_hooks(changed):
  tiers_to_run_hooks = Set()
  for tier in _tiers.values():
    for dependency in tier.depends_on:
      if tier.tier_hooks and dependency in changed:
        tiers_to_run_hooks.add(tier.name)
  for vm in _topology.values():
    for container in vm.containers:
      if container.name in tiers_to_run_hooks:
        hooks = _tiers[container.name].tier_hooks
        container.run_tier_hooks(hooks)

def _parse_tiers(tiers):
  global _tiers
  _tiers.clear()
  db.delete_tiers()
  if tiers is not None:
    for name in tiers:
      image = tiers[name]['image']
      depends_on = tiers[name].get('depends_on')
      tier_hooks = tiers[name].get('tier_hooks')
      id = None
      new_tier = Tier(id, name, image, depends_on, tier_hooks)
      db.insert_tier(new_tier)
      _tiers[name] = new_tier

def _execute_plan(plan):
  changed = Set()
  topology_by_name = _map_topology_by_name()  
  for vm_name in plan:
    is_local = False
    plan_vm = plan[vm_name]
    containers = {}
    vm_obj = None
    plan_containers = plan_vm.get('containers')
    if not vm_name in topology_by_name:
      # create vm
      vm_obj = create_vm(vm_name, plan_vm['cpu_cores'], plan_vm['mem_units'], plan_vm.get('host'), plan_vm.get('docker_port'))
    else:
      vm_obj = topology_by_name[vm_name]
      containers = _map_containers_by_name(vm_obj.containers)
      for container in vm_obj.containers:
        if (not plan_containers or 
            not container.name in plan_containers):
          # delete container
          changed.add(container.name)
          delete_container(container.id)

    if 'containers' in plan_vm:
      for container_name in plan_vm['containers']:
        plan_container = plan_vm['containers'][container_name]
        cpuset = map(int, plan_container['cpuset'].split(','))
        mem_units = plan_container['mem_units']
        scale_hooks = plan_container.get('scale_hooks')
        
        if not container_name in containers:
          # create container
          run_container(vm_obj.id, container_name, cpuset, mem_units, scale_hooks)
          changed.add(container_name)
        else:
          # update container
          container_obj = containers[container_name]
          if cpuset != container_obj.cpuset or mem_units != container_obj.mem_units:
            update_container(container_obj.id, cpuset, mem_units, scale_hooks)
            changed.add(container_obj.name)
  for vm in _topology.values():
    if not vm.name in plan:
      # delete vm
      delete_vm(vm.id)
      for container in vm.containers:
        changed.add(container.name)
  return changed

def get_tier_image(tier):
  return _tiers[tier].image

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  init()
  get_topology()