#!/usr/bin/python

import logging
import copy
import time
import requests
import json
import os
from sets import Set

import translator
import executor
from solver import AllocationSolver


_allocation = {}
_topology = {}

def get_not_scalable_tiers(topology):
  result = []
  for app in topology['apps']:
    for tier_name in app['tiers']:
      max_node = app['tiers'][tier_name].get('max_node', 0)
      if max_node == 1:
        result.append(app['name'] + '_' + tier_name)
  return result

def execute(plan):
  global _allocation, _topology
  solver = AllocationSolver(_topology)
  flat_plan = flatten(plan)
  
  _allocation.pop('time', None)
  if solver.need_solution(flat_plan, _allocation):
    not_scalable_arr = get_not_scalable_tiers(_topology)
    new_allocation = solver.solve(flat_plan, _allocation, not_scalable_arr)
    logging.debug('new_allocation={}'.format(new_allocation))
    flat_topology = flatten_topology(_topology)
    actions =  translator.translate(_allocation, new_allocation, flat_topology)

    _allocation = executor.aws_execute(actions, new_allocation, _topology, _allocation)
  return _allocation

def flatten(plan):
  flat_plan = {}
  for app_name in plan:
    for tier_name in plan[app_name]:
      flat_name = '{}_{}'.format(app_name, tier_name)
      flat_plan[flat_name] = plan[app_name][tier_name]
  return flat_plan

def flatten_topology(topology):
  flat = {}
  for app in topology['apps']:
    for tier_name in app['tiers']:
      new_name = app['name'] + '_' + tier_name
      flat[new_name] = copy.deepcopy(app['tiers'][tier_name])
      if 'depends_on' in flat[new_name]:
        flat[new_name]['depends_on'] = map(lambda x: app['name'] + '_' + x, flat[new_name]['depends_on'])
  return flat

def translate(plan):
  solver = AllocationSolver(_topology)
  flat_plan = flatten(plan)
  not_scalable_arr = get_not_scalable_tiers(_topology)
  new_allocation = solver.solve(flat_plan, _allocation, not_scalable_arr)
  logging.debug('new_allocation={}'.format(new_allocation))
  flat_topology = flatten_topology(_topology)
  return translator.translate(_allocation, new_allocation, flat_topology)

def set_topology(topology):
  global _topology
  _topology = topology
  for vm_name in _allocation:
    ip_addr = _allocation[vm_name]['ip']
    url = 'http://{}:8000/api/topology'.format(ip_addr)
    r = requests.put(url, data=json.dumps(topology), timeout=1)
  logging.debug('Set topology is done')
  set_credentials(topology)

def get_allocation():
  return copy.deepcopy(_allocation)

def inspect():
  inspect = {}
  for vm_name in _allocation:
    ip_addr = _allocation[vm_name]['ip']
    url = 'http://{}:8000/api/inspect'.format(ip_addr)
    r = requests.get(url)
    logging.debug('url={}; result={}'.format(url, r.text))
    inspect[vm_name] = json.loads(r.text)
  return inspect

def get_topology():
  return _topology

def set_credentials(topology):
  filename = topology['infrastructure']['cloud_driver'].get('credentials', None)
  if filename:
    with open(filename, 'r') as f:
      for line in f:
        split = line.split('=')
        if len(split) == 2:
          key = split[0].strip()
          value = split[1].strip()
          logging.debug('set envvar ' + key)
          os.environ[key] = value

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  topology = {
    "infrastructure": {
      "cloud_driver": {
        "autoscaling_groupname": "monolithic-ex-2cpu",
        "credentials": "/ecoware/credentials.conf"
      },
      "max_vms": 10,
      "hooks_git_repo": "https://github.com/n43jl/hooks",
      "cpu_cores": 2,
      "mem_units": 8
    },
    "apps": [{
      "name": "rubis",
      "tiers": {
        "loadbalancer": {
          "name": "Front LoadBalancer",
          "max_node": 1,
          "docker_image": "nginx",
          "depends_on": ["app_server"],
          "on_dependency_scale": "reload_server_pool.sh",
          "max_rt": 0.1
        }, "app_server": {
          "name": "Application Logic Tier",
          "docker_image": "nginx",
          "depends_on": ["db"],
          "on_node_scale": "jboss_hook.sh",
          "on_dependency_scale": "reload_connections.sh",
          "ports": ["80:8080"]
        }, "db": {
          "name": "Data Tier",
          "max_node": 1,
          "docker_image": "nginx",
          "on_node_scale": "mysql_hook.sh",
          "max_rt": 0.2,
          "ports": ["3306:3306"]
        }

      }
    }, {
      "name": "pwitter",
      "tiers": {
        "app_server": {
          "name": "Application Logic Tier",
          "docker_image": "nginx",
          "ports": ["8080:5000"],
          "entrypoint_params": "-w 3 -k eventlet"
        }, "db": {
          "name": "Data Tier",
          "max_node": 1,
          "docker_image": "hello-world",
          "on_node_scale": "mysql_hook.sh",
          "max_rt": 0.2,
          "ports": ["3307:3306"]
        }
      }
    }]
  }

  plan = {
    "rubis": {
      "app_server": {
        "cpu_cores": 2,
        "mem_units": 2
      },
      "db": {
        "cpu_cores": 1,
        "mem_units": 1
      }
    }
  }

  set_topology(topology)
  actions = translate(plan)
  print map(lambda x: map(str, x), actions)
