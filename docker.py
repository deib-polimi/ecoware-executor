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

def create_container(docker_container):
  vm = docker_container.vm
  port = vm.docker_port
  name = docker_container.name
  image = get_image(name)
  cpuset = ','.join(map(str, docker_container.cpuset))
  mem = docker_container.get_mem_mb()
  cmd = 'docker -H :{} exec -it docker-set docker run -it -d --cpuset-cpus={} -m={}m --name={} {}'.format(port, cpuset, mem, name, image)
  subprocess.check_call(cmd.split())
  logging.info('vm={}:{}; docker run -it -d --cpuset-cpus={} -m={}g --name={} {}'.format(vm.name, port, cpuset, mem, name, image))

def stop_container(docker_container):
  vm = docker_container.vm
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H :{} exec -it docker-set docker stop {}'.format(port, name)
  subprocess.check_call(cmd.split())
  logging.info('vm={}:{}; docker stop {}'.format(vm.name, port, name))

def start_container(docker_container):
  vm = docker_container.vm
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H :{} exec -it docker-set docker start {}'.format(port, name)
  subprocess.check_call(cmd.split())
  logging.info('vm={}:{}; docker start {}'.format(vm.name, port, name))

def delete_container(docker_container):
  vm = docker_container.vm
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H :{} exec -it docker-set docker rm -f {}'.format(port, name)
  try:
    subprocess.check_call(cmd.split())
  except Exception, e:
    logging.error(e)
  logging.info('vm={}:{}; docker rm -f {}'.format(vm.name, port, name))

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

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)