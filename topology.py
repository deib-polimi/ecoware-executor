#!/usr/bin/python

import logging
import copy
import time
import requests
import json
import os
import threading
from sets import Set

import aws_driver

_allocation = {}
_topology = {}
lock = threading.RLock()

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
  with lock:
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

def set_vm_capacity(capacity):
  with lock:
    global _allocation, _topology
    allocation = _allocation
    topology = _topology
    start = time.time()
    vm_cpu = topology['infrastructure']['cpu_cores']
    vm_mem = topology['infrastructure']['mem_units']
    autoscaling_group = topology['infrastructure']['cloud_driver']['autoscaling_groupname']
    logging.info('New capacity={}; aws group={}'.format(capacity, autoscaling_group))
    vms = aws_driver.start_virtual_machines(autoscaling_group, capacity)
    finish = time.time()

    i = 0
    for vm_name in allocation.keys():
      found = False
      for name, ip in vms:
        if vm_name == name:
          found = True
      if not found:
        del allocation[vm_name]

    for vm_name, ip_addr in vms:
      success = False
      while not success:
        try:
          r = requests.put('http://{}:8000/api/topology'.format(ip_addr), json=topology, timeout=10)
          success = True
        except Exception as e:
          print e
          sleep_time = 10
          logging.info('VM is not ready;sleep {}s before setting topology;'.format(sleep_time))
          time.sleep(sleep_time)
      logging.debug('Set topology: {}'.format(r.text))
      allocation[vm_name] = {}
      allocation[vm_name]['ip'] = ip_addr
      allocation[vm_name]['cpu_cores'] = vm_cpu
      allocation[vm_name]['mem_units'] = vm_mem
      allocation[vm_name]['used'] = []

    finish = time.time()


    
