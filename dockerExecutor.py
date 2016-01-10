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
  cmd = 'docker -H :{} exec -it docker-set docker run -it -d --cpuset-cpus={} -m={}g {}'.format(port, cpuset, mem, image)
  exit_code = subprocess.check_call(cmd.split())
  if not vm in containers:
    containers[vm] = {}
  container_cpuset = containers[vm]
  container_cpuset[app] = cpuset
  logging.info('vm={}; docker run -cpuset={} -mem={}g {}; exit code={}'.format(vm, cpuset, mem, image, exit_code))

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  vagrant.create_vm('vm1', 2, 2048)
  create_container('vm1', 'jboss', 1, 1024)

