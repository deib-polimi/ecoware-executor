#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import topologyManager
from constraint import *
from action import ActionType, Action
from math import ceil
import time
import sys
import logging

DELIMETER = '_$_'

WEIGHT = {
  'container_set': 1,
  'container_delete': 4,
  'container_create': 8,
  'vm_delete': 20,
  'vm_create': 30,
  'vm_use': 25
}

class MonoliticTranslator:

  def __init__(self, default_cpu_cores, default_mem_units):
    self.default_cpu_cores = default_cpu_cores
    self.default_mem_units = default_mem_units

  def _2allocation(self, topology, solution):
    vms = {}
    for var in solution:
      arr = var.split('_$_')
      vm = arr[0]
      tier = arr[1]
      tiers = {}
      resource = arr[2]
      if solution[var] > 0:
        if vm in vms:
          tiers = vms[vm]
        else:
          vms[vm] = tiers
        resources = {}
        if tier in tiers:
          resources = tiers[tier]
        else:
          tiers[tier] = resources
        resources[resource] = solution[var]
    return vms

  def _estimate(self, topology, allocation):
    # container_set < container_delete < container_create < vm_delete < vm_create
    points = 0
    for vm in allocation:
      if not 'used' in topology[vm]:
        points += WEIGHT['vm_create']
        for tier in allocation[vm]:
          points += WEIGHT['container_create']
      else:
        for tier in allocation[vm]:
          if tier in topology[vm]['used']:
            if (topology[vm]['used'][tier]['cpu_cores'] == allocation[vm][tier]['cpu_cores']
                  and topology[vm]['used'][tier]['mem_units'] == allocation[vm][tier]['mem_units']):
                pass
            else:
              points += WEIGHT['container_set']
          else:
            points += WEIGHT['container_create']
    for vm in topology:
      if not vm in allocation:
        points += WEIGHT['container_delete']
      elif 'used' in topology[vm]:
        for tier in topology[vm]['used']:
          if not tier in allocation[vm]:
            points += WEIGHT['container_delete']
    for vm in allocation:
      points += WEIGHT['vm_use']
    return points

  def _2plan(self, allocation, topology):
    points = 0
    actions = []
    for vm in allocation:
      if not 'used' in topology[vm]:
        actions.append(Action(ActionType.vm_create, vm, None, topology[vm]['cpu_cores'], topology[vm]['mem_units']))
        for tier in allocation[vm]:
          actions.append(Action(ActionType.container_create, vm, tier, allocation[vm][tier]['cpu_cores'], allocation[vm][tier]['mem_units']))
      else:
        for tier in allocation[vm]:
          if tier in topology[vm]['used']:
            if (topology[vm]['used'][tier]['cpu_cores'] == allocation[vm][tier]['cpu_cores']
                  and topology[vm]['used'][tier]['mem_units'] == allocation[vm][tier]['mem_units']):
                pass
            else:
              actions.append(Action(ActionType.container_set, vm, tier, allocation[vm][tier]['cpu_cores'], allocation[vm][tier]['mem_units']))
          else:
            actions.append(Action(ActionType.container_create, vm, tier, allocation[vm][tier]['cpu_cores'], allocation[vm][tier]['mem_units']))
    for vm in topology:
      if 'used' in topology[vm]:
        if not vm in allocation:
          actions.append(Action(ActionType.vm_delete, vm))
        else:
          for tier in topology[vm]['used']:
            if not tier in allocation[vm]:
              actions.append(Action(ActionType.container_delete, vm, tier))

    return actions

  def translate(self, plan_json, topology):
    if self.need_solution(plan_json, topology):
      start = time.time()
      solutions = self._solve_csp(plan_json, topology)
      print 'solver: size={}; time={}sec'.format(len(solutions), time.time() - start)
      if len(solutions) == 0:
        raise Exception('No solution found')
      best = None
      best_estimation = sys.maxint
      start = time.time()
      for solution in solutions:
        allocation = self._2allocation(topology, solution)
        estimation = self._estimate(topology, allocation)
        if estimation < best_estimation:
          best = allocation
          best_estimation = estimation
      print 'search best: time={}sec'.format(time.time() - start)
      def comparator(action0, action1):
        def action2order(action):
          if action.type == ActionType.vm_delete or action.type == ActionType.container_delete:
            return 0 
          elif action.type == ActionType.container_set:
            return 1
          elif action.type == ActionType.vm_create:
            return 2
          else:
            return 3
        action0 = action2order(action0)
        action1 = action2order(action1)
        return action0 - action1
      plan = self._2plan(best, topology)
      actions = sorted(plan, comparator)
      return actions
    else:
      logging.debug('no solution needed')
      actions = []
      for vm in topology:
        is_used = False
        for app in plan_json:
          if app in topology[vm]['used']:
            is_used = True
            break
        if not is_used:
          actions.append(Action(ActionType.vm_delete, vm))
      return actions

  def need_solution(self, plan_json, topology):
    demand = {}
    for vm in topology:
      if 'used' in topology[vm]:
        for app in topology[vm]['used']:
          if not app in demand:
            demand[app] = {}
            demand[app]['cpu_cores'] = 0
            demand[app]['mem_units'] = 0
          demand[app]['cpu_cores'] += topology[vm]['used'][app]['cpu_cores']
          demand[app]['mem_units'] += topology[vm]['used'][app]['mem_units']
    for app in plan_json:
      if (not app in demand or 
          plan_json[app]['cpu_cores'] != demand[app]['cpu_cores'] or
          plan_json[app]['mem_units'] != demand[app]['mem_units']):
        return True
    for app in demand:
      if not app in plan_json:
        plan_json[app] = {}
        plan_json[app]['cpu_cores'] = 0
        plan_json[app]['mem_units'] = 0
        return True
    return False

  def _init_vm(self, plan, allocation):
    demand_cpu = 0
    demand_mem = 0
    for tier in plan:
      demand_cpu += plan[tier]['cpu_cores']
      demand_mem += plan[tier]['mem_units']
    vm_count = len(allocation)
    vm_cpu_cores = self.default_cpu_cores
    vm_mem_units = self.default_mem_units
    resources_cpu = vm_cpu_cores * vm_count
    resources_mem = vm_mem_units * vm_count
    if demand_cpu > resources_cpu or demand_mem > resources_mem:
      vm_add_count = int(ceil(max(1.0 *(demand_cpu - resources_cpu) / vm_cpu_cores, 1.0 * (demand_mem - resources_mem) / vm_mem_units)))
      for i in range(0, vm_add_count):
        allocation['new_vm{}'.format(i)] = {
          'cpu_cores': vm_cpu_cores,
          'mem_units': vm_mem_units
        }
    logging.debug('allocation={}'.format(allocation))
    return allocation


  def _solve_csp(self, plan, topology):
    topology = self._init_vm(plan, topology)
    problem = Problem()
    tier_cpu_vars = {}
    tier_mem_vars = {}
    for vm, limit in topology.iteritems():
      vm_cpu_vars = []
      vm_mem_vars = []
      for tier in plan:
        cpu_vars = tier_cpu_vars.setdefault(tier, [])
        mem_vars = tier_mem_vars.setdefault(tier, [])
        cpu_var = '{0}{2}{1}{2}cpu_cores'.format(vm, tier, DELIMETER)
        mem_var = '{0}{2}{1}{2}mem_units'.format(vm, tier, DELIMETER)
        
        # variables grouped by VM
        vm_cpu_vars.append(cpu_var)
        vm_mem_vars.append(mem_var)

        # variables grouped by Tier
        cpu_vars.append(cpu_var)
        mem_vars.append(mem_var)

        problem.addVariable(cpu_var, range(0, limit['cpu_cores'] + 1))
        problem.addVariable(mem_var, range(0, limit['mem_units'] + 1))

        # activation cpu <-> ram
        problem.addConstraint(lambda cpu, mem: 
          cpu * 1000 >= mem and mem * 1000 >= cpu, 
          (cpu_var, mem_var))

      problem.addConstraint(MaxSumConstraint(limit['cpu_cores']), vm_cpu_vars)
      problem.addConstraint(MaxSumConstraint(limit['mem_units']), vm_mem_vars)

    for tier, demand in plan.iteritems():
      problem.addConstraint(ExactSumConstraint(demand['cpu_cores']), tier_cpu_vars[tier])
      problem.addConstraint(ExactSumConstraint(demand['mem_units']), tier_mem_vars[tier])
    solutions = problem.getSolutions()
    return solutions


def read_plan(filename):
  plan = {}
  with open(filename, 'r') as f:
    read_data = f.read()
    plan = json.loads(read_data)
  f.closed
  return plan



def main():
  logging.basicConfig(level=logging.DEBUG)
  topology = {
    "app": {
      "vm_cpu_cores": 2,
      "tiers": {
        "jboss": {
          "image": "httpd"
        },
        "db": {
          "image": "nginx"
        }
      },
      "vm_mem_units": 8,
      "name": "Ecoware",
      "auto_scale_group_name": "ex3"
    }
  }

  plan = {
    "jboss": {
      "cpu_cores": 1,
      "mem_units": 3
    },
    "db": {
      "cpu_cores": 2,
      "mem_units": 2
    }
  }
  
  allocation = {}

  translator = MonoliticTranslator(topology['app']['vm_cpu_cores'], topology['app']['vm_mem_units'])
  
  actions = translator.translate(plan, allocation)
  string_actions = map(lambda x: x.__str__(), actions)
  print 'plan=', plan
  print 'allocation=', allocation
  print json.dumps(string_actions, indent=2)

if __name__ == '__main__':
  main()