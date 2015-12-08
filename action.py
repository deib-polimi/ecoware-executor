#!/usr/bin/python
# -*- coding: utf-8 -*-

from enum import Enum

class ActionType(Enum):
    create = 1
    modify = 2
    delete = 3

class Action:
  def __init__(self, type, vm, container=None, cpu=None, mem=None):
    self.type = type
    self.vm = vm
    self.container = container
    self.cpu = cpu
    self.mem = mem

  def __str__(self):
    if self.type == ActionType.create:
      return "create '{0}' container in '{1}' virtual machine with cpu_cores={2} and mem={3}gb".format(self.container, self.vm, self.cpu, self.mem)
    elif self.type == ActionType.modify:
      return "set '{0}' container in '{1}' virtual machine cpu_cores={2} and mem={3}gb".format(self.container, self.vm, self.cpu, self.mem)
    elif self.type == ActionType.delete:
      return "delete '{0}' container from '{1}' virtual machine".format(self.container, self.vm)
