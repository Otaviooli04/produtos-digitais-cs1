import urllib.request
import json

with urllib.request.urlopen("http://localhost:8000/exam/1/results") as r:
    print(json.dumps(json.loads(r.read()), indent=2, ensure_ascii=False))
