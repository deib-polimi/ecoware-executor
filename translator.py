#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import topologyManager
from constraint import *
from action import ActionType, Action

DELIMETER = '_$_'

class Translator:

  def translate(self, plan_json, topology):
    solutions = self._solve_csp(plan_json, topology)
    allocations = self._parse_solutions(solutions)
    if len(allocations) == 0:
      print "No solutions found"
      return
    return self._allocations2plans(allocations, topology)[0]

  def _allocations2plans(self, allocations, topology):
    plans = []
    for allocation in allocations:
      plans.append(self._allocation2plan(allocation, topology))
    return plans

  def _allocation2plan(self, new_allocation, topology):
    result = []
    for vm_key in topology:
      if 'used' in topology[vm_key]:
        used = topology[vm_key]['used']
        if not vm_key in new_allocation:
          action = Action(ActionType.delete, vm_key)
        else:
          for app_key in used:
            if not app_key in new_allocation[vm_key]:
              action = Action(ActionType.delete, vm_key, app_key)

    for vm_key in new_allocation:
      if vm_key == 'estimation': continue
      apps = new_allocation[vm_key]
      for app_key in apps:
        demand = apps[app_key]
        if 'used' in topology[vm_key] and app_key in topology[vm_key]['used']:
          action = Action(ActionType.modify, vm_key, app_key, demand['cpu_cores'], demand['mem'])
        else:
          action = Action(ActionType.create, vm_key, app_key, demand['cpu_cores'], demand['mem'])
          result.append(action)
    return result


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
      problem.addConstraint(ExactSumConstraint(demand['cpu_cores']), tier_cpu_vars[tier])
      problem.addConstraint(ExactSumConstraint(demand['mem']), tier_mem_vars[tier])

    return problem.getSolutions()

  def _parse_solution(self, solution):
    vms = {}
    for key, value in solution.iteritems():
      if value == 0: continue
      arr = key.split(DELIMETER)
      vm_key = arr[0]
      vm = vms.setdefault(vm_key, {})
      tier_key = arr[1]
      tier = vm.setdefault(tier_key, {})
      resource = arr[2]
      if resource == 'cpu_cores':
        tier['cpu_cores'] = value
      else:
        tier['mem'] = value
    return vms

  def _parse_solutions(self, solutions):
    results = []
    for solution in solutions:
      results.append(self._parse_solution(solution))
    return results


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
  print json.dumps(string_actions, indent=2)
  print topologyManager.preview(actions)

if __name__ == '__main__':
  main()