#!/usr/bin/python

import logging
import subprocess
import os
from sets import Set

import docker

_used_cpus = Set()
_allocation = {}
_topology = {"infrastructure" : {"cpu_cores": 0, "mem_units": 0}}
_tiers = {}

def get_cpuset(cpu_cores):
  used_cpus = _used_cpus
  cpuset = []
  vm_cpu_cores = _topology['infrastructure']['cpu_cores']
  if vm_cpu_cores - len(used_cpus) < cpu_cores:
    logging.error('vm_cpu_cores={}; used_cpus={}; "cpu_cores={}; allocation={}'.format(vm_cpu_cores, used_cpus, cpu_cores, _allocation))
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

def release_cpuset_by_tiers(tiers):
  allocation = _allocation
  for tier in tiers:
    if tier in allocation:
      cpuset_arr = allocation[tier]['cpuset']
      release_cpuset(cpuset_arr)

def _allocate(data):
  allocation = _allocation
  tier = data['name']
  cpu_cores = data['cpu_cores']
  allocation[tier] = {}
  allocation[tier]['cpu_cores'] = data['cpu_cores']
  allocation[tier]['mem_units'] = data['mem_units']
  cpuset = get_cpuset(cpu_cores)
  allocation[tier]['cpuset'] = cpuset
  return cpuset

def run(data):
  cpuset = _allocate(data)

  tier = data['name']
  cpu_cores = data['cpu_cores']
  mem_units = data['mem_units']
  hosts = data.get('hosts', [])

  info = get_tier_info(tier)
  image = info['docker_image']
  entrypoint_params = info.get('entrypoint_params', '')
  logging.debug('params; {} {} {}'.format(image, host, entrypoint_params))
  docker_params = ''
  for host in hosts:
    docker_params += ' --add-host "{}"'.format(host)
  docker.run_container(tier, image, cpuset, mem_units, docker_params, entrypoint_params)
  if 'scale_hooks' in info:
    docker.run_scale_hooks(tier, info['scale_hooks'])

def update(data):
  cpuset = _allocate(data)

  tier = data['name']
  cpu_cores = data['cpu_cores']
  mem_units = data['mem_units']

  docker.update_container(tier, cpuset, mem_units)
  info = get_tier_info(tier)
  if 'scale_hooks' in info:
    docker.run_scale_hooks(tier, info['scale_hooks'])

def remove(data):
  allocation = _allocation
  tier = data['name']

  if tier in allocation:
    del allocation[tier]

  docker.remove_container(tier)

def execute(plan):
  allocation = _allocation

  # DELETE
  for tier in allocation:
    if not tier in plan:
      cpuset = allocation[tier]['cpuset']
      release_cpuset(cpuset)
      del allocation[tier]
      docker.remove_container(tier)

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
      info = get_tier_info(tier)
      image = info['docker_image']
      entrypoint_params = info.get('entrypoint_params', '')
      logging.debug('params; {} {}'.format(image, entrypoint_params))
      docker.run_container(tier, image, cpuset, mem_units, entrypoint_params)
      if 'scale_hooks' in info:
        docker.run_scale_hooks(tier, info['scale_hooks'])
    else:
      docker.update_container(tier, cpuset, mem_units)

def get_tier_info(tier):
  for tier_name in _tiers:
    if tier_name == tier:
      return _tiers[tier_name]
  raise Exception('Unknown tier ' + tier)

def translate(plan):
  allocation = _allocation

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
  global _topology, _tiers
  _topology = topology
  if 'hooks_git_repo' in topology['infrastructure']:
    update_scale_folder(topology['infrastructure']['hooks_git_repo'])
  _tiers = {}
  tiers = _tiers
  for app_json in topology['apps']:
    for tier_name in app_json['tiers']:
      flat_name = '{}_{}'.format(app_json['name'], tier_name)
      tiers[flat_name] = app_json['tiers'][tier_name]

def update_scale_folder(git_repo):
  logging.debug('git repo' + git_repo)
  try:
    dir_name = '/ecoware'
    repo_folder = '/ecoware/hooks'
    if not os.path.isdir(dir_name):
      os.mkdir(dir_name)
      os.chdir(dir_name)
      cmd = 'git clone {} {}'.format(git_repo, repo_folder)
      subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    os.chdir(repo_folder)
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

def run_tier_hooks(tiers):
  for tier_name in tiers:
    if tier_name in _allocation:
      info = get_tier_info(tier_name)
      if 'tier_hooks' in info:
        docker.run_tier_hooks(tier_name, info['tier_hooks'])