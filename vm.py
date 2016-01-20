#!/usr/bin/python

class Vm:

  MEM_UNIT = 512

  def __init__(self, id, name, cpu_cores, mem_units, docker_port):
    self.id = id
    self.name = name
    self.docker_port = docker_port
    self.cpu_cores = cpu_cores
    self.mem_units = mem_units

  def get_mem(self):
    return Vm.MEM_UNIT * self.mem_units / 1024.

  def __str__(self):
    return (self.id, self.name, self.cpu_cores, self.get_mem(), self.docker_port).__str__()

