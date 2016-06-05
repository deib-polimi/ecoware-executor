#!/usr/bin/python
import time
import logging
import requests
import json
from threading import Thread

import aws_driver
from action import action_type, VmAction, ContainerAction

def get_hosts(app_name, tier_name, topology, allocation):
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
    for vm_name, vm in allocation.iteritems():
      ip = vm['ip']
      for item in vm['used']:
        if item == full_name:
          result.append(host + ':' + ip)
  return result

def aws_execute(actions, new_allocation, topology, prev_allocation):
  for action_list in actions:
    threads = []

    for action in action_list:
      thread = Thread(target=threaded_run_action, args=(action, topology, new_allocation, prev_allocation))
      threads.append(thread)
      thread.start()

    for thread in threads:
      thread.join()

  return new_allocation

def threaded_run_action(action, topology, new_allocation, prev_allocation):
  logging.debug('Start run action: {}'.format(action.__str__()))
  if action.action_type == action_type['create_container']:
    ip = new_allocation[action.vm]['ip']
    data = {
      'name': action.container,
      'cpu_cores': action.cpu_cores,
      'mem_units': action.mem_units
    }

    arr = action.container.split('_', 1)
    app_name = arr[0]
    tier_name = arr[1]
    hosts = get_hosts(app_name, tier_name, topology, new_allocation)
    if len(hosts):
      data['hosts'] = hosts

    url = 'http://{}:8000/api/docker/run'.format(ip)
    r = requests.put(url, data=json.dumps(data), timeout=60)
    resp_json = json.loads(r.text)
    if 'error' in resp_json:
      logging.error('action={}; resp_json={}'.format(str(action), resp_json['error']))
  elif action.action_type == action_type['update_container']:
    ip = new_allocation[action.vm]['ip']
    data = {
      'name': action.container,
      'cpu_cores': action.cpu_cores,
      'mem_units': action.mem_units
    }
    url = 'http://{}:8000/api/docker/update'.format(ip)
    r = requests.put(url, data=json.dumps(data), timeout=60)
    resp_json = json.loads(r.text)
    if 'error' in resp_json:
      logging.error('action={}; resp_json={}'.format(str(action), resp_json['error']))
  elif action.action_type == action_type['delete_container']:
    ip = new_allocation[action.vm]['ip']
    data = {
      'name': action.container
    }
    url = 'http://{}:8000/api/docker'.format(ip)
    r = requests.delete(url, data=json.dumps(data), timeout=60)
    resp_json = json.loads(r.text)
    if 'error' in resp_json:
      logging.error('action={}; resp_json={}'.format(str(action), resp_json['error']))
  elif action.action_type == action_type['delete_vm']:
    autoscaling_group = topology['infrastructure']['cloud_driver']['autoscaling_groupname']
    vm_name = action.vm
    aws_driver.remove_vm(vm_name, autoscaling_group)
  elif action.action_type == action_type['run_tier_hooks']:
    ip = new_allocation[action.vm]['ip']
    data = {
      'tier': action.container,
      'old_allocation': prev_allocation,
      'new_allocation': new_allocation
    }
    url = 'http://{}:8000/api/run/tier_hook'.format(ip)
    r = requests.post(url, data=json.dumps(data), timeout=60)
    resp_json = json.loads(r.text)
    if 'error' in resp_json:
      logging.error('action={}; resp_json={}'.format(str(action), resp_json['error']))
  logging.debug('-- End run action: {}'.format(action.__str__()))