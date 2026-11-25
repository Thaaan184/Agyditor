import subprocess, json

queries = [
    ("tag_typography", ["npx", "hyperframes", "catalog", "--type", "component", "--tag", "typography", "--json"]),
    ("tag_captions", ["npx", "hyperframes", "catalog", "--type", "component", "--tag", "caption-style", "--json"]),
    ("q_3d_text", ["npx", "hyperframes", "catalog", "--query", "3d text", "--json"]),
    ("q_blur", ["npx", "hyperframes", "catalog", "--query", "blur text", "--json"]),
    ("q_roll", ["npx", "hyperframes", "catalog", "--query", "roll", "--json"]),
    ("q_glitch", ["npx", "hyperframes", "catalog", "--query", "glitch text", "--json"]),
]

for label, cmd in queries:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"ERROR {label}: {res.stderr}")
        continue
    data = json.loads(res.stdout)
    results = data if isinstance(data, list) else data.get("results", [])
    print(f"\n=== {label} ({len(results)}) ===")
    for r in results[:20]:
        print(f"  [{r.get('type')}] {r.get('name')}: {r.get('title')} | {r.get('description')}")
