import io
import json
import pandas as pd
from pandas.io.json import json_normalize

acled = None
with io.open('acled.json', 'r', encoding='utf-8') as json_file:
    acled = json.load(json_file)
    acled = acled['data']

df = json_normalize(acled)
df.to_csv('acled.csv', encoding='utf-8', index=False)
