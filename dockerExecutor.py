#!/usr/bin/python

import vagrantExecutor as vagrant

import subprocess
import logging

def create_container(vm, app, cpu, mem):
  port = vagrant.get_docker_port(vm)
  image = ''
  if app == 'jboss':
    image = 'httpd'
  elif app == 'db':
    image = 'nginx'
  else:
    raise Exception('Unknown app: {}'.format(app))
  cmd = 'docker -H :{} exec -it docker-set docker run -it -d {}'.format(port, image)
  exit_code = subprocess.check_call(cmd.split())
  logging.info('vm={}; docker run -cpu={} -mem={}g {}; exit code={}'.format(vm, cpu, mem, image, exit_code))
  

if __name__ == '__main__':
  logging.basicConfig(logging.INFO)
  vagrant.create_vm('vm1', 2, 2048)
  create_container('vm1', 'jboss', 1, 1024)

