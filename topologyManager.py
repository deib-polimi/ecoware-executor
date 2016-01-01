#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import copy
from action import ActionType

_topology = {}

def load(filename):
  global _topology
  data = {}
  with open(filename, 'r') as f:
    read_data = f.read()
    _topology = json.loads(read_data)
  f.closed

load('topology.json')

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
      new_topology[action.vm].pop(action.container)
  return new_topology

def execute(actions):
  global _topology
  _topology = preview(actions)
  return _topology

def set(new_topology):
  global _topology
  _topology = new_topology