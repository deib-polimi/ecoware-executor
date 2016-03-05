#!/usr/bin/python

import subprocess
import logging
import json

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

def get_allocation():
  containers = ['rubis-jboss', 'pwitter-web']
  result = {}
  for container in containers:
    cmd = 'docker inspect ' + container
    try:
      output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
      logging.info(cmd)
      info = json.loads(output)
      cpuset = info[0]['HostConfig']['CpusetCpus']
      mem = info[0]['HostConfig']['Memory']
      mem_units = int(info[0]['HostConfig']['Memory'] / (1024 * 1024 * 512))
      result[container] = {
        'CpusetCpus': cpuset,
        'Memory': mem,
        'MemUnits': mem_units
      }
    except subprocess.CalledProcessError, ex: # error code <> 0 
      print ex.output
      raise Exception(ex.output) 
  return result

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  print get_allocation()