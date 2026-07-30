import sys
sys.path.append('E:\\Project_AGY\\13_AGY_model_monitor')
import data_fetcher
import json

data = data_fetcher.fetcher.get_quota()
print(json.dumps(data, indent=2))
