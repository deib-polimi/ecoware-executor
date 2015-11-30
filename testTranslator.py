import unittest
import json
import topologyManager
from translator import read_plan, Translator


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
    topologyManager.load('tests/topology1.json')
    actions = translator.translate(plan, topologyManager.get_current())
    # not solution
    self.assertTrue(actions == None)

  def test2(self):
    plan = read_plan('tests/plan2.json')
    translator = Translator()
    topologyManager.load('tests/topology2.json')
    actions = translator.translate(plan, topologyManager.get_current())

    result = self.read_json('tests/result2.json')
    string_actions = map(lambda x: x.__str__(), actions)
    print string_actions
    self.assertEquals(result.sort(), actions.sort())

  def test_allocation2plan(self):
    allocation = self.read_json('tests/allocation1.0.json')
    topologyManager.load('tests/topology1.json')
    translator = Translator()
    plan = translator._allocation2plan(allocation, topologyManager.get_current())
    result = self.read_json('tests/result1.0.json')
    self.assertEquals(result.sort(), plan.sort())

if __name__ == '__main__':
  unittest.main()