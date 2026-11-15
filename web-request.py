import json, csv, re, time, requests

with open("categorymembers.json", encoding="utf-8") as f:
    members = json.load(f)["query"]["categorymembers"]

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "Artwork-Template-To-CSV/1.0 (you@example.org) requests/2"}

def fetch_wikitext(pageid, retries=3):
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "pageids": str(pageid),
        "format": "json",
        "formatversion": 2,
    }
    for attempt in range(retries):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
            pages = r.json()["query"]["pages"]
            if pages and "revisions" in pages[0]:
                return pages[0]["revisions"][0]["content"]
        print(f"  page {pageid}: HTTP {r.status_code}, retrying")
        time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch wikitext for pageid {pageid}")

def parse_artwork_template(wikitext):
    """Extract {{Artwork ...}} parameters, handling nested {{...}} and [[...]]."""
    m = re.search(r'\{\{\s*Artwork\b', wikitext, re.IGNORECASE)
    if not m:
        return {}
    start = m.start()
    depth = 0
    i = start
    while i < len(wikitext):
        if wikitext[i:i+2] == "{{":
            depth += 1
            i += 2
        elif wikitext[i:i+2] == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                break
        else:
            i += 1
    template_body = wikitext[start+2:i-2]

    # Split on top-level pipes
    params = {}
    key = None
    buf = ""
    depth = 0
    for ch in template_body:
        if ch in "[{":
            depth += 1
            buf += ch
        elif ch in "]}":
            depth -= 1
            buf += ch
        elif ch == "|" and depth == 0:
            if key is not None:
                params[key.strip()] = buf.strip()
            key, buf = "", ""
            # read key up to next '='
            # handled in next segment
        elif ch == "=" and depth == 0 and key is not None and not buf:
            key = ""
            # key already accumulated? simpler: we'll parse differently
        else:
            buf += ch
    # A simpler approach: split on top-level pipes, then split each on first '='
    parts = []
    depth = 0
    current = ""
    for ch in template_body:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "|" and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    parts.append(current)

    for part in parts:
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        params[k.strip().lower()] = v.strip()
    return params

rows = []
for m in members:
    pageid = m["pageid"]
    title = m["title"]
    wikitext = fetch_wikitext(pageid)
    params = parse_artwork_template(wikitext)
    row = {"pageid": pageid, "title": title}
    row.update(params)
    rows.append(row)

# Collect all parameter names that appear
all_keys = set()
for r in rows:
    all_keys.update(r.keys())
all_keys.discard("pageid")
all_keys.discard("title")
fieldnames = ["pageid", "title"] + sorted(all_keys)

with open("artwork_metadata.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fieldnames})

print(f"Wrote {len(rows)} rows to artwork_metadata.csv")