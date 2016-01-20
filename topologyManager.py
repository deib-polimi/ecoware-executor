#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from vm import Vm
from db import get_connection


_topology = {}

def init():
  global _topology
  conn = get_connection()
  try:
    for row in conn.execute('select * from vm'):
      vm = Vm(row[0], row[1], row[2], row[3], row[4])
      _topology[vm.name] = vm
      logging.debug('vm loaded={}'.format(vm))
    logging.debug('vm loaded={}'.format(_topology))
  finally:
    conn.close()

def get_vms():
  global _topology
  return _topology.values()

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  init()