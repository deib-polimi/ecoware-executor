#!/usr/bin/python

import subprocess
import logging

import topologyManager

def run_container(name, cpuset_arr, mem_units, info):
  logging.debug('run container')
  cpuset = ','.join(map(str, cpuset_arr))
  mem_mb = mem_units * 512
  image = info['image']
  docker_params = info.get('docker_params', '')
  entrypoint_params = info.get('entrypoint_params', '')
  cmd = 'docker run -it -d {} --cpuset-cpus={} -m={}m --name={} -v=/vagrant:/vagrant {} {}'.format(docker_params, cpuset, mem_mb, name, image, entrypoint_params)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def stop_container(name):
  logging.debug('stop container')
  cmd = 'docker stop {}'.format(name)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def start_container(name):
  logging.debug('start container')
  cmd = 'docker start {}'.format(name)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def delete_container(name):
  logging.debug('start container')
  cmd = 'docker rm -f {}'.format(name)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def update_container(name, cpuset_arr, mem_units):
  logging.debug('update container')
  cpuset = ','.join(map(str, cpuset_arr))
  mem_mb = mem_units * 512
  cmd = 'docker update --cpuset-cpus={} -m={}m {}'.format(cpuset, mem_mb, name)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def run_tier_hooks(name, hooks):
  for hook in hooks:
    cmd = 'docker exec {} sh -c "cd /vagrant/tier_hooks && ./{}"'.format(name, hook)
    subprocess.check_output(cmd, shell=True)
    logging.info(cmd)

def run_scale_hooks(container, hooks):
  for hook in hooks:
    cmd = 'docker exec {} sh -c "cd /vagrant/scale_hooks && ./{}"'.format(name, hook)
    subprocess.check_output(cmd, shell=True)
    logging.info(cmd)

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
