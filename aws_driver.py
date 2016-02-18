#!/usr/bin/python
import subprocess
from subprocess import Popen, PIPE

def console(cmd):
  p = Popen(cmd, shell=True, stdout=PIPE)
  out, err = p.communicate()
  return (p.returncode, out, err)

def set_desired_capacity(capacity):
  cmd = 'aws --region us-west-2 autoscaling update-auto-scaling-group --auto-scaling-group-name ex3 --desired-capacity {0} --max {0}'.format(capacity)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

  