#!/usr/bin/python
# -*- coding: utf-8 -*-

class TopologyManager:
  
  def get_current(self):
    return {
      'vm1': {
        'cpu_cores': 2,
        'mem': 2
      },
      'vm2': {
        'cpu_cores': 2,
        'mem': 2
      }
    }