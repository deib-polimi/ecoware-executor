#!/usr/bin/python

import subprocess
import os
import errno
import shutil
import time
import logging
import time
import sqlite3

work_dir = '.workspace/executor/vms'
vms = {}

conn = sqlite3.connect('executor.db')
try:
  for row in conn.execute('select * from vm'):
    vms[row[1]] = {
      'docker_port': row[4],
      'free_cpu': range(0, row[2]),
      'taken_cpu': []
    }
finally:
  conn.close()

def get_docker_port(vm):
  global vms
  return vms.get(vm)['docker_port']

def use_cpu(vm):
  global vms
  vm = vms.get(vm)
  cpu_index = vm['free_cpu'].pop()
  vm['taken_cpu'].append(cpu_index)
  return cpu_index

def free_cpu(vm, cpu_index):
  global vms
  vm = vms.get(vm)
  vm['taken_cpu'].remove(cpu_index)
  vm['free_cpu'].append(cpu_index)

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

def create_vm(vm_name, cpu, mem):
  global vms
  start = time.time()
  port = 5000
  mem = mem * 1000 # gb to mb
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
  taken_ports = map(lambda x: x['docker_port'], vms.values())
  while port in taken_ports:
    port = port + 1
  vms[vm_name] = {
    'docker_port': port, 
    'free_cpu': range(0, cpu),
    'taken_cpu': []
  }
  txt = modify_vagrant_file(txt, cpu, mem, port)
  with open('{}/{}'.format(path, 'Vagrantfile'), 'w') as f:
    f.write(txt)
  cwd = os.getcwd()
  os.chdir(path)
  try:
    cmd = 'vagrant up'
    subprocess.check_call(cmd.split())
  finally:
    os.chdir(cwd)
  conn = sqlite3.connect('executor.db')
  try:
    conn.execute("insert into vm (name, cpu, mem, docker_port) values ('{}', {}, {}, {})".format(vm_name, cpu, mem, port))
    conn.commit()
  finally:
    conn.close()
  logging.info('VM {}:{} (cpu={}, mem={}) is up; time={}s'.format(vm_name, port, cpu, mem, time.time() - start))

def delete_vm(vm):
  global vms
  start = time.time()
  cwd = os.getcwd()
  path = '{0}/{1}'.format(work_dir, vm)
  os.chdir(path)
  try:
    cmd = 'vagrant destroy -f'
    subprocess.check_call(cmd.split())
  finally:
    os.chdir(cwd)
  vm_data = vms[vm]
  del vms[vm]
  conn = sqlite3.connect('executor.db')
  try:
    conn.execute("delete from vm where name = '{}'".format(vm))
    conn.commit()
  finally:
    conn.close()
  logging.info('VM {}:{} is deleted; time={}s'.format(vm, vm_data['docker_port'], time.time() - start))

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  create_vm('vm1', 1, 1)
  create_vm('vm2', 1, 1)
  delete_vm('vm1')
  delete_vm('vm2')
  
