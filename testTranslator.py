import unittest
import json
from translator import read_plan, Translator
from topologyManager import TopologyManager

class TestTranslator(unittest.TestCase):

  def read_result(self, filename):
    result = {}
    with open(filename, 'r') as f:
      result = json.loads(f.read())
    f.closed
    return result

  def test(self):
    plan = read_plan('tests/plan0.json')
    translator = Translator()
    topology = TopologyManager()
    micro_plan = translator.translate(plan, topology.get_current())
    expected_plan = self.read_result('tests/result0.json')
    found = False
    self.assertEquals(micro_plan, expected_plan)

if __name__ == '__main__':
  unittest.main()