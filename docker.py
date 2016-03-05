#!/usr/bin/python

import subprocess
import logging

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

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
