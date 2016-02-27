#!/usr/bin/python
import subprocess
import sys, os, base64, datetime, hashlib, hmac 
import urllib
import re
import time
import boto3
import json
import logging
from xml.etree import ElementTree
from collections import OrderedDict

def set_desired_capacity(group_name, capacity):
  client = boto3.client('autoscaling')
  return client.update_auto_scaling_group(
    AutoScalingGroupName=group_name,
    DesiredCapacity=capacity,
    MaxSize=capacity
  )

def get_auto_scale_groups():
  client = boto3.client('autoscaling')
  response = client.describe_auto_scaling_groups()
  groups = {}
  for group in response['AutoScalingGroups']:
    groups[group['AutoScalingGroupName']] = group['DesiredCapacity']
  return groups

def start_virtual_machines(group_name, capacity):
  start = time.time()
  set_desired_capacity(group_name, capacity)
  client = boto3.client('autoscaling')
  my_group = None
  is_ready = False
  while not is_ready:
    response = client.describe_auto_scaling_groups()
    for group in response['AutoScalingGroups']:
      if group['AutoScalingGroupName'] == group_name:
        my_group = group
        break
    if len(my_group['Instances']) == capacity:
      is_ready = True
      for instance in my_group['Instances']:
        if instance['LifecycleState'] != 'InService':
          is_ready = False
    else:
      print 'sleep 10s'
      time.sleep(10)
  instance_ids = []
  for instance in my_group['Instances']:
    instance_ids.append(instance['InstanceId'])
  logging.debug('AWS instance ids; autoscale_group={}; ids={}'.format(group_name, instance_ids))
  return get_ip_addresses(instance_ids)

def get_ip_addresses(instance_ids):
  ec2 = boto3.client('ec2')
  request = ec2.describe_instances(
    Filters=[
      {
        'Name': 'instance-id',
        'Values': instance_ids,
      },
    ]
  )
  response = request['Reservations'][0]['Instances']
  instances = []
  for reservation in request['Reservations']:
    for instance in reservation['Instances']:
      instance_id = instance['InstanceId']
      public_ip = instance['PublicIpAddress']
      instances.append((instance_id, public_ip))
  return instances


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  os.environ["AWS_ACCESS_KEY_ID"] = ""
  os.environ["AWS_SECRET_ACCESS_KEY"] = ""