#!/usr/bin/python

import logging
from sets import Set

import docker

_used_cpus = Set()
_allocation = {}
_topology = {'cpu_cores': 0}

def get_cpuset(cpu_cores):
  used_cpus = _used_cpus
  cpuset = []
  vm_cpu_cores = _topology['cpu_cores']
  if vm_cpu_cores - len(used_cpus) < cpu_cores:
    raise Exception('Not enough CPU cores')
  for i in range(0, vm_cpu_cores):
    if not i in used_cpus:
      used_cpus.add(i)
      cpuset.append(i)
      if len(cpuset) == cpu_cores:
        return cpuset
  return cpuset

def release_cpuset(cpuset_arr):
  used_cpus = _used_cpus
  for i in cpuset_arr:
    used_cpus.discard(i)

def update_containers(self, plan):
  allocation = _allocation
  for tier in plan:
    if tier in allocation:
      cpuset = allocation[tier]['cpuset']
      release_cpuset(cpuset)

  for tier in plan:
    cpu_cores = plan[tier]['cpu_cores']
    mem_units = plan[tier]['mem_units']

    if not tier in allocation:
      allocation[tier] = {}

    allocation[tier]['cpu_cores'] = cpu_cores
    allocation[tier]['mem_units'] = mem_units

    cpuset = get_cpuset(cpu_cores)
    allocation[tier]['cpuset'] = cpuset

    logging.debug('Update container; {} {} {} {}'.format(tier, cpu_cores, cpuset, mem_units))
    docker.update_container(tier, cpuset, mem_units)

def set_topology(topology):
  _topology['cpu_cores'] = topology['cpu_cores']

def get_allocation():
  return _allocation

def inspect():
  return docker.inspect()

def get_topology():
  return _topology

def create_container(container):
  allocation = _allocation
  tier = container['name']
  if tier in allocation:
    raise Exception('Trying create already existing container: ' + tier)
  cpu_cores = container['cpu_cores']
  mem_units = container['mem_units']
  allocation[tier] = {}
  allocation[tier]['cpu_cores'] = cpu_cores
  allocation[tier]['mem_units'] = mem_units

  cpuset = get_cpuset(cpu_cores)
  allocation[tier]['cpuset'] = cpuset
  image = container['image']
  docker_params = container.get('docker_params', '')
  endpoint_params = container.get('endpoint_params', '')
  logging.debug('Run container; {} {} {} {} {} {} {}'.format(tier, image, cpu_cores, cpuset, mem_units, docker_params, endpoint_params))
  docker.run_container(tier, image, cpuset, mem_units, docker_params, endpoint_params)