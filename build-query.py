import json

with open("artworks.json", encoding="utf-8") as f:
    members = json.load(f)["query"]["categorymembers"]

values = "\n".join(
    f"    <https://commons.wikimedia.org/entity/M{m['pageid']}>" for m in members
)

print(f"""SELECT ?file ?depicts ?depictsLabel WHERE {{
  VALUES ?file {{
{values}
  }}
  OPTIONAL {{ ?file wdt:P180 ?depicts . }}
  OPTIONAL {{
    SERVICE <https://query.wikidata.org/sparql> {{
      ?depicts rdfs:label ?depictsLabel .
      FILTER(LANG(?depictsLabel) = "en")
    }}
  }}
}}""")