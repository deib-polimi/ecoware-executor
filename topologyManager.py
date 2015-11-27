#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import copy
from action import ActionType


class TopologyManager:
  
  def __init__(self):
    self.load('topology.json')

  def load(self, filename):
    with open(filename, 'r') as f:
      read_data = f.read()
      self._topology = json.loads(read_data)
    f.closed

  def get_current(self):
    return self._topology

  def preview(self, actions):
    new_topology = copy.deepcopy(self._topology)
    for action in actions:
      if action.type == ActionType.create or action.type == ActionType.modify:
        vm = new_topology[action.vm]
        used = vm['used'] if 'used' in vm else {}
        vm['used'] = used
        if action.type == ActionType.create:
          used[action.container] = {}
        container = used[action.container]
        container['cpu_cores'] = action.cpu
        container['mem'] = action.mem
      elif action.type == ActionType.delete:
        if action.container is not None:
          new_topology[action.vm].pop(action.container)
        else:
          new_topology.pop(action.vm)
    return new_topology

  def execute(self, actions):
    self._topology = self.preview(actions)
    return self._topology
