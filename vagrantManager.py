#/usr/bin/python

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

def create_vm():
  vm_name = 'vm1'
  path = '{0}/{1}'.format(work_dir, vm_name)
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise
  with open('virtualization/vagrant/Vagrantfile') as vagrant_file:
    txt = vagrant_file.read()
  txt = modify_vagrant_file(txt, 2, 2048)
  with open('{}/{}'.format(path, 'Vagrantfile'), 'w') as f:
    f.write(txt)

if __name__ == '__main__':
  create_vm()
  print 'finished'