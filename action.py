#!/usr/bin/python
# -*- coding: utf-8 -*-

from enum import Enum

class ActionType(Enum):
    vm_create = 1
    vm_delete = 2
    container_create = 3
    container_set = 4
    container_delete = 5

class Action:
  def __init__(self, type, vm, container=None, cpu=None, mem=None):
    self.type = type
    self.vm = vm
    self.container = container
    self.cpu = cpu
    self.mem = mem

  def __str__(self):
    if self.type == ActionType.vm_create:
      return "create virtual machine '{0}' with cpu_cores={1} and mem={2}gb".format(self.vm, self.cpu, self.mem)
    elif self.type == ActionType.vm_delete:
      return "delete virtual machine '{0}'".format(self.vm)
    elif self.type == ActionType.container_create:
      return "create '{0}' container in '{1}' virtual machine with cpu_cores={2} and mem={3}gb".format(self.container, self.vm, self.cpu, self.mem)
    elif self.type == ActionType.container_set:
      return "set '{0}' container in '{1}' virtual machine cpu_cores={2} and mem={3}gb".format(self.container, self.vm, self.cpu, self.mem)
    elif self.type == ActionType.container_delete:
      return "delete '{0}' container from '{1}' virtual machine".format(self.container, self.vm)
