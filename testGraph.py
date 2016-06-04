import logging
logging.basicConfig(level=logging.DEBUG)
import unittest
import json

import dependencyGraph

nodes = {
  'node0': {
    'depends_on': ['node1']
  },
  'node1': {
    'depends_on': ['node2']
  },
  'node3': {
    'depends_on': ['node1', 'node4']
  },
  'node4': {},
  'node2': {
    'depends_on': ['node4']
  }
}

class TestGraph(unittest.TestCase):

  def test(self):
    ordered_nodes = dependencyGraph.get_ordered_list(nodes)
    expected = [['node4'], ['node2'], ['node1'], ['node0', 'node3']]
    self.assertEquals(ordered_nodes, expected)

if __name__ == '__main__':
  unittest.main()