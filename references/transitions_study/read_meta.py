import json

with open("references/transitions_study/meta.jsonl", "r", encoding="utf-8-sig") as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            print("ID:", d.get("id"))
            print("Title:", d.get("title"))
            print("Uploader:", d.get("uploader"))
            print("Duration:", d.get("duration"))
            print("Description snippet:", (d.get("description") or "")[:200])
            print("-" * 50)
