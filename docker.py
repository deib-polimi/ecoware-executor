#!/usr/bin/python

import subprocess
import logging

import topologyManager

def _get_host_ip():
  cmd = "ip addr | awk '/docker0/ { print $0 }' | awk '/inet/ { print $2 }'"
  output = subprocess.check_output(cmd, shell=True)
  host = output.strip().split('/')[0]
  return host

def run_container(name, image, cpuset_arr, mem_units):
  logging.debug('run container')
  cpuset = ','.join(map(str, cpuset_arr))
  mem_mb = mem_units * 512
  cmd = 'docker run -it -d --cpuset-cpus={} -m={}m --name={} -v=/vagrant:/vagrant {}'.format(cpuset, mem_mb, name, image)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def stop_container(docker_container):
  vm = docker_container.vm
  host = vm.host
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H {}:{} docker stop {}'.format(host, port, name)
  subprocess.check_call(cmd.split())
  logging.info('docker -H {}:{} stop {}'.format(host, port, name))

def start_container(docker_container):
  vm = docker_container.vm
  host = vm.host
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H {}:{} docker start {}'.format(host, port, name)
  subprocess.check_call(cmd.split())
  logging.info('docker -H {}:{} start {}'.format(host, port, name))

def delete_container(docker_container):
  vm = docker_container.vm
  host = vm.host
  port = vm.docker_port
  name = docker_container.name
  cmd = 'docker -H {}:{} rm -f {}'.format(host, port, name)
  try:
    subprocess.check_call(cmd.split())
  except Exception, e:
    logging.error(e)
  logging.info('docker -H {}:{} rm -f {}'.format(host, port, name))

def update_container(container, cpuset, mem_mb):
  vm = container.vm
  # host = vm.host
  host = _get_host_ip()
  port = vm.docker_port
  cpuset_string = ','.join(map(str, cpuset))
  cmd = 'docker run -it n43jl/docker-update docker -H {}:{} update --cpuset-cpus={} -m={}m {}'.format(host, port, cpuset_string, mem_mb, container.name)
  subprocess.check_call(cmd.split())
  logging.info(cmd)

def run_tier_hooks(container, hooks):
  vm = container.vm
  host = vm.host
  port = vm.docker_port
  for hook in hooks:
    cmd = 'docker -H {}:{} exec {} sh -c "cd /vagrant/tier_hooks && ./{}"'.format(host, port, container.name, hook)
    subprocess.check_output(cmd, shell=True)
    logging.info(cmd)

def run_scale_hooks(container, hooks):
  vm = container.vm
  host = vm.host
  port = vm.docker_port
  for hook in hooks:
    cmd = 'docker -H {}:{} exec {} sh -c "cd /vagrant/scale_hooks && ./{}"'.format(host, port, container.name, hook)
    subprocess.check_output(cmd, shell=True)
    logging.info(cmd)

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  print _get_host_ip()