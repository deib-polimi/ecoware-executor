#!/usr/bin/python

import subprocess

def cli_set_desired_capacity(group_name, capacity):
  cmd = 'aws --region us-west-2 autoscaling update-auto-scaling-group --auto-scaling-group-name {} --desired-capacity {0} --max {0}'.format(group_name, capacity)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)