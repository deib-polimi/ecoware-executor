import logging
logging.basicConfig(level=logging.DEBUG)
import unittest
import json
from os.path import isfile

from solver import AllocationSolver


class TestSolver(unittest.TestCase):

  def read_json(self, filename):
    result = {}
    with open(filename, 'r') as f:
      result = json.loads(f.read())
    f.closed
    return result

  def test(self):
    topology = {
      'infrastructure': {
        'cpu_cores': 2,
        'mem_units': 8
      }
    }
    i = 1
    while True:
      plan_file = 'tests/plan{0}.json'.format(i)
      if isfile(plan_file):
        plan = self.read_json(plan_file)
        solver = AllocationSolver(topology)
        allocation = self.read_json('tests/allocation{0}.json'.format(i))
        if i == 2 or i == 10:
          try:
            new_allocation = solver.solve(plan, allocation)
          except Exception as e:
            if ((i == 2 and str(e) == 'No solution needed') or
                (i == 10 and str(e) == 'No solution found')):
              pass
            else:
              raise e
        else:
          new_allocation = solver.solve(plan, allocation)
          expected = self.read_json('tests/result{0}.json'.format(i))
          print i
          print 'old_allocation=', allocation
          print 'plan=', plan
          print 'new_allocation=', new_allocation
          print 'expected=', expected
          self.assertEquals(new_allocation, expected)
      else:
        break
      i += 1

if __name__ == '__main__':
  unittest.main()