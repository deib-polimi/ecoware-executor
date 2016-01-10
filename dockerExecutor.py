#!/usr/bin/python

import vagrantExecutor as vagrant

import subprocess
import logging
import sqlite3

containers = {}

conn = sqlite3.connect('executor.db')
try:
  sql = '''
    select c.*, vm.name
    from container c
    join vm on vm.id = c.vm_id
  '''
  for row in conn.execute(sql):
    vm = row[5]
    app = row[2]
    cpuset = row[3]
    containers[vm] = {}
    containers[vm][app] = cpuset
    cpu_list = map(int, cpuset.split(','))
    for i in cpu_list:
      vagrant.vms[vm]['free_cpu'].remove(i)
      vagrant.vms[vm]['taken_cpu'].append(i)
    logging.debug('container init; vm={}; app={}; cpuset={}'.format(vm, app, cpuset))
finally:
  conn.close()

def get_image(app):
  image = ''
  if app == 'jboss':
    image = 'httpd'
  elif app == 'db':
    image = 'nginx'
  else:
    raise Exception('Unknown app: {}'.format(app))
  return image

def get_cpuset(vm, cpu):
  cpu_list = []
  for i in range(0, cpu):
    cpu_list.append(str(vagrant.use_cpu(vm)))
  cpuset = ','.join(cpu_list)
  return cpuset

def create_container(vm, app, cpu, mem):
  port = vagrant.get_docker_port(vm)
  image = get_image(app)
  cpuset = get_cpuset(vm, cpu)  
  cmd = 'docker -H :{} exec -it docker-set docker run -it -d --cpuset-cpus={} -m={}g --name={} {}'.format(port, cpuset, mem, app, image)
  subprocess.check_call(cmd.split())
  if not vm in containers:
    containers[vm] = {}
  container_cpuset = containers[vm]
  container_cpuset[app] = cpuset
  conn = sqlite3.connect('executor.db')
  try:
    vm_id = conn.execute("select id from vm where name = '{}'".format(vm)).fetchone()[0]
    conn.execute("insert into container(vm_id, name, cpuset, mem) values ({}, '{}', '{}', {})".format(vm_id, app, cpuset, mem))
    conn.commit()
  finally:
    conn.close
  logging.info('vm={}:{}; docker run -it -d --cpuset-cpus={} -m={}g --name={} {}'.format(vm, port, cpuset, mem, app, image))

def set_container(vm, app, cpu, mem):
  global containers
  port = vagrant.get_docker_port(vm)
  prev_cpuset = containers.get(vm).get(app)
  prev_cpu_list = map(int, prev_cpuset.split(','))
  for i in prev_cpu_list:
    vagrant.free_cpu(vm, i)
  cpuset = get_cpuset(vm, cpu)
  cmd = 'docker -H :{} exec -it docker-set docker set --cpuset-cpus={} -m={}g {}'.format(port, cpuset, mem, app)
  subprocess.check_call(cmd.split())
  containers[vm][app] = cpuset
  conn = sqlite3.connect('executor.db')
  try:
    vm_id = conn.execute("select id from vm where name = '{}'".format(vm)).fetchone()[0]
    conn.execute("update container set cpuset = '{}', mem = {} where vm_id = {} and name = '{}'".format(cpuset, mem, vm_id, app))
    conn.commit()
  finally:
    conn.close()
  logging.info('vm={}:{}; docker set -cpuset={} -m={}g {}'.format(vm, port, cpuset, mem, app))

def rm_container(vm, app):
  global containers
  port = vagrant.get_docker_port(vm)
  cmd = 'docker -H :{} exec -it docker-set docker rm -f {}'.format(port, app)
  subprocess.check_call(cmd.split())
  cpuset = containers.get(vm).get(app)
  cpu_list = map(int, cpuset.split(','))
  for i in cpu_list:
    vagrant.free_cpu(vm, i)
  conn = sqlite3.connect('executor.db')
  try:
    vm_id = conn.execute("select id from vm where name = '{}'".format(vm)).fetchone()[0]
    conn.execute("delete from container where vm_id = {} and name = '{}'".format(vm_id, app))
    conn.commit()
  finally:
    conn.close()
  logging.info('vm={}:{}; docker rm {}'.format(vm, port, app))

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  # vagrant.create_vm('vm2', 2, 2)
  create_container('vm2', 'jboss', 2, 2)
  set_container('vm2', 'jboss', 1, 1)
  rm_container('vm2', 'jboss')

