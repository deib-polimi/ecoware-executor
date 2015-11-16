#!/usr/bin/python

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
  with open('plan.json', 'r') as f:
    read_data = f.read()
    print read_data
  f.closed

read_plan()