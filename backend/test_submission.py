import urllib.request
import json

BASE = "http://localhost:8000"

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

EXAM_ID = 1

print("=== SUBMISSÃO CORRETA ===")
result = post("/submission/evaluate", {
    "exam_id": EXAM_ID,
    "question_number": "1",
    "code": (
        '#include <stdio.h>\n'
        'int main(){\n'
        '    int n;\n'
        '    scanf("%d",&n);\n'
        '    if(n%2==0) printf("par\\n");\n'
        '    else printf("impar\\n");\n'
        '    return 0;\n'
        '}'
    )
})
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n=== SUBMISSÃO INCORRETA ===")
result2 = post("/submission/evaluate", {
    "exam_id": EXAM_ID,
    "question_number": "1",
    "code": (
        '#include <stdio.h>\n'
        'int main(){\n'
        '    int n;\n'
        '    scanf("%d",&n);\n'
        '    printf("par\\n");\n'
        '    return 0;\n'
        '}'
    )
})
print(json.dumps(result2, indent=2, ensure_ascii=False))

print("\n=== VERIFICANDO NO BANCO ===")
print(json.dumps(get(f"/exam/{EXAM_ID}"), indent=2, ensure_ascii=False))
