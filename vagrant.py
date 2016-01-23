#!/usr/bin/python

import subprocess
import os
import errno
import shutil
import time
import logging
import time
import sqlite3

import vm

work_dir = '.workspace/executor/vms'

def modify_vagrant_file(txt, cpu, mem, port):
  lines = txt.split('\n')
  for i in range(0, len(lines)):
    if lines[i].find('v.cpus') is not -1:
      lines[i] = '    v.cpus = {}'.format(cpu)
    elif lines[i].find('v.memory') is not -1:
      lines[i] = '    v.memory = {}'.format(mem)
    elif lines[i].find('config.vm.network "forwarded_port"') is not -1:
      lines[i] = '  config.vm.network "forwarded_port", guest: 2376, host: {}'.format(port)
  return '\n'.join(lines)

def create_vm(new_vm):
  start = time.time()
  mem_mb = new_vm.get_mem_mb()
  path = '{}/{}'.format(work_dir, new_vm.name)
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise
  with open('virtualization/vagrant/Vagrantfile') as vagrant_file:
    txt = vagrant_file.read()
  txt = modify_vagrant_file(txt, new_vm.cpu_cores, mem_mb, new_vm.docker_port)
  with open('{}/Vagrantfile'.format(path), 'w') as f:
    f.write(txt)
  cwd = os.getcwd()
  os.chdir(path)
  try:
    cmd = 'vagrant up'
    subprocess.check_call(cmd.split())
  finally:
    os.chdir(cwd)
  logging.info('VM {}:{} (cpu={}, mem={}mb) is up; time={}s'.format(new_vm.name, new_vm.docker_port, new_vm.cpu_cores, mem_mb, time.time() - start))

def delete_vm(vm2remove):
  start = time.time()
  cwd = os.getcwd()
  path = '{}/{}'.format(work_dir, vm2remove.name)
  try:
    os.chdir(path)
    try:
      cmd = 'vagrant destroy -f'
      subprocess.check_call(cmd.split())
    finally:
      os.chdir(cwd)
    os.remove('{}/Vagrantfile'.format(path))
    shutil.rmtree(path)
  except:
    pass
  logging.info('VM {}:{} is deleted; time={}s'.format(vm2remove.name, vm2remove.docker_port, time.time() - start))

def stop_vm(vm2remove):
  start = time.time()
  cwd = os.getcwd()
  path = '{0}/{1}'.format(work_dir, vm2remove.name)
  os.chdir(path)
  try:
    cmd = 'vagrant halt'
    subprocess.check_call(cmd.split())
  finally:
    os.chdir(cwd)
  logging.info('VM {}:{} is stopped; time={}s'.format(vm2remove.name, vm2remove.docker_port, time.time() - start))
  
if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  new_vm = vm.Vm(0, 'test', 1, 1, 5000)
  # create_vm(new_vm)
  # stop_vm(new_vm)
  delete_vm(new_vm)