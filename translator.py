#/usr/bin/python

import sys
from sets import Set
from itertools import islice
from operator import attrgetter

import dependencyGraph
from action import VmAction, ContainerAction, TierHookAction, action_type

def translate(current_allocation, new_allocation, flat_topology):
  actions = []
  for vm in current_allocation:
    if vm in new_allocation:
      for container in current_allocation[vm]['used']:
        if not container in new_allocation[vm]:
          action = ContainerAction(action_type['delete_container'], vm, container)
          actions.append(action)
    else:
      action = VmAction(action_type['delete_vm'], vm)
      actions.append(action)

  for vm in new_allocation:
    if vm in current_allocation:
      for container in new_allocation[vm]:
        cpu = new_allocation[vm][container]['cpu_cores']
        mem = new_allocation[vm][container]['mem_units']
        if container in current_allocation[vm]['used']:
          current_container = current_allocation[vm]['used'][container]
          if (current_container['cpu_cores'] != cpu or
                current_container['mem_units'] != mem):
            action = ContainerAction(action_type['update_container'], vm, container, cpu, mem)
            actions.append(action)
        else:
          action = ContainerAction(action_type['create_container'], vm, container, cpu, mem)
          actions.append(action)
    else:
      action = VmAction(action_type['create_vm'], vm)
      actions.append(action)
      for container in new_allocation[vm]:
        cpu = new_allocation[vm][container]['cpu_cores']
        mem = new_allocation[vm][container]['mem_units']
        action = ContainerAction(action_type['create_container'], vm, container, cpu, mem)
        actions.append(action)
  print map(str, actions)
  actions = ordered(actions, flat_topology)
  actions = insert_tier_hooks_actions(actions, flat_topology)
  return actions

def insert_tier_hooks_actions(actions, flat_topology):
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

def ordered(actions, flat_topology):
  order = dependencyGraph.get_ordered_list(flat_topology)

  first = []
  last = []

  for action in actions:
    if action.action_type == action_type['create_vm']:
      first.append(action)
    elif action.action_type == action_type['delete_vm']:
      last.append(action)

  result = []
  if len(first):
    result.append(first)
  for sub_list in order:
    current = []
    for action in actions:
      if isinstance(action, ContainerAction):
        tier_name = action.container
        for order_tier in sub_list:
          if tier_name == order_tier:
            current.append(action)
    if len(current):
      result.append(current)
  if len(last):
    result.append(last)
  return result
  

if __name__ == '__main__':
  current_allocation = {
    'vm0': {
      'used': {
        'jboss': {
          'cpu_cores': 1,
          'mem_units': 1
        }
      }
      
    },
    'vm1': {
      'used': {
        'jboss': {
          'cpu_cores': 1,
          'mem_units': 1,
        },
        'db': {
          'cpu_cores': 1,
          'mem_units': 1
        }
      }
    },
    'vm2': {
      'used': {
        'jboss':{
          'cpu_cores': 1,
          'mem_units': 1
        }
      }
    }
  }

  new_allocation = {
    'new_vm': {
      'jboss': {
        'cpu_cores': 2,
        'mem_units': 2
      }
    },
    'vm1': {
      'jboss': {
        'cpu_cores': 2,
        'mem_units': 2      
      },
      'load-balancer': {
        'cpu_cores': 1,
        'mem_units': 1
      }
    },
    'vm2': {
      'jboss':{
        'cpu_cores': 1,
        'mem_units': 1
      }
    }
  }

  flat_topology = {
    'jboss': {
      'depends_on': ['db'],
      'on_dependency_scale': 'qwert'
    },
    'db' : {},
    'load-balancer': {
      'depends_on': ['jboss']
    }
  }

  actions = translate(current_allocation, new_allocation, flat_topology)
  print map(lambda x: map(str, x), actions)