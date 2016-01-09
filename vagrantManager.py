#!/usr/bin/python

import subprocess
import os
import errno
import shutil

work_dir = '.workspace/executor/vms'

def modify_vagrant_file(txt, cpu, mem):
  lines = txt.split('\n')
  for i in range(0, len(lines)):
    if lines[i].find('v.cpus') is not -1:
      lines[i] = '    v.cpus = {}'.format(cpu)
    elif lines[i].find('v.memory') is not -1:
      lines[i] = '    v.memory = {}'.format(mem)
  return '\n'.join(lines)

def create_vm(vm_name, cpu, mem):
  path = '{0}/{1}'.format(work_dir, vm_name)
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise
  shutil.copy('virtualization/vagrant/bootstrap.sh', path)
  with open('virtualization/vagrant/Vagrantfile') as vagrant_file:
    txt = vagrant_file.read()
  txt = modify_vagrant_file(txt, cpu, mem)
  with open('{}/{}'.format(path, 'Vagrantfile'), 'w') as f:
    f.write(txt)
  cwd = os.getcwd()
  os.chdir(path)
  try:
    cmd = 'time vagrant up'
    print subprocess.check_call(cmd.split())
  finally:
    os.chdir(cwd)

if __name__ == '__main__':
  # create_vm('vm1', 1, 1024)
  print 'finished'
