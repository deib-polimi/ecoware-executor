#/usr/bin/python

import copy

def get_ordered_list(input_nodes):
  nodes = copy.deepcopy(input_nodes)
  result = []
  processed = []
  while nodes:
    sub_result = []
    cycle = True
    keys = nodes.keys()
    for key in keys:
      value = nodes[key]
      # remove dependencies on already processed nodes
      if 'depends_on' in value:
        value['depends_on'] = filter(lambda s: s not in processed, value['depends_on'])
      else:
        value['depends_on'] = []
      if not value['depends_on']:
        sub_result.append(key)
        del nodes[key]
        cycle = False
    for value in sub_result:
      processed.append(value)
    if len(sub_result):
      result.append(sub_result)
    if cycle:
      raise Exception('Cycle dependency')
  return result

if __name__ == '__main__':
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
    'node2': {}
  }
  print get_ordered_list(nodes)



