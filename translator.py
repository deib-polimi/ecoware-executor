#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
from constraint import *

DELIMETER = '_$_'

topology = {
  'vm1': {
    'cpu_cores': 2,
    'mem': 2
  },
  'vm2': {
    'cpu_cores': 2,
    'mem': 2
  }
}

def read_plan():
  plan = {}
  with open('plan.json', 'r') as f:
    read_data = f.read()
    plan = json.loads(read_data)
  f.closed
  return plan

def translate():
  plan = read_plan()
  solutions = solve_csp(plan)
  print json.dumps(parse_solutions(solutions))

def solve_csp(plan):
  problem = Problem()
  tier_cpu_vars = {}
  tier_mem_vars = {}
  for vm, limit in topology.iteritems():
    vm_cpu_vars = []
    vm_mem_vars = []
    for tier in plan:
      cpu_vars = tier_cpu_vars.setdefault(tier, [])
      mem_vars = tier_mem_vars.setdefault(tier, [])
      cpu_var = '{0}{2}{1}{2}cpu'.format(vm, tier, DELIMETER)
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

def parse_solution(solution):
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

def parse_solutions(solutions):
  results = []
  for solution in solutions:
    results.append(parse_solution(solution))
  return results

def main():
  translate()

if __name__ == '__main__':
  main()