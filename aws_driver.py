#!/usr/bin/python
import subprocess
import sys, os, base64, datetime, hashlib, hmac 
import urllib
import re
import requests # pip install requests
from xml.etree import ElementTree
from collections import OrderedDict

def cli_set_desired_capacity(group_name, capacity):
  cmd = 'aws --region us-west-2 autoscaling update-auto-scaling-group --auto-scaling-group-name {} --desired-capacity {0} --max {0}'.format(group_name, capacity)
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    return cmd
  except subprocess.CalledProcessError, ex: # error code <> 0 
    print ex.output
    raise Exception(ex.output)

def set_desired_capacity(group_name, capacity):
  method = 'GET'
  endpoint = 'https://autoscaling.us-west-2.amazonaws.com'
  parameters = {
    'Action': 'UpdateAutoScalingGroup',
    'AutoScalingGroupName': group_name,
    'DesiredCapacity': capacity,
    'HonorCooldown': False,
    'MaxSize': capacity,
    'Version': '2011-01-01'
  }
  request_url, headers = build_canonical_request(method, endpoint, parameters)
  r = requests.get(request_url, headers=headers)
  if r.status_code is not 200:
    raise Exception(r.text)  
  return r.text

def get_auto_scale_groups():
  method = 'GET'
  endpoint = 'https://autoscaling.us-west-2.amazonaws.com'
  parameters = {
    'Action': 'DescribeAutoScalingGroups',
    'Version': '2011-01-01'
  }
  request_url, headers = build_canonical_request(method, endpoint, parameters)
  r = requests.get(request_url, headers=headers)
  if r.status_code is not 200:
    raise Exception(r.text)  
  root = ElementTree.fromstring(r.text)
  ns = namespace(root)
  groups = root.find('.//*{}AutoScalingGroups'.format(ns))
  groups_dict = {}
  for member in groups:
    name = member.find(ns + 'AutoScalingGroupName').text
    desired_capacity = int(member.find(ns + 'DesiredCapacity').text)
    groups_dict[name] = desired_capacity
  return groups_dict

# http://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
# Key derivation functions. See:
# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def get_credentials():
  access_key = os.environ.get('AWS_ACCESS_KEY_ID')
  secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
  if access_key is None or secret_key is None:
      msg = 'No access key is available.'
      raise Exception(msg)
  return (access_key, secret_key)

def get_date():
  # Create a date for headers and the credential string
  t = datetime.datetime.utcnow()
  amzdate = t.strftime('%Y%m%dT%H%M%SZ')
  datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
  return (amzdate, datestamp)

def build_canonical_request(method, endpoint, parameters):
  access_key, secret_key = get_credentials()
  ordered_parameters = OrderedDict(sorted(parameters.items()))
  request_parameters = urllib.urlencode(ordered_parameters)
  canonical_uri = '/' 
  canonical_querystring = request_parameters
  amzdate, datestamp = get_date()
  # endpoint = 'https://autoscaling.us-west-2.amazonaws.com'
  # host = 'autoscaling.us-west-2.amazonaws.com'
  host = endpoint.split('//')[1]
  canonical_headers = 'host:' + host + '\n' + 'x-amz-date:' + amzdate + '\n'
  signed_headers = 'host;x-amz-date'
  payload_hash = hashlib.sha256('').hexdigest()
  canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
  algorithm = 'AWS4-HMAC-SHA256'

  # region = 'us-west-2'
  region = host.split('.')[1]
  # service = 'autoscaling'
  service = host.split('.')[0]
  credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'
  string_to_sign = algorithm + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request).hexdigest()
  signing_key = getSignatureKey(secret_key, datestamp, region, service)
  signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
  authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
  headers = {'x-amz-date':amzdate, 'Authorization':authorization_header}
  request_url = endpoint + '?' + canonical_querystring
  return (request_url, headers)

def namespace(element):
  m = re.match('\{.*\}', element.tag)
  return m.group(0) if m else ''

if __name__ == '__main__':
  os.environ["AWS_ACCESS_KEY_ID"] = "AKIAIOLT23JQ7DHIXATQ"
  os.environ["AWS_SECRET_ACCESS_KEY"] = ""
  print get_auto_scale_groups()
