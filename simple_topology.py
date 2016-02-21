#!/usr/bin/python

import copy

import aws_driver

_topology = {
  'jboss': {
    'auto_scale_group_name': 'ex3',
    'vm_cpu_cores': 2,
    'vm_mem_units': 8
  }
}

_allocation = {
  'jboss': {
    'cpu_cores': 0,
    'mem_units': 0
  }
}
def get_topology():
  return _topology

def set_topology(new_topology):
  global _topology
  _topology = new_topology

def get_allocation():
  groups = aws_driver.get_auto_scale_groups()
  allocation = copy.deepcopy(_allocation)
  for tier in allocation:
    group_name = _topology[tier]['auto_scale_group_name']
    capacity = groups[group_name]
    allocation[tier]['desired_capacity'] = capacity
  return allocation