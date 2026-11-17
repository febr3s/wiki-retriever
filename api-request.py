import json, csv, time, requests
from config import API, HEADERS, CATEGORY
# CATEGORY = "Art of Colombia"

with open(f"output/{CATEGORY.replace(' ', '_')}.json", encoding="utf-8") as f:
    members = json.load(f)["query"]["categorymembers"]

API = "https://commons.wikimedia.org/w/api.php"
WD_API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "SDC-to-CSV/1.0 (you@example.org) requests/2"}

def flatten_snak(snak):
    """Return (raw_value, datatype). datatype tells us if label resolution is needed."""
    if "datavalue" not in snak:
        return "", None
    dv = snak["datavalue"]
    v = dv["value"]
    dtype = dv.get("type")
    if isinstance(v, dict):
        if "id" in v:      return v["id"],    "wikibase-entityid"   # Q123 / P123
        if "time" in v:    return v["time"],  "time"
        if "text" in v:    return v["text"],  "monolingualtext"
        if "amount" in v:  return v["amount"], "quantity"
        return json.dumps(v), dtype
    return str(v), dtype

def fetch_entity(mid, retries=3):
    params = {"action": "wbgetentities", "ids": mid,
              "props": "labels|descriptions|statements", "format": "json"}
    for attempt in range(retries):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
            return r.json()["entities"][mid]
        print(f"  {mid}: HTTP {r.status_code}, body: {r.text[:200]!r}")
        time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {mid}")

def fetch_labels(ids, lang="en", chunk=50):
    """Fetch labels for a set of Q/P IDs from Wikidata. Returns {id: label}."""
    ids = list(ids)
    labels = {}
    for i in range(0, len(ids), chunk):
        batch = ids[i:i+chunk]
        r = requests.get(WD_API, params={
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "labels",
            "languages": lang,
            "languagefallback": 1,
            "format": "json",
        }, headers=HEADERS, timeout=30)
        r.raise_for_status()
        for eid, ent in r.json().get("entities", {}).items():
            lbl = ent.get("labels", {}).get(lang, {}).get("value")
            if lbl:
                labels[eid] = lbl
        time.sleep(0.2)
    return labels

# ---- Phase 1: fetch entities, build rows, collect IDs needing labels ----
rows = []
ids_to_resolve = set()

for m in members:
    mid = f"M{m['pageid']}"
    ent = fetch_entity(mid)

    for lab in ent.get("labels", {}).values():
        rows.append({"file": mid, "title": m["title"], "type": "label",
                     "lang": lab["language"], "property": "", "property_label": "",
                     "value": lab["value"], "value_label": lab["value"]})
    for desc in ent.get("descriptions", {}).values():
        rows.append({"file": mid, "title": m["title"], "type": "description",
                     "lang": desc["language"], "property": "", "property_label": "",
                     "value": desc["value"], "value_label": desc["value"]})
    for pid, claims in ent.get("statements", {}).items():
        ids_to_resolve.add(pid)
        for c in claims:
            val, dtype = flatten_snak(c["mainsnak"])
            if dtype == "wikibase-entityid":
                ids_to_resolve.add(val)
            rows.append({"file": mid, "title": m["title"], "type": "statement",
                         "lang": "", "property": pid, "property_label": "",
                         "value": val, "value_label": ""})

# ---- Phase 2: one batched lookup on Wikidata ----
labels = fetch_labels(ids_to_resolve)
print(f"Resolved {len(labels)}/{len(ids_to_resolve)} labels from Wikidata")

# ---- Phase 3: fill in labels, write CSV ----
for row in rows:
    if row["property"]:
        row["property_label"] = labels.get(row["property"], row["property"])
    if row["type"] == "statement":
        v = row["value"]
        if v.startswith("Q") or v.startswith("P"):
            row["value_label"] = labels.get(v, v)
        else:
            row["value_label"] = v[1:] if v.startswith("+") else v

with open(f"output/{CATEGORY.replace(' ', '_')}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file", "title", "type", "lang",
                                      "property", "property_label",
                                      "value", "value_label"])
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} rows to {CATEGORY.replace(' ', '_')}.csv")