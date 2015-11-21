#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

class TopologyManager:
  
  def __init__(self):
    self.load('topology.json')

  def load(self, filename):
    with open(filename, 'r') as f:
      read_data = f.read()
      self._plan = json.loads(read_data)
    f.closed

  def get_current(self):
    return self._plan