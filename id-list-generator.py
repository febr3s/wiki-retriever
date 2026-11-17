import json, requests

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "SDC-fetch/1.0 (you@example.org) requests/2"}
CATEGORY = "Paintings from Colombia"

def fetch_category(category):
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmtype": "file",
        "cmlimit": "max",
        "format": "json",
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "continue" in data:
        raise RuntimeError(f"{category} has more than 500 files; truncation not supported")
    return data["query"]["categorymembers"]

if __name__ == "__main__":
    category = CATEGORY
    members = fetch_category(category)

    with open(f"{category.replace(' ', '_')}.json", "w", encoding="utf-8") as f:
        json.dump({"batchcomplete": "", "query": {"categorymembers": members}},
                  f, indent=2, ensure_ascii=False)

    print(f"Fetched {len(members)} files")