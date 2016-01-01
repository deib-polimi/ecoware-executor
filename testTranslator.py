import unittest
import json
import topologyManager
from os.path import isfile
from translator import read_plan, Translator


class TestTranslator(unittest.TestCase):

  def read_json(self, filename):
    result = {}
    with open(filename, 'r') as f:
      result = json.loads(f.read())
    f.closed
    return result

  def test(self):
    i = 1
    while True:
      plan_file = 'tests/plan{0}.json'.format(i)
      if isfile(plan_file):
        plan = read_plan(plan_file)
        translator = Translator()
        topologyManager.load('tests/topology{0}.json'.format(i))
        actions = translator.translate(plan, topologyManager.get_current())
        string_actions = map(lambda x: x.__str__(), actions)
        expected = self.read_json('tests/result{0}.json'.format(i))
        string_actions = sorted(string_actions)
        expected = sorted(expected)
        print i
        print 'topology=', topologyManager.get_current()
        print 'plan=', plan
        print 'actions=', string_actions
        print 'expected=', expected
        self.assertEquals(string_actions, expected)        
        return
      else:
        break
      i += 1

  def test_allocation2plan(self):
    allocation = self.read_json('tests/allocation1.0.json')
    topologyManager.load('tests/topology1.json')
    translator = Translator()
    actions = translator._2plan(allocation, topologyManager.get_current())
    string_actions = map(lambda x: x.__str__(), actions)
    result = self.read_json('tests/result1.0.json')
    self.assertEquals(sorted(string_actions), sorted(result))

if __name__ == '__main__':
  unittest.main()