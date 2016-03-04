#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import copy
from math import ceil

import topologyManager
from constraint import *
from ortools.linear_solver import pywraplp
from action import ActionType, Action


DELIMETER = '_$_'

class MonoliticTranslator:

  def _init_vm(self, plan, topology):
    allocation = copy.deepcopy(topology)
    demand_cpu = 0
    demand_mem = 0
    for tier in plan:
      demand_cpu += plan[tier]['cpu_cores']
      demand_mem += plan[tier]['mem_units']
    vm_count = len(allocation)
    vm_cpu = 2
    vm_mem = 8
    resources_cpu = vm_cpu * vm_count
    resources_mem = vm_mem * vm_count
    if demand_cpu > resources_cpu or demand_mem > resources_mem:
      vm_add_count = int(ceil(max(1.0 *(demand_cpu - resources_cpu) / vm_cpu, 1.0 * (demand_mem - resources_mem) / vm_mem)))
      for i in range(0, vm_add_count):
        allocation['new_vm{}'.format(i)] = {
          'cpu_cores': vm_cpu,
          'mem_units': vm_mem
        }
    return allocation

  def translate(self, plan_json, topology):
    if self.need_solution(plan_json, topology):
      print 'need solution'
      if len(plan_json) == 0:
        allocation = {}
        return self._allocation2plan(allocation, topology) 
      topology = self._init_vm(plan_json, topology)
      temp = self._solve_ilp(plan_json, topology)
      allocation = self._solve_ilp(plan_json, topology)
      print 'new_allocation', allocation
      return self._allocation2plan(allocation, topology)
    else:
      allocation = {}
      print 'no need solution'
      return []

  def translate2allocation(self, plan_json, topology):
    if self.need_solution(plan_json, topology):
      print 'need solution'
      if len(plan_json) == 0:
        allocation = {}
        return allocation 
      topology = self._init_vm(plan_json, topology)
      print 'allocation', topology
      temp = self._solve_ilp(plan_json, topology)
      return self._solve_ilp(plan_json, topology)
    else:
      print 'no need solution'
      return topology

  def need_solution(self, plan_json, topology):
    if len(plan_json) == 0 and len(topology) != 0:
      return True
    demand = {}
    for vm in topology:
      if 'used' in topology[vm]:
        for app in topology[vm]['used']:
          if not app in plan_json:
            return True
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
    return False


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
          action = Action(ActionType.vm_delete, vm_key)
          result.append(action)
        else:
          for app_key in used:
            if not app_key in new_allocation[vm_key]:
              action = Action(ActionType.container_delete, vm_key, app_key)
              result.append(action)

    for vm_key in new_allocation:
      if vm_key.startswith('new_vm'):
        action = Action(ActionType.vm_create, vm_key, None, 2, 8)
        result.append(action)
      apps = new_allocation[vm_key]
      for app_key in apps:
        demand = apps[app_key]
        if 'used' in topology[vm_key] and app_key in topology[vm_key]['used']:
          if (topology[vm_key]['used'][app_key]['cpu_cores'] != demand['cpu_cores'] or
            topology[vm_key]['used'][app_key]['mem_units'] != demand['mem_units']):
            action = Action(ActionType.container_set, vm_key, app_key, demand['cpu_cores'], demand['mem_units'])
            result.append(action)
        else:
          action = Action(ActionType.container_create, vm_key, app_key, demand['cpu_cores'], demand['mem_units'])
          result.append(action)
    return result


  def _solve_ilp(self, plan, topology):
    solver = pywraplp.Solver('Solver', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # variables
    vm_usage = {}
    vm_idle = {}
    tier_usage = {}
    tier_idle = {}
    cpu = {}
    mem = {}
    for vm in topology:
      cpu[vm] = {}
      mem[vm] = {}
      vm_usage[vm] = solver.BoolVar('vm_usage_{0}'.format(vm))
      vm_idle[vm] = solver.BoolVar('vm_idle_{0}'.format(vm))
      tier_usage[vm] = {}
      tier_idle[vm] = {}
      for tier in plan:
        cpu[vm][tier] = solver.IntVar(0, solver.infinity(), 'cpu_{0}_{1}'.format(vm, tier))
        mem[vm][tier] = solver.IntVar(0, solver.infinity(), 'mem_{0}_{1}'.format(vm, tier))
        tier_usage[vm][tier] = solver.BoolVar('tier_usage_{0}_{1}'.format(vm, tier))
        tier_idle[vm][tier] = solver.BoolVar('tier_idle_{0}_{1}'.format(vm, tier))
    
    # wDockerDelete < wDockerSet <  < wDockerCreate < wVmDelete < wVmUse < wVmCreate
    wDockerDelete = 1
    wDockerSet = 2
    wDockerCreate = 3

    wVmDelete = 10
    wVmUse = 11
    wVmCreate = 20
    
    objective = solver.Objective()
    for vm in topology:
      if vm.startswith('new_vm'):
        objective.SetCoefficient(vm_usage[vm], wVmCreate)
      else:
        objective.SetCoefficient(vm_usage[vm], wVmUse)
        objective.SetCoefficient(vm_idle[vm], wVmDelete)

      for tier in plan:
        if 'used' in topology[vm]:
          if tier in topology[vm]['used']:
            objective.SetCoefficient(tier_usage[vm][tier], wDockerSet)
            objective.SetCoefficient(tier_idle[vm][tier], wDockerDelete)
          else: # new container
            objective.SetCoefficient(tier_usage[vm][tier], wDockerCreate)
        else:
          objective.SetCoefficient(tier_usage[vm][tier], wDockerCreate)
    objective.SetMinimization()

    for vm in topology:
      # sum{i in Tier} cpu[i, j] - cpu_max[j] * vm_usage[j] <= 0
      cpu_availability = solver.Constraint(-solver.infinity(), 0)
      mem_availability = solver.Constraint(-solver.infinity(), 0)
      cpu_availability.SetCoefficient(vm_usage[vm], -topology[vm]['cpu_cores'])
      mem_availability.SetCoefficient(vm_usage[vm], -topology[vm]['mem_units'])
      for tier in plan:
        cpu_availability.SetCoefficient(cpu[vm][tier], 1)

        mem_availability.SetCoefficient(mem[vm][tier], 1)

        # cpu_max[j] * tier_usage[i, j] - cpu[i, j] >= 0
        cpu_activation = solver.Constraint(0, solver.infinity())
        cpu_activation.SetCoefficient(tier_usage[vm][tier], topology[vm]['cpu_cores'])
        cpu_activation.SetCoefficient(cpu[vm][tier], -1)

        # mem_max[j] * tier_usage[i, j] - mem[i, j] >= 0
        ram_activation = solver.Constraint(0, solver.infinity())
        ram_activation.SetCoefficient(tier_usage[vm][tier], topology[vm]['mem_units'])
        ram_activation.SetCoefficient(mem[vm][tier], -1)

        # subject to CPU_RAM_activation{i in Tier, j in VM}:
        #   mem_max[j] * cpu[i, j] - mem[i, j] >= 0;
        cpu_ram_activation = solver.Constraint(0, solver.infinity())
        cpu_ram_activation.SetCoefficient(cpu[vm][tier], topology[vm]['mem_units'])
        cpu_ram_activation.SetCoefficient(mem[vm][tier], -1)

        # subject to RAM_CPU_activation{i in Tier, j in VM}:
          # cpu_max[j] * mem[i, j] - cpu[i, j] >= 0
        ram_cpu_activation = solver.Constraint(0, solver.infinity())
        ram_cpu_activation.SetCoefficient(mem[vm][tier], topology[vm]['cpu_cores'])
        ram_cpu_activation.SetCoefficient(cpu[vm][tier], -1)

        # link tier_idle to tier_usage
        # subject to link_tier_idle{i in Tier, j in VM}:
        #   tier_idle[i, j] + tier_usage[i, j] = 1;
        link_tier_idle = solver.Constraint(1, 1)
        link_tier_idle.SetCoefficient(tier_idle[vm][tier], 1)
        link_tier_idle.SetCoefficient(tier_usage[vm][tier], 1)

        # link vm_idle to vm_usage
        # subject to link_vm_idle{j in VM}:
        #   vm_idle[j] + vm_usage[j] = 1;
        link_vm_idle = solver.Constraint(1, 1)
        link_vm_idle.SetCoefficient(vm_idle[vm], 1)
        link_vm_idle.SetCoefficient(vm_usage[vm], 1)
      
    for tier in plan:
      # sum{j in VM} cpu[i, j] >= cpu_demand[i];
      cpu_demand = solver.Constraint(plan[tier]['cpu_cores'], solver.infinity())
      mem_demand = solver.Constraint(plan[tier]['mem_units'], solver.infinity())
      for vm in topology:
        cpu_demand.SetCoefficient(cpu[vm][tier], 1)
        mem_demand.SetCoefficient(mem[vm][tier], 1)

    status = solver.Solve()
    allocation = {}
    for vm in topology:
      for tier in plan:
        # print '{0}={1} cpu={2} mem={3}'.format(usage[vm][tier], usage[vm][tier].solution_value(), cpu[vm][tier].solution_value(), mem[vm][tier].solution_value())
        if tier_usage[vm][tier].solution_value() > 0:
          allocation.setdefault(vm, {})
          allocation[vm].setdefault(tier, {})
          allocation[vm][tier]['cpu_cores'] = cpu[vm][tier].solution_value()
          allocation[vm][tier]['mem_units'] = mem[vm][tier].solution_value()
    return allocation

def read_plan(filename):
  plan = {}
  with open(filename, 'r') as f:
    read_data = f.read()
    plan = json.loads(read_data)
  f.closed
  return plan

# def main():
#   translator = Translator()
#   plan = read_plan('plan.json')
#   actions = translator.translate(plan, topologyManager.get_current())
#   string_actions = map(lambda x: x.__str__(), actions)
#   print json.dumps(string_actions, indent=2)
#   print topologyManager.preview(actions)

# if __name__ == '__main__':
#   main()

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

  translator = MonoliticTranslator()
  actions = translator.tranate(plan, allocation)
  string_actions = map(lambda x: x.__str__(), actions)
  print 'plan=', plan
  print 'allocation=', allocation
  print json.dumps(string_actions, indent=2)

if __name__ == '__main__':
  main()