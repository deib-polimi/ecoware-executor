#!/usr/bin/python

import json

import topologyManager
import vagrant

class Vm:

  MEM_UNIT = 512

  def __init__(self, id, name, cpu_cores, mem_units, host, docker_port):
    self.id = id
    self.name = name
    self.cpu_cores = cpu_cores
    self.mem_units = mem_units
    self.mem = self.get_mem()
    self.host = host
    self.docker_port = docker_port
    self.containers = []

  def get_mem(self):
    return self.get_mem_mb() / 1024.

  def get_mem_mb(self):
    return Vm.MEM_UNIT * self.mem_units

  def start(self):
    vagrant.create_vm(self)

  def delete(self):
    vagrant.delete_vm(self)

  def stop(self):
    vagrant.stop_vm(self)

  def dict(self):
    return {
      'id': self.id,
      'name': self.name,
      'cpu_cores': self.cpu_cores,
      'mem_units': self.mem_units,
      'mem': self.get_mem(),
      'host': self.host,
      'docker_port': self.docker_port,
      'containers': map(lambda x: x.dict(), self.containers)
    }

  def __str__(self):
    return (self.id, self.name, self.cpu_cores, self.mem_units, '{}:{}'.format(self.host, self.docker_port)).__str__()

  def __repr__(self):
    return self.__str__()