import threading
import copy
import logging
import requests
import json
from sets import Set
from itertools import islice

import topology as mod_topology
import dependencyGraph
import executor
from action import VmAction, ContainerAction, TierHookAction, action_type

lock = threading.RLock()

_actions = {}

def add_action(action, prev_allocation):
  with lock:
    if not action.vm in _actions:
      _actions[action.vm] = {}
    _actions[action.vm][action.container] = action
  proceed(prev_allocation)

def proceed(prev_allocation):
  global _actions
  allocation = mod_topology.get_allocation()
  for vm_name, vm in allocation.iteritems():
    for container_name in vm['used']:
      if not vm_name in _actions or not container_name in _actions[vm_name]:
        return

  vm_map = {}
  with lock:
    vm_map = copy.deepcopy(_actions)
    _actions = {}

  actions = []
  for vm_name, vm in vm_map.iteritems():
    tiers = []
    for container_name, action in vm.iteritems():
      actions.append(action)
      if action.action_type == action_type['update_container']:
        cpu_cores = prev_allocation[vm_name]['used'][container_name]['cpu_cores']
        mem_units = prev_allocation[vm_name]['used'][container_name]['mem_units']
        if action.cpu_cores != cpu_cores or action.mem_units != mem_units:
          tiers.append(action.container)
      elif action.action_type == action_type['delete_container']:
        tiers.append(action.container)
    ip = prev_allocation[vm_name]['ip']
    url = 'http://{}:8000/api/cpuset/release'.format(ip)
    r = requests.put(url, data=json.dumps(tiers), timeout=10)
    logging.debug('Release cpuset on {} for tiers {}; response={}'.format(ip, tiers, r.text))

  new_allocation = copy.deepcopy(prev_allocation)
  for action in actions:
    if action.action_type == action_type['delete_container']:
      del new_allocation[action.vm]['used'][action.container]
    elif action.action_type == action_type['create_container']:
      new_allocation[action.vm]['used'][action.container] = {
        'cpu_cores': action.cpu_cores,
        'mem_units': action.mem_units
      }
    elif action.action_type == action_type['update_container']:
      new_allocation[action.vm]['used'][action.container]['cpu_cores'] = action.cpu_cores
      new_allocation[action.vm]['used'][action.container]['mem_units'] = action.mem_units
    else:
      raise Exception('Unknow action=' + str(action))

  actions = ordered(actions)
  actions = insert_tier_hooks_actions(actions)
  logging.debug('Actions: }' + str(map(lambda x: map(str, x), actions)))
  topology = mod_topology.get_topology()
  executor.aws_execute(actions, new_allocation, topology, prev_allocation)
  mod_topology.set_allocation(new_allocation)

def get_status():
  result = {}
  allocation = mod_topology.get_allocation()
  for vm_name, vm in allocation.iteritems():
    for container_name in vm['used']:
      if not vm_name in result:
        result[vm_name] = {}
      if not vm_name in _actions:
        result[vm_name][container_name] = False
      elif not container_name in _actions[vm_name]:
        result[vm_name][container_name] = False
      else:
        result[vm_name][container_name] = str(_actions[vm_name][container_name])
  for vm_name, vm in _actions.iteritems():
    for container_name, action in vm.iteritems():
      result[vm_name][container_name] = str(action)
  return result

def ordered(actions):
  flat_topology = mod_topology.get_flatten_topology()
  order = dependencyGraph.get_ordered_list(flat_topology)

  result = []
  for sub_list in order:
    current = []
    for action in actions:
      tier_name = action.container
      for order_tier in sub_list:
        if tier_name == order_tier:
          current.append(action)
    if len(current):
      result.append(current)
  return result


def insert_tier_hooks_actions(actions):
  flat_topology = mod_topology.get_flatten_topology()
  changed = Set()
  for action_list in actions:
    for action in action_list:
      if isinstance(action, ContainerAction):
        changed.add(action.container)

  actions_copy = islice(actions, 0, None)
  for action_list in actions_copy:
    for action in action_list:
      if isinstance(action, ContainerAction):
        for tier_name in flat_topology:
          if tier_name == action.container:
            tier_info = flat_topology[tier_name]
            tier_hook = tier_info.get('on_dependency_scale', None)
            if tier_hook:
              dependencies = tier_info.get('depends_on', [])
              for dependency in dependencies:
                if (dependency in changed and 
                    (action.action_type == action_type['create_container'] or action.action_type == action_type['update_container'])):
                  i = actions.index(action_list)
                  tier_hook_action = TierHookAction(action.vm, action.container)
                  next_list = []
                  if len(actions) > i+1:
                    next_list = actions[i+1]
                  else:
                    actions.append(next_list)
                  next_list.append(tier_hook_action)
                  break
  return actions