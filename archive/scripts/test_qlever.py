import requests, time

QLEVER = "https://qlever.dev/api/wikidata"
HEADERS = {
    "User-Agent": "BooktimeTest/1.0",
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
}

def sparql(query):
    t0 = time.time()
    r = requests.post(QLEVER, data=query.encode(), headers=HEADERS, timeout=30)
    elapsed = time.time() - t0
    rows = r.json().get("results", {}).get("bindings", []) if r.status_code == 200 else []
    return rows, elapsed

# Test 1 : compter le total de book series
print("=== Test 1 : COUNT book series (Q7725634) ===")
q = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd:  <http://www.wikidata.org/entity/>
SELECT (COUNT(?series) AS ?n) WHERE {
  ?series wdt:P31 wd:Q7725634 .
}
"""
rows, t = sparql(q)
print(f"Total book series : {rows[0]['n']['value'] if rows else '?'}   ({t:.2f}s)")

# Test 2 : compter les novel series
print("\n=== Test 2 : COUNT novel series (Q1667921) ===")
q = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd:  <http://www.wikidata.org/entity/>
SELECT (COUNT(?series) AS ?n) WHERE {
  ?series wdt:P31 wd:Q1667921 .
}
"""
rows, t = sparql(q)
print(f"Total novel series : {rows[0]['n']['value'] if rows else '?'}   ({t:.2f}s)")

# Test 3 : compter les manga series
print("\n=== Test 3 : COUNT manga series (Q21191270) ===")
q = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd:  <http://www.wikidata.org/entity/>
SELECT (COUNT(?series) AS ?n) WHERE {
  ?series wdt:P31 wd:Q21191270 .
}
"""
rows, t = sparql(q)
print(f"Total manga series : {rows[0]['n']['value'] if rows else '?'}   ({t:.2f}s)")

# Test 4 : pagination offset 5000 (book series)
print("\n=== Test 4 : Page offset=5000 (book series) ===")
q = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd:  <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?series ?label WHERE {
  ?series wdt:P31 wd:Q7725634 ;
          rdfs:label ?label .
  FILTER(LANG(?label) = "en")
}
ORDER BY ?series
LIMIT 500 OFFSET 5000
"""
rows, t = sparql(q)
print(f"Resultats : {len(rows)}   ({t:.2f}s)")
if rows:
    print(f"  Premier : {rows[0]['label']['value']}")
    print(f"  Dernier : {rows[-1]['label']['value']}")

# Test 5 : oeuvres d'une série (Harry Potter)
print("\n=== Test 5 : Oeuvres de Harry Potter (Q8337) ===")
q = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd:  <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?work ?labelFR ?labelEN ?volume WHERE {
  ?work wdt:P179 wd:Q8337 .
  OPTIONAL { ?work rdfs:label ?labelFR FILTER(LANG(?labelFR) = "fr") }
  OPTIONAL { ?work rdfs:label ?labelEN FILTER(LANG(?labelEN) = "en") }
  OPTIONAL { ?work wdt:P1545 ?volume }
}
"""
rows, t = sparql(q)
print(f"Resultats : {len(rows)}   ({t:.2f}s)")
for row in rows[:5]:
    fr = row.get("labelFR", {}).get("value", "")
    en = row.get("labelEN", {}).get("value", "")
    vol = row.get("volume", {}).get("value", "")
    print(f"  vol={vol:>3}  FR={fr}  EN={en}")
