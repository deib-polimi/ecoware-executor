#!/usr/bin/python

import logging
import subprocess
from sets import Set

import docker

_used_cpus = Set()
_allocation = {}
_topology = {'cpu_cores': 0, 'mem_units': 0}

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

def execute(plan):
  allocation = _allocation
  topology = _topology

  # DELETE
  for tier in allocation:
    if not tier in plan:
      cpuset = allocation[tier]['cpuset']
      release_cpuset(cpuset)
      del allocation[tier]
      docker.remove_container(tier)
      changed.add(tier)

  # Release resources
  for tier in plan:
    if tier in allocation:
      cpuset = allocation[tier]['cpuset']
      release_cpuset(cpuset)

  for tier in plan:
    cpu_cores = plan[tier]['cpu_cores']
    mem_units = plan[tier]['mem_units']

    action = 'update'
    if not tier in allocation:
      action = 'create'
      allocation[tier] = {}

    allocation[tier]['cpu_cores'] = cpu_cores
    allocation[tier]['mem_units'] = mem_units

    cpuset = get_cpuset(cpu_cores)
    allocation[tier]['cpuset'] = cpuset

    logging.debug('{} container; {} {} {} {}'.format(action, tier, cpu_cores, cpuset, mem_units))
    if action == 'create':
      info = None
      for tier_info in topology['tiers']:
        if tier_info['name'] == tier:
          info = tier_info
          break
      if not info:
        raise Exception('Unknown tier ' + tier)
      image = info['image']
      docker_params = info.get('docker_params', '')
      endpoint_params = info.get('endpoint_params', '')
      logging.debug('params; {} {} {}'.format(image, docker_params, endpoint_params))
      docker.run_container(tier, image, cpuset, mem_units, docker_params, endpoint_params)
      if 'scale_hooks' in info:
        docker.run_scale_hooks(tier, info['scale_hooks'])
    else:
      docker.update_container(tier, cpuset, mem_units)

def translate(plan):
  allocation = _allocation
  topology = _topology

  actions = []
  # DELETE
  for tier in allocation:
    if not tier in plan:
      actions.append('delete container ' + tier)

  for tier in plan:
    cpu_cores = plan[tier]['cpu_cores']
    mem_units = plan[tier]['mem_units']

    action = 'update'
    if not tier in allocation:
      actions.append('create container "{}" with cpu_cores={} and mem_units={}'.format(tier, cpu_cores, mem_units))
    else:
      actions.append('update container "{}" set cpu_cores={} and mem_units={}'.format(tier, cpu_cores, mem_units))
  return actions

def set_topology(topology):
  global _topology
  _topology = topology
  if 'hooks_git' in topology:
    update_scale_folder(topology['hooks_git'])

def update_scale_folder(git_repo):
  try:
    dir_name = '/ecoware'
    repo_folder = '/ecoware/hooks'
    if !os.path.isdir(dir_name):
      os.mkdir(dir_name)
      os.chdir(dir_name)
      cmd = 'git clone {} {}'.format(git_repo, repo_folder)
      subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    os.chdir(dir_name)
    cmd = 'git pull'
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def get_allocation():
  return _allocation

def inspect():
  return docker.inspect()

def get_topology():
  return _topology