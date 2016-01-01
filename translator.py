#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import topologyManager
from constraint import *
from action import ActionType, Action


DELIMETER = '_$_'

WEIGHT = {
  'container_set': 1,
  'container_delete': 4,
  'container_create': 8,
  'vm_delete': 20,
  'vm_create': 30,
  'cpu_use': 2,
  'mem_use': 2,
  'vm_use': 25
}

class Translator:

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
            if (topology[vm]['used']['cpu_cores'] == allocation[vm][tier]['cpu_cores']
                  and topology[vm]['used']['mem'] == allocation[vm][tier]['mem']):
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
      for tier in allocation[vm]:
        points += allocation[vm][tier]['cpu_cores'] * WEIGHT['cpu_use']
        points += allocation[vm][tier]['mem'] * WEIGHT['mem_use']
    return points

  def _2plan(self, allocation, topology):
    points = 0
    actions = []
    for vm in allocation:
      if not 'used' in topology[vm]:
        actions.append(Action(ActionType.vm_create, vm, None, topology[vm]['cpu_cores'], topology[vm]['mem']))
        for tier in allocation[vm]:
          actions.append(Action(ActionType.container_create, vm, tier, allocation[vm][tier]['cpu_cores'], allocation[vm][tier]['mem']))
      else:
        for tier in allocation[vm]:
          if tier in topology[vm]['used']:
            if (topology[vm]['used'][tier]['cpu_cores'] == allocation[vm][tier]['cpu_cores']
                  and topology[vm]['used'][tier]['mem'] == allocation[vm][tier]['mem']):
                pass
            else:
              actions.append(Action(ActionType.container_set, vm, tier, allocation[vm][tier]['cpu_cores'], allocation[vm][tier]['mem']))
          else:
            actions.append(Action(ActionType.container_create, vm, tier, allocation[vm][tier]['cpu_cores'], allocation[vm][tier]['mem']))
    for vm in topology:
      if not vm in allocation:
        points += WEIGHT['container_delete']
      elif 'used' in topology[vm]:
        for tier in topology[vm]['used']:
          if not tier in allocation[vm]:
            points += WEIGHT['container_delete']
    for vm in allocation:
      points += WEIGHT['vm_use']
      for tier in allocation[vm]:
        points += allocation[vm][tier]['cpu_cores'] * WEIGHT['cpu_use']
        points += allocation[vm][tier]['mem'] * WEIGHT['mem_use']
    return actions

  def translate(self, plan_json, topology):
    if self.need_solution(plan_json, topology):
      solutions = self._solve_csp(plan_json, topology)
      estimated = []
      for solution in solutions:
        allocation = self._2allocation(topology, solution)
        estimation = self._estimate(topology, allocation)
        plan = self._2plan(allocation, topology)
        estimated.append([estimation, allocation, plan])
      estimated = sorted(estimated, key=lambda x: x[0])
      actions = estimated[0][2]
      return actions
    else:
      return []

  def need_solution(self, plan_json, topology):
    demand = {}
    for vm in topology:
      if 'used' in topology[vm]:
        for app in topology[vm]['used']:
          if not app in demand:
            demand[app] = {}
            demand[app]['cpu_cores'] = 0
            demand[app]['mem'] = 0
          demand[app]['cpu_cores'] += topology[vm]['used'][app]['cpu_cores']
          demand[app]['mem'] += topology[vm]['used'][app]['mem']
    for app in plan_json:
      if (not app in demand or 
          plan_json[app]['cpu_cores'] != demand[app]['cpu_cores'] or
          plan_json[app]['mem'] != demand[app]['mem']):
        return True
    return False

  def _solve_csp(self, plan, topology):
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
        mem_var = '{0}{2}{1}{2}mem'.format(vm, tier, DELIMETER)
        
        # variables grouped by VM
        vm_cpu_vars.append(cpu_var)
        vm_mem_vars.append(mem_var)

        # variables grouped by Tier
        cpu_vars.append(cpu_var)
        mem_vars.append(mem_var)

        problem.addVariable(cpu_var, range(0, limit['cpu_cores'] + 1))
        problem.addVariable(mem_var, range(0, limit['mem'] + 1))

        # activation cpu <-> ram
        problem.addConstraint(lambda cpu, mem: 
          cpu * 1000 >= mem and mem * 1000 >= cpu, 
          (cpu_var, mem_var))

      problem.addConstraint(MaxSumConstraint(limit['cpu_cores']), vm_cpu_vars)
      problem.addConstraint(MaxSumConstraint(limit['mem']), vm_mem_vars)

    for tier, demand in plan.iteritems():
      problem.addConstraint(MinSumConstraint(demand['cpu_cores']), tier_cpu_vars[tier])
      problem.addConstraint(MinSumConstraint(demand['mem']), tier_mem_vars[tier])

    return problem.getSolutions()


def read_plan(filename):
  plan = {}
  with open(filename, 'r') as f:
    read_data = f.read()
    plan = json.loads(read_data)
  f.closed
  return plan

def main():
  translator = Translator()
  plan = read_plan('plan.json')
  actions = translator.translate(plan, topologyManager.get_current())
  string_actions = map(lambda x: x.__str__(), actions)
  print 'plan=', plan
  print 'topology=', topologyManager.get_current()
  print json.dumps(string_actions, indent=2)

if __name__ == '__main__':
  main()