#!/usr/bin/python

import logging
import copy
import time
import requests
import json
import os
from sets import Set

_allocation = {}
_topology = {}

def flatten_topology(topology):
  flat = {}
  for app in topology['apps']:
    for tier_name in app['tiers']:
      new_name = app['name'] + '_' + tier_name
      flat[new_name] = copy.deepcopy(app['tiers'][tier_name])
      if 'depends_on' in flat[new_name]:
        flat[new_name]['depends_on'] = map(lambda x: app['name'] + '_' + x, flat[new_name]['depends_on'])
  return flat

def set_topology(topology):
  global _topology
  _topology = topology
  for vm_name in _allocation:
    ip_addr = _allocation[vm_name]['ip']
    url = 'http://{}:8000/api/topology'.format(ip_addr)
    r = requests.put(url, data=json.dumps(topology), timeout=1)
    logging.debug('url={}; payload={}; result={}'.format(url, payload, r.text))
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
