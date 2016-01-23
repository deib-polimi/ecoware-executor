#!/usr/bin/python

import json

import topologyManager
from vagrant import create_vm

class Vm:

  MEM_UNIT = 512

  def __init__(self, id, name, cpu_cores, mem_units, docker_port):
    self.id = id
    self.name = name
    self.docker_port = int(docker_port)
    self.cpu_cores = int(cpu_cores)
    self.mem_units = int(mem_units)

  def get_mem(self):
    return self.get_mem_mb / 1024.

  def get_mem_mb(self):
    return Vm.MEM_UNIT * self.mem_units

  def start(self):
    create_vm(self)

  def __dict__(self):
    return {
      'id': self.id,
      'name': self.name,
      'cpu_cores': self.cpu_cores,
      'mem': self.get_mem(),
      'docker_port': self.docker_port
    }

  def __str__(self):
    return (self.id, self.name, self.cpu_cores, self.mem_units, self.docker_port).__str__()

  def __repr__(self):
    return self.__str__()