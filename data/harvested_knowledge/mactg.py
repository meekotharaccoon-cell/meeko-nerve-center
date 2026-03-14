{
  'graph': {
    'nodes': ['root', 'revenue_agents', 'orchestrator', 'commerce', 'intelligence'],
    'edges': [
      {'from': 'root', 'to': 'revenue_agents', 'weight': 1.0},
      {'from': 'intelligence', 'to': 'all_nodes', 'weight': 0.95}
    ],
    'accuracy': 0.9444
  }
}
