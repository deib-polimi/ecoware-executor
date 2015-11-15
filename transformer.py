#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
from constraint import *
  
topology = {
  'vm1': {
    'cpu': 2,
    'mem': 2
  },
  'vm2': {
    'cpu': 2,
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
  problem = Problem()
  tier_cpu_vars = {}
  tier_mem_vars = {}
  for vm, limit in topology.iteritems():
    vm_cpu_vars = []
    vm_mem_vars = []
    for tier in plan:
      cpu_vars = tier_cpu_vars.setdefault(tier, [])
      mem_vars = tier_mem_vars.setdefault(tier, [])
      cpu_var = '{}_{}_cpu'.format(vm, tier)
      mem_var = '{}_{}_mem'.format(vm, tier)
      
      # variables grouped by VM
      vm_cpu_vars.append(cpu_var)
      vm_mem_vars.append(mem_var)

      # variables grouped by Tier
      cpu_vars.append(cpu_var)
      mem_vars.append(mem_var)

      problem.addVariable(cpu_var, range(0, limit['cpu'] + 1))
      problem.addVariable(mem_var, range(0, limit['mem'] + 1))

      # activation cpu <-> ram
      problem.addConstraint(lambda cpu, mem: 
        cpu * 1000 >= mem and mem * 1000 >= cpu, 
        (cpu_var, mem_var))

    problem.addConstraint(MaxSumConstraint(limit['cpu']), vm_cpu_vars)
    problem.addConstraint(MaxSumConstraint(limit['mem']), vm_mem_vars)

  for tier, demand in plan.iteritems():
    problem.addConstraint(ExactSumConstraint(demand['cpu']), tier_cpu_vars[tier])
    problem.addConstraint(ExactSumConstraint(demand['mem']), tier_mem_vars[tier])
  print problem.getSolutions()

def main():
  translate()

if __name__ == '__main__':
  main()