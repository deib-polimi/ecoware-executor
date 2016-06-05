#/usr/bin/python

action_type = {
  'create_vm': 0,
  'delete_vm': 1,
  'create_container': 2,
  'delete_container': 3,
  'update_container': 4,
  'run_scale_hooks': 5,
  'run_tier_hooks': 6
}

 # container=None, cpu_cores=None, mem_units=None, prev_cpu_cores=None, prev_mem_units=None, topology=None
 #    self.prev_mem_units = prev_mem_units
 #    self.topology = topology

class VmAction:

  def __init__(self, action_type, vm):
    self.action_type = action_type
    self.vm = vm
    self.order_key = 0

  def __str__(self):
    if self.action_type == action_type['create_vm']:
      return "create vm '{}'".format(self.vm)
    elif self.action_type == action_type['delete_vm']:
      return "delete vm '{}'".format(self.vm)


class ContainerAction(VmAction):

  def __init__(self, action_type, vm, container, cpu_cores=None, mem_units=None):
    VmAction.__init__(self, action_type, vm)
    self.container = container
    self.cpu_cores = cpu_cores
    self.mem_units = mem_units

  def __str__(self):
    if self.action_type == action_type['delete_container']:
      return "delete container '{}' from vm '{}'".format(self.container, self.vm)
    elif self.action_type == action_type['update_container']:
      return "update container '{}' on vm '{}' with cpu cores={} and mem_units={}".format(self.container, self.vm, self.cpu_cores, self.mem_units)
    elif self.action_type == action_type['create_container']:
      return "create container '{}' on vm '{}' with cpu cores={} and mem_units={}".format(self.container, self.vm, self.cpu_cores, self.mem_units)

class TierHookAction(ContainerAction):
  def __init__(self, vm, container):
    ContainerAction.__init__(self, action_type['run_tier_hooks'], vm, container)

  def __str__(self):
    return "run tier hook for container '{}' on vm '{}'".format(self.container, self.vm)