import json, csv, time, requests

with open("artworks.json", encoding="utf-8") as f:
    members = json.load(f)["query"]["categorymembers"]

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "SDC-to-CSV/1.0 (you@example.org) requests/2"}

def flatten_value(snak):
    if "datavalue" not in snak:
        return ""
    v = snak["datavalue"]["value"]
    if isinstance(v, dict):
        return v.get("id") or v.get("time") or v.get("text") or v.get("amount") or json.dumps(v)
    return str(v)

def fetch_entity(mid, retries=3):
    params = {"action": "wbgetentities", "ids": mid,
              "props": "labels|descriptions|statements", "format": "json"}
    for attempt in range(retries):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200 and r.headers.get("content-type","").startswith("application/json"):
            return r.json()["entities"][mid]
        print(f"  {mid}: HTTP {r.status_code}, body: {r.text[:200]!r}")
        time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {mid}")

rows = []
for m in members:
    mid = f"M{m['pageid']}"
    ent = fetch_entity(mid)

    for lab in ent.get("labels", {}).values():
        rows.append({"file": mid, "title": m["title"], "type": "label",
                     "lang": lab["language"], "property": "", "value": lab["value"]})
    for desc in ent.get("descriptions", {}).values():
        rows.append({"file": mid, "title": m["title"], "type": "description",
                     "lang": desc["language"], "property": "", "value": desc["value"]})
    for pid, claims in ent.get("statements", {}).items():
        for c in claims:
            rows.append({"file": mid, "title": m["title"], "type": "statement",
                         "lang": "", "property": pid, "value": flatten_value(c["mainsnak"])})

with open("sdc.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file","title","type","lang","property","value"])
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} rows to sdc.csv")