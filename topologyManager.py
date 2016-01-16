#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import copy
import sqlite3
import logging

from action import ActionType

_topology = {}

conn = sqlite3.connect('executor.db')
try:
  vm_ids = {}
  for row in conn.execute('select * from vm'):
    _topology[row[1]] = {
      'cpu_cores': row[2],
      'mem': row[3]
    }
    _topology[row[1]]['used'] = {}
    vm_ids[row[0]] = row[1]
  for row in conn.execute('select * from container'):
    vm = vm_ids[row[1]]
    cpuset = row[3]
    cpu = len(cpuset.split(','))
    _topology[vm]['used'][row[2]] = {
      'cpu_cores': cpu,
      'mem': row[4]
    }
  logging.debug('topology={}'.format(_topology))  
finally:
  conn.close()    

def load(filename):
  global _topology
  data = {}
  with open(filename, 'r') as f:
    read_data = f.read()
    _topology = json.loads(read_data)
  f.closed

def get_current():
  return _topology

def preview(actions):
  new_topology = copy.deepcopy(_topology)
  for action in actions:
    if action.type == ActionType.vm_create:
      new_topology[action.vm]['used'] = {}
    elif action.type == ActionType.container_create:
      container = {}
      container['cpu_cores'] = action.cpu
      container['mem'] = action.mem
      new_topology[action.vm]['used'][action.container] = container
    elif action.type == ActionType.container_set:
      container = new_topology[action.vm]['used'][action.container]
      container['cpu_cores'] = action.cpu
      container['mem'] = action.mem
    elif action.type == ActionType.vm_delete:
      new_topology.pop(action.vm)
    elif action.type == ActionType.container_delete:
      print 'new_topology', new_topology, 'action_vm', action.vm, 'tier=', action.container
      new_topology[action.vm]['used'].pop(action.container)
  return new_topology

def execute(actions):
  global _topology
  _topology = preview(actions)
  return _topology

def set(new_topology):
  global _topology
  _topology = new_topology