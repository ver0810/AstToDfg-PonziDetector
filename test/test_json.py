import pandas as pd

data = pd.read_json("cache/batch_detection_cache.json")

print(data.head())