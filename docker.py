#!/usr/bin/python

import subprocess
import logging
import json

def update_container(name, cpuset_arr, mem_units):
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

def run_container(name, image, cpuset_arr, mem_units, docker_params, entrypoint_params):
  cpuset = ','.join(map(str, cpuset_arr))
  mem_mb = mem_units * 512
  cmd = 'docker run -itd {} --cpuset-cpus={} -m={}m --name={} -v=/ecoware:/ecoware {} {}'.format(docker_params, cpuset, mem_mb, name, image, entrypoint_params)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def remove_container(name):
  cmd = 'docker rm -f {}'.format(name)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def inspect():
  containers = []
  cmd = 'docker ps -q'
  try:
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
    for line in output.split('\n'):
      if line:
        containers.append(line)
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output) 
  result = {}
  for container_id in containers:
    cmd = 'docker inspect ' + container_id
    try:
      output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
      logging.info(cmd)
      info = json.loads(output)
      name = info[0]['Name'][1:]
      cpuset = info[0]['HostConfig']['CpusetCpus']
      mem = info[0]['HostConfig']['Memory']
      mem_units = int(mem / (1024 * 1024 * 512))
      result[name] = {
        'CpusetCpus': cpuset,
        'Memory': mem,
        'MemUnits': mem_units
      }
    except subprocess.CalledProcessError, ex: # error code <> 0 
      print ex.output
      raise Exception(ex.output) 
  return result

def run_tier_hooks(name, hook, arg1, arg2):
  try:
    cmd = 'docker exec {} sh -c \'cd /ecoware/hooks/tier_hooks && ./{} "{}" "{}"\''.format(name, hook, arg1, arg2)
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logging.info(cmd)
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def run_scale_hooks(name, hooks):
  try:
    for hook in hooks:
      cmd = 'docker exec {} sh -c "cd /ecoware/hooks/scale_hooks && ./{}"'.format(name, hook)
      subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
      logging.info(cmd)
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  print inspect()