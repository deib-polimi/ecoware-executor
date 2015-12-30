#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import topologyManager
from constraint import *
from ortools.linear_solver import pywraplp
from action import ActionType, Action


DELIMETER = '_$_'

class Translator:

  def translate(self, plan_json, topology):
    if self.need_solution(plan_json, topology):
      allocation = self._solve_ilp(plan_json, topology)
      if not allocation:
        return None
      return self._allocation2plan(allocation, topology)
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

  def _allocation2plan(self, new_allocation, topology):
    result = []
    for vm_key in topology:
      if 'used' in topology[vm_key]:
        used = topology[vm_key]['used']
        if not vm_key in new_allocation:
          for app_key in used:
            action = Action(ActionType.delete, vm_key, app_key)
            result.append(action)
        else:
          for app_key in used:
            if not app_key in new_allocation[vm_key]:
              action = Action(ActionType.delete, vm_key, app_key)
              result.append(action)

    for vm_key in new_allocation:
      apps = new_allocation[vm_key]
      for app_key in apps:
        demand = apps[app_key]
        if 'used' in topology[vm_key] and app_key in topology[vm_key]['used']:
          if (topology[vm_key]['used'][app_key]['cpu_cores'] != demand['cpu_cores'] or
            topology[vm_key]['used'][app_key]['mem'] != demand['mem']):
            action = Action(ActionType.modify, vm_key, app_key, demand['cpu_cores'], demand['mem'])
            result.append(action)
        else:
          action = Action(ActionType.create, vm_key, app_key, demand['cpu_cores'], demand['mem'])
          result.append(action)
    return result


  def _solve_ilp(self, plan, topology):
    solver = pywraplp.Solver('Solver', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # variables
    usage = {}
    cpu = {}
    mem = {}
    # MIN_RAM = 0.5
    for vm in topology:
      cpu[vm] = {}
      mem[vm] = {}
      usage[vm] = {}
      for tier in plan:
        cpu[vm][tier] = solver.IntVar(0, solver.infinity(), 'cpu_{0}_{1}'.format(vm, tier))
        mem[vm][tier] = solver.IntVar(0, solver.infinity(), 'mem_{0}_{1}'.format(vm, tier))
        usage[vm][tier] = solver.BoolVar('used_{0}_{1}'.format(vm, tier))

    objective = solver.Objective()
    for vm in topology:
      for tier in plan:
        weight = 5 # w(vm_use)
        if 'used' in topology[vm]:
          if tier in topology[vm]['used']:
            weight = 1 # w(container_set)
          else:
            
        else:
          k1 = 20
          k2 = 3
        objective.SetCoefficient(usage[vm][tier], k1)
    objective.SetMinimization()

    for vm in topology:
      cpu_availability = solver.Constraint(0, topology[vm]['cpu_cores'])
      mem_availability = solver.Constraint(0, topology[vm]['mem'])
      for tier in plan:
        cpu_availability.SetCoefficient(cpu[vm][tier], 1)

        mem_availability.SetCoefficient(mem[vm][tier], 1)

        used_cpu_activation = solver.Constraint(0, solver.infinity())
        used_cpu_activation.SetCoefficient(cpu[vm][tier], -1)
        used_cpu_activation.SetCoefficient(usage[vm][tier], topology[vm]['cpu_cores'])

        used_mem_activation = solver.Constraint(0, solver.infinity())
        used_mem_activation.SetCoefficient(mem[vm][tier], -1)
        used_mem_activation.SetCoefficient(usage[vm][tier], topology[vm]['mem'])

        cpu_ram_activation = solver.Constraint(0, solver.infinity())
        cpu_ram_activation.SetCoefficient(mem[vm][tier], -1)
        cpu_ram_activation.SetCoefficient(cpu[vm][tier], topology[vm]['mem'])

        ram_cpu_activation = solver.Constraint(0, solver.infinity())
        ram_cpu_activation.SetCoefficient(cpu[vm][tier], -1)
        ram_cpu_activation.SetCoefficient(mem[vm][tier], topology[vm]['cpu_cores'])

        # min_ram = solver.Constraint(0, solver.infinity())
        # min_ram.SetCoefficient(mem[vm][tier], 1)
        # min_ram.SetCoefficient(used[vm][tier], -MIN_RAM)
      
    for tier in plan:
      cpu_demand = solver.Constraint(plan[tier]['cpu_cores'], plan[tier]['cpu_cores'])
      mem_demand = solver.Constraint(plan[tier]['mem'], plan[tier]['mem'])
      for vm in topology:
        cpu_demand.SetCoefficient(cpu[vm][tier], 1)
        mem_demand.SetCoefficient(mem[vm][tier], 1)

    status = solver.Solve()
    allocation = {}
    for vm in topology:
      for tier in plan:
        # print '{0}={1} cpu={2} mem={3}'.format(usage[vm][tier], usage[vm][tier].solution_value(), cpu[vm][tier].solution_value(), mem[vm][tier].solution_value())
        if usage[vm][tier].solution_value() > 0:
          allocation.setdefault(vm, {})
          allocation[vm].setdefault(tier, {})
          allocation[vm][tier]['cpu_cores'] = cpu[vm][tier].solution_value()
          allocation[vm][tier]['mem'] = mem[vm][tier].solution_value()
    return allocation

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