#!/usr/bin/python
import time
import logging
import requests
import json
from threading import Thread

import aws_driver
from action import action_type, VmAction, ContainerAction

def aws_create_vms(new_allocation, topology, prev_allocation):
  vm_name_dict = {}
  autoscaling_group = topology['infrastructure']['cloud_driver']['autoscaling_groupname']
  logging.debug('autoscaling group=' + autoscaling_group)
  need_vm_created = False
  for vm_name in new_allocation:
    if vm_name[:6] == 'new_vm':
      need_vm_created = True
      break
  if need_vm_created:
    start = time.time()
    capacity = len(new_allocation)
    logging.info('New capacity={}; aws group={}'.format(capacity, autoscaling_group))
    vms = aws_driver.start_virtual_machines(autoscaling_group, capacity)
    finish = time.time()

    i = 0
    for vm_name, ip_addr in vms:
      if not vm_name in prev_allocation:
        new_vm_name = 'new_vm{}'.format(i)
        vm_name_dict[new_vm_name] = (vm_name, ip_addr)
        i += 1
        logging.debug('VM: {}; {}; {}'.format(new_vm_name, vm_name, ip_addr))
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
    finish = time.time()
    if finish - start > 20:
      sleep_time = 20
      logging.debug('SLEEP {} seconds to wait till docker is booted'.format(sleep_time))
      time.sleep(sleep_time)
  return vm_name_dict

def get_hosts(app_name, tier_name, topology, allocation, vm_name_dict):
  hosts = []
  for app in topology['apps']:
    if app['name'] == app_name:
      tiers = app['tiers']
      tier = tiers[tier_name]
      dependencies = tier.get('depends_on', [])
      for key, value in tiers.iteritems():
        if 'max_node' in value and value['max_node'] == 1 and key in dependencies:
            hosts.append(key)
  result = []
  for host in hosts:
    full_name = app_name + '_' + host
    for vm_name in allocation:
      other_name, ip = vm_name_dict[vm_name]
      for item in allocation[vm_name]:
        if item == full_name:
          result.append(host + ':' + ip)
  return result

def aws_execute(actions, new_allocation, topology, prev_allocation):
  vm_name_dict = aws_create_vms(new_allocation, topology, prev_allocation)
  for vm_name in prev_allocation:
    ip = prev_allocation[vm_name]['ip']
    vm_name_dict[vm_name] = (vm_name, ip)

    tiers = []
    for action_list in actions:
      for action in action_list:
        if action.vm == vm_name and type(action) == ContainerAction:
          tiers.append(action.container)
    if tiers:
      url = 'http://{}:8000/api/cpuset/release'.format(ip)
      logging.debug('Release cpuset on {} for tiers {}'.format(ip, tiers))
      r = requests.put(url, data=json.dumps(tiers), timeout=10)

  vm_cpu = topology['infrastructure']['cpu_cores']
  vm_mem = topology['infrastructure']['mem_units']
  result_allocation = {}
  for vm_name in new_allocation:
    name, ip = vm_name_dict[vm_name]
    result_allocation[name] = {}
    result_allocation[name]['ip'] = ip
    result_allocation[name]['used'] = {}
    result_allocation[name]['cpu_cores'] = vm_cpu
    result_allocation[name]['mem_units'] = vm_mem
    for tier_name in new_allocation[vm_name]:
      result_allocation[name]['used'][tier_name] = new_allocation[vm_name][tier_name]

  for action_list in actions:
    threads = []

    for action in action_list:
      thread = Thread(target=threaded_run_action, args=(action, vm_name_dict, topology, new_allocation, prev_allocation, result_allocation))
      threads.append(thread)
      thread.start()

    for thread in threads:
      thread.join()

  return result_allocation

def threaded_run_action(action, vm_name_dict, topology, new_allocation, prev_allocation, result_allocation):
  logging.debug('Start run action: {}'.format(action.__str__()))
  if action.action_type == action_type['create_container']:
    name, ip = vm_name_dict[action.vm]
    data = {
      'name': action.container,
      'cpu_cores': action.cpu_cores,
      'mem_units': action.mem_units
    }

    arr = action.container.split('_', 1)
    app_name = arr[0]
    tier_name = arr[1]
    hosts = get_hosts(app_name, tier_name, topology, new_allocation, vm_name_dict)
    if len(hosts):
      data['hosts'] = hosts

    url = 'http://{}:8000/api/docker/run'.format(ip)
    r = requests.put(url, data=json.dumps(data), timeout=60)
  elif action.action_type == action_type['update_container']:
    name, ip = vm_name_dict[action.vm]
    data = {
      'name': action.container,
      'cpu_cores': action.cpu_cores,
      'mem_units': action.mem_units
    }
    url = 'http://{}:8000/api/docker/update'.format(ip)
    r = requests.put(url, data=json.dumps(data), timeout=60)
  elif action.action_type == action_type['delete_container']:
    name, ip = vm_name_dict[action.vm]
    data = {
      'name': action.container
    }
    url = 'http://{}:8000/api/docker'.format(ip)
    r = requests.delete(url, data=json.dumps(data), timeout=60)
  elif action.action_type == action_type['delete_vm']:
    autoscaling_group = topology['infrastructure']['cloud_driver']['autoscaling_groupname']
    vm_name = action.vm
    aws_driver.remove_vm(vm_name, autoscaling_group)
  elif action.action_type == action_type['run_tier_hooks']:
    name, ip = vm_name_dict[action.vm]
    data = {
      'tier': action.container,
      'old_allocation': prev_allocation,
      'new_allocation': result_allocation
    }
    url = 'http://{}:8000/api/run/tier_hook'.format(ip)
    r = requests.delete(url, data=json.dumps(data), timeout=60)
  logging.debug('-- End run action: {}'.format(action.__str__()))