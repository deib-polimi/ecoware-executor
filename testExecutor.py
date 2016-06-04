import logging
logging.basicConfig(level=logging.DEBUG)
import unittest
import json
from os.path import isfile

import executor


class TestExecutor(unittest.TestCase):

  def read_json(self, filename):
    result = {}
    with open(filename, 'r') as f:
      result = json.loads(f.read())
    f.closed
    return result

  def test(self):
    topology = self.read_json('tests/topology.json')
    
    allocation = {
      'new_vm0': {
        'rubis_db': {}
      }
    }

    vm_name_dict = {
      'new_vm0': ('i-123', '127.0.0.1')
    }

    hosts = executor.get_hosts('rubis', 'app_server', topology, allocation, vm_name_dict)
    self.assertEquals(hosts, [u'db:127.0.0.1'])

if __name__ == '__main__':
  unittest.main()