#!/usr/bin/python

import math
import logging

import aws_driver

def execute(plan, topology):
  for tier in plan:
    topology_data = topology.get(tier)
    if topology_data:
      vm_cpu_cores = topology_data['vm_cpu_cores']
      vm_mem_units = topology_data['vm_mem_units']
      group_name = topology_data.get('auto_scale_group_name')
      if group_name:
        require_cpu_cores = plan[tier]['cpu_cores']
        require_mem_units = plan[tier]['mem_units']
        require_vm_number0 = 1.0 *require_cpu_cores / vm_cpu_cores 
        require_vm_number1 = 1.0 * require_mem_units / vm_mem_units
        require_vm_number = int(math.ceil(max(require_vm_number0, require_vm_number1)))
        logging.debug('set auto scale group={}; capacity={}'.format(group_name, require_vm_number))
        aws_driver.set_desired_capacity(group_name, require_vm_number)
      else:
        logging.info('Tier {} is not scalable'.format(tier))
    else:
      logging.info('Tier {} is not scalable'.format(tier))

    