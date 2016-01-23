#!/usr/bin/python

import subprocess
import os
import errno
import shutil
import time
import logging
import time
import sqlite3

from vm import Vm

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

def create_vm(vm):
  start = time.time()
  mem_mb = vm.mem_units * Vm.MEM_UNIT
  print mem_mb
  path = '{0}/{1}'.format(work_dir, vm.name)
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise
  with open('virtualization/vagrant/Vagrantfile') as vagrant_file:
    txt = vagrant_file.read()
  txt = modify_vagrant_file(txt, cpu, mem_mb, port)
  with open('{}/{}'.format(path, 'Vagrantfile'), 'w') as f:
    f.write(txt)
  cwd = os.getcwd()
  os.chdir(path)
  try:
    cmd = 'vagrant up'
    subprocess.check_call(cmd.split())
  finally:
    os.chdir(cwd)
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
    vm_id = conn.execute("select id from vm where name = '{}'".format(vm)).fetchone()[0]
    conn.execute('delete from container where vm_id = {}'.format(vm_id))
    conn.execute("delete from vm where name = '{}'".format(vm))
    conn.commit()
  finally:
    conn.close()
  logging.info('VM {}:{} is deleted; time={}s'.format(vm, vm_data['docker_port'], time.time() - start))

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  create_vm('vm1', 2, 1)
  # create_vm('vm2', 2, 1)
  delete_vm('vm1')
  # delete_vm('vm2')
  
