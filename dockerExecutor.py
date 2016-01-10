#!/usr/bin/python

import vagrantExecutor as vagrant

import subprocess
import logging

containers = {}

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
  exit_code = subprocess.check_call(cmd.split())
  if not vm in containers:
    containers[vm] = {}
  container_cpuset = containers[vm]
  container_cpuset[app] = cpuset
  logging.info('vm={}:{}; docker run -it -d --cpuset-cpus={} -m={}g --name={} {}; exit code={}'.format(vm, port, cpuset, mem, app, image, exit_code))

def set_container(vm, app, cpu, mem):
  global containers
  port = vagrant.get_docker_port(vm)
  image = get_image(app)
  prev_cpuset = containers.get(vm).get(app)
  prev_cpu_list = map(int, prev_cpuset.split(','))
  for i in prev_cpu_list:
    vagrant.free_cpu(vm, i)
  cpuset = get_cpuset(vm, cpu)
  cmd = 'docker -H :{} exec -it docker-set docker set --cpuset-cpus={} -m={}g {}'.format(port, cpuset, mem, app)
  exit_code = subprocess.check_call(cmd.split())
  containers[vm][app] = cpuset
  logging.info('vm={}:{}; docker set -cpuset={} -m={}g {}; exit code={}'.format(vm, port, cpuset, mem, image, exit_code))

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  vagrant.create_vm('vm2', 2, 2)
  create_container('vm2', 'jboss', 2, 2)
  set_container('vm2', 'jboss', 1, 1)

