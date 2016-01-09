#!/usr/bin/python

import subprocess
import os
import errno
import shutil
import time
import logging

work_dir = '.workspace/executor/vms'
port = 5000
vms = {}

def get_docker_port(vm):
  return vms.get(vm)[0]

def get_cpu_counter(vm):
  return vms.get(vm)[1]

def set_cpu_counter(vm, new_value):
  vms.get(vm)[1] = new_value

def get_cpu_limit(vm):
  return vms.get(vm)[2]

def modify_vagrant_file(txt, cpu, mem, port):
  lines = txt.split('\n')
  for i in range(0, len(lines)):
    if lines[i].find('v.cpus') is not -1:
      lines[i] = '    v.cpus = {}'.format(cpu)
    elif lines[i].find('v.memory') is not -1:
      lines[i] = '    v.memory = {}'.format(mem * 1000) # gb to mb
    elif lines[i].find('config.vm.network "forwarded_port"') is not -1:
      lines[i] = '  config.vm.network "forwarded_port", guest: 2376, host: {}'.format(port)
  return '\n'.join(lines)

def create_vm(vm_name, cpu, mem):
  global port
  if vm_name in vms:
    raise Exception('Vm is already created ', vm_name)
  path = '{0}/{1}'.format(work_dir, vm_name)
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise
  shutil.copy('virtualization/vagrant/bootstrap.sh', path)
  shutil.copy('virtualization/vagrant/docker', path)
  with open('virtualization/vagrant/Vagrantfile') as vagrant_file:
    txt = vagrant_file.read()
  while port in vms.values():
    port = port + 1
  cpu_round_robin = 0
  vms[vm_name] = [port, cpu_round_robin, cpu]
  txt = modify_vagrant_file(txt, cpu, mem, port)
  with open('{}/{}'.format(path, 'Vagrantfile'), 'w') as f:
    f.write(txt)
  cwd = os.getcwd()
  os.chdir(path)
  try:
    cmd = 'time vagrant up'
    logging.info('vagrant up; exit code={}'.format(subprocess.check_call(cmd.split())))
  finally:
    os.chdir(cwd)
  logging.info('VM {} (cpu={}, mem={}, docker_port={}) is up'.format(vm_name, cpu, mem, vms[vm_name][0]))

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  create_vm('vm1', 1, 1024)
  create_vm('vm2', 1, 1024)
  
