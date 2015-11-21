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
    solutions = translator.translate(plan, topology.get_current())
    expected_plan = self.read_result('tests/result0.json')
    found = False
    for solution in solutions:
      if solution == expected_plan:
        found = True
    self.assertTrue(found, 'We should found the solution: ' + json.dumps(expected_plan, indent=4))

if __name__ == '__main__':
  unittest.main()