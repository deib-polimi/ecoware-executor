#!/usr/bin/python

import vagrantExecutor as vagrant

import subprocess
import logging

def get_image(app):
  image = ''
  if app == 'jboss':
    image = 'httpd'
  elif app == 'db':
    image = 'nginx'
  else:
    raise Exception('Unknown app: {}'.format(app))
  return image

def get_cpuset():
  max_cpu = vagrant.get_cpu_limit(vm)
  cpuset_start = vagrant.get_cpu_counter(vm) % max_cpu
  cpuset_end = cpuset_start + cpu
  cpuset = ','.join(map(lambda x: str(x % cpu), range(cpuset_start, cpuset_end)))


def create_container(vm, app, cpu, mem):
  port = vagrant.get_docker_port(vm)
  image = get_image(app)
  vagrant.set_cpu_counter(vm, cpuset_end)
  logging.debug('new cpu counter={}; vm={}; vm cpu={}'.format(cpuset_end, vm, max_cpu))
  cmd = 'docker -H :{} exec -it docker-set docker run -it -d --cpuset-cpus={} -m={}g {}'.format(port, cpuset, mem, image)
  exit_code = subprocess.check_call(cmd.split())
  logging.info('vm={}; docker run -cpu={} -mem={}g {}; exit code={}'.format(vm, cpu, mem, image, exit_code))

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  vagrant.create_vm('vm1', 2, 2048)
  create_container('vm1', 'jboss', 1, 1024)

