#!/usr/bin/python

import math

import aws_driver

# t2.medium
CPU_CORES = 2.0
MEM_UNITS = 8.0

def execute(plan):
  actions = []
  for tier in plan:
    if tier == 'jboss':
      require_cpu_cores = plan[tier]['cpu_cores']
      require_mem_units = plan[tier]['mem_units']
      require_vm_number0 = math.ceil(require_cpu_cores / CPU_CORES)
      require_vm_number1 = math.ceil(require_mem_units / MEM_UNITS)
      require_vm_number = int(max(require_vm_number0, require_vm_number1))
      action = aws_driver.set_desired_capacity(require_vm_number)
      actions.append(action)
  return actions

    