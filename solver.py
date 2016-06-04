#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import copy
from math import ceil
from ortools.linear_solver import pywraplp

DELIMETER = '_$_'

class AllocationSolver:

  def __init__(self, topology):
    self.topology = topology

  def _init_vm(self, plan, allocation):
    allocation = copy.deepcopy(allocation)
    demand_cpu = 0
    demand_mem = 0
    for tier in plan:
      demand_cpu += plan[tier]['cpu_cores']
      demand_mem += plan[tier]['mem_units']
    vm_count = len(allocation)
    vm_cpu = self.topology['infrastructure']['cpu_cores']
    vm_mem = self.topology['infrastructure']['mem_units']
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

  def solve(self, plan_json, allocation, no_scale_arr=[]):
    if self.need_solution(plan_json, allocation):
      logging.debug('need solution')
      if len(plan_json) == 0:
        return {}
      new_allocation = self._init_vm(plan_json, allocation)
      logging.debug('VM upper bound; new_allocation={}'.format(new_allocation))
      return self._solve_ilp(plan_json, new_allocation, no_scale_arr)
    raise Exception('No solution needed')

  def need_solution(self, plan_json, allocation):
    if len(plan_json) == 0 and len(allocation) != 0:
      return True
    demand = {}
    for vm in allocation:
      if 'used' in allocation[vm]:
        for app in allocation[vm]['used']:
          if not app in plan_json:
            return True
          if not app in demand:
            demand[app] = {}
            demand[app]['cpu_cores'] = 0
            demand[app]['mem_units'] = 0
          demand[app]['cpu_cores'] += allocation[vm]['used'][app]['cpu_cores']
          demand[app]['mem_units'] += allocation[vm]['used'][app]['mem_units']
    for app in plan_json:
      if (not app in demand or 
          plan_json[app]['cpu_cores'] != demand[app]['cpu_cores'] or
          plan_json[app]['mem_units'] != demand[app]['mem_units']):
        return True
    return False


  def _solve_ilp(self, plan, allocation, no_scale_arr=[]):
    logging.debug('Not scalable tiers: ' + str(no_scale_arr))
    solver = pywraplp.Solver('Solver', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # variables
    vm_usage = {}
    vm_idle = {}
    tier_usage = {}
    tier_idle = {}
    cpu = {}
    mem = {}
    for vm in allocation:
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
    
    # wDockerDelete < wDockerSet << wDockerCreate < wVmDelete < wVmUse < wVmCreate
    wDockerDelete = 1
    wVmDelete = 2
    wDockerSet = 3
    wDockerCreate = 4

    wVmUse = 11
    wVmCreate = 20

    wNotScalableDelete = 100
    
    objective = solver.Objective()
    for vm in allocation:
      if vm.startswith('new_vm'):
        objective.SetCoefficient(vm_usage[vm], wVmCreate)
      else:
        objective.SetCoefficient(vm_usage[vm], wVmUse)
        objective.SetCoefficient(vm_idle[vm], wVmDelete)

      for tier in plan:
        if 'used' in allocation[vm]:
            if tier in allocation[vm]['used']:
              if tier in no_scale_arr:
                objective.SetCoefficient(tier_usage[vm][tier], wDockerSet)
                objective.SetCoefficient(tier_idle[vm][tier], wNotScalableDelete)  
              else:
                objective.SetCoefficient(tier_usage[vm][tier], wDockerSet)
                objective.SetCoefficient(tier_idle[vm][tier], wDockerDelete)
            else: # new container
              objective.SetCoefficient(tier_usage[vm][tier], wDockerCreate)
        else:
          objective.SetCoefficient(tier_usage[vm][tier], wDockerCreate)
    objective.SetMinimization()

    for vm in allocation:
      # sum{i in Tier} cpu[i, j] - cpu_max[j] * vm_usage[j] <= 0
      cpu_availability = solver.Constraint(-solver.infinity(), 0)
      mem_availability = solver.Constraint(-solver.infinity(), 0)
      cpu_availability.SetCoefficient(vm_usage[vm], -allocation[vm]['cpu_cores'])
      mem_availability.SetCoefficient(vm_usage[vm], -allocation[vm]['mem_units'])
      for tier in plan:
        cpu_availability.SetCoefficient(cpu[vm][tier], 1)

        mem_availability.SetCoefficient(mem[vm][tier], 1)

        # cpu_max[j] * tier_usage[i, j] - cpu[i, j] >= 0
        cpu_activation = solver.Constraint(0, solver.infinity())
        cpu_activation.SetCoefficient(tier_usage[vm][tier], allocation[vm]['cpu_cores'])
        cpu_activation.SetCoefficient(cpu[vm][tier], -1)

        # mem_max[j] * tier_usage[i, j] - mem[i, j] >= 0
        ram_activation = solver.Constraint(0, solver.infinity())
        ram_activation.SetCoefficient(tier_usage[vm][tier], allocation[vm]['mem_units'])
        ram_activation.SetCoefficient(mem[vm][tier], -1)

        # subject to CPU_RAM_activation{i in Tier, j in VM}:
        #   mem_max[j] * cpu[i, j] - mem[i, j] >= 0;
        cpu_ram_activation = solver.Constraint(0, solver.infinity())
        cpu_ram_activation.SetCoefficient(cpu[vm][tier], allocation[vm]['mem_units'])
        cpu_ram_activation.SetCoefficient(mem[vm][tier], -1)

        # subject to RAM_CPU_activation{i in Tier, j in VM}:
          # cpu_max[j] * mem[i, j] - cpu[i, j] >= 0
        ram_cpu_activation = solver.Constraint(0, solver.infinity())
        ram_cpu_activation.SetCoefficient(mem[vm][tier], allocation[vm]['cpu_cores'])
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
      # sum{j in VM} cpu[i, j] = cpu_demand[i];
      cpu_demand = solver.Constraint(plan[tier]['cpu_cores'], plan[tier]['cpu_cores'])
      mem_demand = solver.Constraint(plan[tier]['mem_units'], plan[tier]['mem_units'])
      for vm in allocation:
        cpu_demand.SetCoefficient(cpu[vm][tier], 1)
        mem_demand.SetCoefficient(mem[vm][tier], 1)

    status = solver.Solve()
    print status
    if status != 0:
      raise Exception('No solution found')
    new_allocation = {}
    for vm in allocation:
      for tier in plan:
        if tier_usage[vm][tier].solution_value() > 0:
          new_allocation.setdefault(vm, {})
          new_allocation[vm].setdefault(tier, {})
          new_allocation[vm][tier]['cpu_cores'] = int(cpu[vm][tier].solution_value())
          new_allocation[vm][tier]['mem_units'] = int(mem[vm][tier].solution_value())
    return new_allocation

def main():
  logging.basicConfig(level=logging.DEBUG)
  topology = {
    'infrastructure': {
      "cpu_cores": 2,
      "mem_units": 8,
    },
    "auto_scaling_group": "monolithic-ex-2cpu",
    "hooks_git": "https://github.com/n43jl/hooks",
    "tiers": [
      {
        "name": "pwitter-web",
        "image": "pwitter-web",
        "entrypoint_params": "-w 3 -k eventlet",
        "tier_hooks": ["test_tier_hook.sh"],
        "depends_on": ["rubiss-jboss"],
        "scale_hooks": ["test_scale_hook.sh"]
      }, {
        "name": "rubis-jboss",
        "image": "polimi/rubis-jboss:nosensors",
        "entrypoint_params": " /opt/jboss-4.2.2.GA/bin/run.sh --host=0.0.0.0 --bootdir=/opt/rubis/rubis-cvs-2008-02-25/Servlets_Hibernate -c default"
      }
    ]
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
  solver = AllocationSolver(topology)
  new_allocation = solver.solve(plan, allocation)
  print 'plan=', plan
  print 'allocation=', allocation
  print 'new allocation', new_allocation

if __name__ == '__main__':
  main()