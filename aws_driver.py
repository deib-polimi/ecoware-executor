#!/usr/bin/python
import subprocess
import sys, os, base64, datetime, hashlib, hmac 
import urllib
import re
import time
import boto3
import json
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

if __name__ == '__main__':
  os.environ["AWS_ACCESS_KEY_ID"] = ""
  os.environ["AWS_SECRET_ACCESS_KEY"] = ""
  