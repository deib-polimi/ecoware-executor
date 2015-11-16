#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

topology = {
  'vm1': {
    'cpu': 1,
    'mem': 1
  },
  'vm2': {
    'cpu': 2,
    'mem': 2
  }
}

def read_plan():
  plan = {}
  with open('plan.json', 'r') as f:
    read_data = f.read()
    plan = json.loads(read_data)
  f.closed
  return plan

print read_plan()