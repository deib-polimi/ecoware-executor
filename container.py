#!/usr/bin/python

import vm

class Container:

  def __init__(self, id, vm, name, cpuset, mem_units):
    self.id = id
    self.vm = vm
    self.name = name
    self.cpuset = map(int, cpuset.split())
    self.mem_units = int(mem_units)

  def get_mem(self):
    return vm.Vm.MEM_UNIT * self.mem_units / 1024.

  def dict(self):
    return {
      'id': self.id,
      'name': self.name,
      'cpuset': self.cpuset,
      'mem_units': self.mem_units,
      'mem': self.get_mem()
    }

  def __str__(self):
    return (self.id, self.vm.id, self.name, self.cpuset, self.mem_units).__str__()