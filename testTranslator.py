import unittest
import json
from translator import read_plan, Translator
from topologyManager import TopologyManager

class TestTranslator(unittest.TestCase):

  def read_json(self, filename):
    result = {}
    with open(filename, 'r') as f:
      result = json.loads(f.read())
    f.closed
    return result

  def test_full_translation(self):
    plan = read_plan('tests/plan1.json')
    translator = Translator()
    topology = TopologyManager()
    topology.load('tests/topology1.json')
    micro_plan = translator.translate(plan, topology.get_current())
    expected_plan = self.read_json('tests/result1.json')
    self.assertEquals(micro_plan.sort(), expected_plan.sort())

  def test_allocation2plan(self):
    allocation = self.read_json('tests/allocation1.0.json')
    topology = TopologyManager()
    topology.load('tests/topology1.json')
    translator = Translator()
    plan = translator._allocation2plan(allocation, topology.get_current())
    result = self.read_json('tests/result1.0.json')
    self.assertEquals(result.sort(), plan.sort())

if __name__ == '__main__':
  unittest.main()