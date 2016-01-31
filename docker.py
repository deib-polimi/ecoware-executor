#!/usr/bin/python

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

def run_container(docker_container):
  vm = docker_container.vm
  host = vm.host
  port = vm.docker_port
  name = docker_container.name
  image = get_image(name)
  cpuset = ','.join(map(str, docker_container.cpuset))
  mem = docker_container.get_mem_mb()
  cmd = 'docker -H {}:{} exec -it docker-set docker run -it -d --cpuset-cpus={} -m={}m --name={} -v=/vagrant:/vagrant {}'.format(host, port, cpuset, mem, name, image)
  subprocess.check_call(cmd.split())
  logging.info('docker -H {}:{} run -it -d --cpuset-cpus={} -m={}m --name={} {}'.format(host, port, cpuset, mem, name, image))

def stop_container(docker_container):
  vm = docker_container.vm
  host = vm.host
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H {}:{} exec -it docker-set docker stop {}'.format(host, port, name)
  subprocess.check_call(cmd.split())
  logging.info('docker -H {}:{} stop {}'.format(host, port, name))

def start_container(docker_container):
  vm = docker_container.vm
  host = vm.host
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H {}:{} exec -it docker-set docker start {}'.format(host, port, name)
  subprocess.check_call(cmd.split())
  logging.info('docker -H {}:{} start {}'.format(host, port, name))

def delete_container(docker_container):
  vm = docker_container.vm
  host = vm.host
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H {}:{} exec -it docker-set docker rm -f {}'.format(host, port, name)
  try:
    subprocess.check_call(cmd.split())
  except Exception, e:
    logging.error(e)
  logging.info('docker -H {}:{} rm -f {}'.format(host, port, name))

def set_container(container, cpuset, mem_mb):
  vm = container.vm
  host = vm.host
  port = vm.docker_port
  cpuset_string = ','.join(map(str, cpuset))
  cmd = 'docker -H {}:{} exec -it docker-set docker set --cpuset-cpus={} -m={}m {}'.format(host, port, cpuset_string, mem_mb, container.name)
  subprocess.check_call(cmd.split())
  logging.info('docker -H {}:{} set -cpuset={} -m={}m {}'.format(host, port, cpuset_string, mem_mb, container.name))
  

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)