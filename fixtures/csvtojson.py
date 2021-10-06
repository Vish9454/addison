import csv
import json
from itertools import groupby
from datetime import datetime
csvFilePath = 'Region_Country_Addison.csv'
jsonFilePath = 'Region_Country_Addison.csv.json'

with open(csvFilePath, 'r') as csv_questions:
    r = csv.DictReader(csv_questions)
    data = [dict(d) for d in r]

    groups = []

    for k, g in groupby(data, lambda r: (r['pk'], r['model'])):
        for i in list(g):
            i.pop('pk')
            i.pop('model')
            # i['created_at'] = datetime.now()
            # i['updated_at'] = datetime.now()
            # i['is_deleted'] = False
            x = i
        groups.append({"pk": int(k[0]),
                       "model": k[1],
                       "fields": {k: v for k, v in x.items()}})

with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
    jsonf.write(json.dumps(groups, indent=4))