#!/usr/bin/python

import copy
import json
import requests
import time

import aws_driver
import simple_executor
from monolitic_translator import MonoliticTranslator
from action import ActionType

_topology = {
  'app': {
    'name': 'Ecoware',
    'auto_scale_group_name': 'monolithic-experiments',
    'vm_cpu_cores': 8,
    'vm_mem_units': 64,
    'tiers': {
      'pwitter-web': {
        'image': 'pwitter-web',
        'docker_params': '-p 8080:5000 --add-host="db:172.31.31.123"',
        'entrypoint_params': '-w 3 -k eventlet'
      },
      'rubis-jboss': {
        'image': 'polimi/rubis-jboss:nosensors',
        'docker_params': '-p 80:8080 --add-host="db:172.31.31.123"',
        'entrypoint_params': '/opt/jboss-4.2.2.GA/bin/run.sh --host=0.0.0.0 --bootdir=/opt/rubis/rubis-cvs-2008-02-25/Servlets_Hibernate -c default'
      }
    }
  }
}

_allocation = {
}
def get_topology():
  return _topology

def set_topology(new_topology):
  global _topology
  _topology = new_topology

def get_allocation():
    return _allocation

def execute(plan):
  global _allocation, _topology
  _allocation.pop('time', None)
  old_allocation = copy.deepcopy(_allocation)
  topology = _topology
  allocation = _allocation
  
  group_name = topology['app']['auto_scale_group_name']
  translator = MonoliticTranslator()
  new_allocation = translator.translate2allocation(plan, allocation)
  print 'new_allocation', new_allocation
  vm_name_dict = {}
  if allocation != new_allocation:
    if len(allocation) < len(new_allocation): # only create new vm,
      capacity = len(new_allocation)
      print 'capacity', capacity
      print 'aws group', group_name
      start = time.time()
      vms = aws_driver.start_virtual_machines(group_name, capacity)
      finish = time.time()
      print start, finish, finish - start
      if finish - start > 10:
        print 'SLEEP 30 seconds to wait till OS is booted'  
        time.sleep(30)
      print 'VMS', vms
      i = 0
      for vm_name, ip_addr in vms:
        print vm_name, ip_addr, vm_name_dict
        if not vm_name in allocation:
          vm_name_dict['new_vm{}'.format(i)] = (vm_name, ip_addr)
          i += 1
        print 'topology', topology, 'url', 'http://{}:8000/api/monolitic/topology'.format(ip_addr)
        r = requests.post('http://{}:8000/api/monolitic/topology'.format(ip_addr), json=topology)
        print 'set topology to ', ip_addr, r.text
    used_ip = {}
    print vm_name_dict
    for vm in new_allocation:
      print vm
      if vm.startswith('new_vm'):
        vm_name, ip_addr = vm_name_dict[vm]
        print vm, vm_name, ip_addr
        # create VM
        allocation[vm_name] = {
          'ip': ip_addr,
          'cpu_cores': 8,
          'mem_units': 64,
          'used': {}
        }

        # create Containers
        for container in new_allocation[vm]:
          payload = {
            'ip': ip_addr,
            'name': container,
            'cpuset': range(0, int(new_allocation[vm][container]['cpu_cores'])),
            'mem_units': int(new_allocation[vm][container]['mem_units'])
          }
          print 'payload', payload
          r = requests.post('http://{}:8000/api/docker/run'.format(ip_addr), data=json.dumps(payload))
          print 'run container', ip_addr, r.text
          allocation[vm_name]['used'][container] = {
            'cpu_cores': len(payload['cpuset']),
            'mem_units': payload['mem_units']
          }
      else: # existing vm
        if not vm in allocation: raise Error('Unknown vm: ' + vm)
        ip_addr = allocation[vm]['ip']
        for container in new_allocation[vm]:
          old_containers = allocation[vm]['used']
          if not container in old_containers:
            # create new container
            payload = {
              'name': container,
              'cpuset': range(0, int(new_allocation[vm][container]['cpu_cores'])),
              'mem_units': int(new_allocation[vm][container]['mem_units'])
            }
            print 'payload', payload
            r = requests.post('http://{}:8000/api/docker/run'.format(ip_addr), data=json.dumps(payload))
            print 'run container', ip_addr, r.text
            allocation[vm]['used'][container] = {
              'cpu_cores': len(payload['cpuset']),
              'mem_units': payload['mem_units']
            }
          else:
            old_container_data = old_containers[container]
            new_container_data = new_allocation[vm][container]
            if (old_container_data['cpu_cores'] != new_container_data['cpu_cores'] or
                old_container_data['mem_units'] != new_container_data['mem_units']):
              # update container
              payload = {
                'cpuset': range(0, int(new_allocation[vm][container]['cpu_cores'])),
                'mem_units': int(new_allocation[vm][container]['mem_units'])
              }
              print 'payload', payload
              r = requests.put('http://{}:8000/api/docker/{}'.format(ip_addr, container), data=json.dumps(payload))
              print 'update container', ip_addr, r.text, payload
              allocation[vm]['used'][container] = {
                'cpu_cores': len(payload['cpuset']),
                'mem_units': payload['mem_units']
              }

        for container_name in allocation[vm]['used'].keys():
          if not container_name in new_allocation[vm]:
            # delete container
              r = requests.delete('http://{}:8000/api/docker/{}'.format(ip_addr, container_name))
              print 'update container', ip_addr, r.text, payload
              del allocation[vm]['used'][container_name]

    for vm_name in old_allocation.keys():
      if not vm_name in new_allocation:
        aws_driver.remove_vm(vm_name, group_name)
        del allocation[vm_name]

    print 'plan=', plan
    print 'allocation=', allocation
  return allocation

def translate(plan):
  global _allocation, _topology
  _allocation.pop('time', None)
  topology = _topology
  allocation = _allocation
  translator = MonoliticTranslator()
  actions = translator.translate(plan, allocation)
  return actions