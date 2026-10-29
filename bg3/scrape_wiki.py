""" Exports equipment pages from bg3.wiki (CC BY-NC-SA 4.0) through the MediaWiki API.

    Step 1, fetch:  python -m bg3.scrape_wiki fetch     -> bg3/data/raw/pages.jsonl (page wikitext, not committed)
    Step 2, parse:  python -m bg3.scrape_wiki parse     -> bg3/data/raw/parsed.json (template parameters per item, for review)

    Modelled effects are kept in bg3/data/items.json, built from the parsed pages and reviewed by hand,
    since effect text ("weapon attacks deal an additional 1d4 fire damage") needs checking before it changes results """
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://bg3.wiki/w/api.php"
RAW = Path(__file__).parent / "data" / "raw"
USER_AGENT = "DAndDSimulator item export (https://github.com/AClaybrook/DAndDSimulator)"
# Item pages are built from these templates, every page that uses one is exported
TEMPLATES = ["Template:WeaponPage", "Template:EquipmentPage", "Template:ArmourPage", "Template:ClothingPage"]
BATCH = 50

def api(**params):
    params = {"format": "json", "formatversion": "2", **params}
    request = urllib.request.Request(f"{API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)

def pages_using(template):
    """ Titles of every article that uses a template """
    titles, params = [], {"action": "query", "list": "embeddedin", "eititle": template, "einamespace": 0, "eilimit": 500}
    while True:
        data = api(**params)
        titles += [p["title"] for p in data["query"]["embeddedin"]]
        if "continue" not in data:
            return titles
        params.update(data["continue"])
        time.sleep(0.5)

def wikitext(titles):
    """ {title: wikitext} for up to BATCH titles """
    data = api(action="query", prop="revisions", rvprop="content|timestamp", rvslots="main", titles="|".join(titles))
    return {p["title"]: (p["revisions"][0]["slots"]["main"]["content"], p["revisions"][0]["timestamp"])
            for p in data["query"]["pages"] if p.get("revisions")}

def fetch(templates=TEMPLATES):
    RAW.mkdir(parents=True, exist_ok=True)
    titles = {}
    for template in templates:
        found = pages_using(template)
        print(f"{template}: {len(found)} pages")
        titles.update({t: template for t in found})
    with open(RAW / "pages.jsonl", "w", encoding="utf-8") as f:
        ordered = sorted(titles)
        for ii in range(0, len(ordered), BATCH):
            for title, (text, timestamp) in wikitext(ordered[ii:ii + BATCH]).items():
                f.write(json.dumps({"title": title, "template": titles[title], "timestamp": timestamp, "wikitext": text}) + "\n")
            print(f"fetched {min(ii + BATCH, len(ordered))}/{len(ordered)}")
            time.sleep(0.5)

def template_params(text, template_name):
    """ Top level |key=value parameters of the first use of a template, nested templates and links are kept as text """
    start = text.find("{{" + template_name)
    if start < 0:
        return {}
    depth, ii, body_start = 0, start, start + 2 + len(template_name)
    while ii < len(text):
        if text.startswith("{{", ii):
            depth, ii = depth + 1, ii + 2
        elif text.startswith("}}", ii):
            depth, ii = depth - 1, ii + 2
            if depth == 0:
                break
        else:
            ii += 1
    body = text[body_start:ii - 2]
    params, depth, current = [], 0, ""
    for jj, char in enumerate(body):
        pair = body[jj:jj + 2]
        if pair in ("{{", "[["):
            depth += 1
        elif pair in ("}}", "]]"):
            depth -= 1
        if char == "|" and depth == 0:
            params.append(current)
            current = ""
        else:
            current += char
    params.append(current)
    result = {}
    for p in params:
        if "=" in p:
            key, value = p.split("=", 1)
            result[key.strip()] = value.strip()
    return result

def plain_text(value):
    """ Wikitext to readable text: [[Page|label]] -> label, {{DamageText|1d4|Fire}} -> 1d4 Fire, removes formatting """
    value = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", value)
    while re.search(r"\{\{[^{}]*\}\}", value):
        # Innermost templates first: keep the arguments, drop the template name
        value = re.sub(r"\{\{([^{}]*)\}\}", lambda m: " ".join(a.strip() for a in m.group(1).split("|")[1:]) or m.group(1).strip(), value)
    return re.sub(r"'{2,}", "", value).strip()

def parse():
    parsed = []
    with open(RAW / "pages.jsonl", encoding="utf-8") as f:
        for line in f:
            page = json.loads(line)
            params = template_params(page["wikitext"], page["template"].split(":", 1)[1])
            parsed.append({"title": page["title"], "template": page["template"], "timestamp": page["timestamp"],
                           "source": f"https://bg3.wiki/wiki/{urllib.parse.quote(page['title'].replace(' ', '_'))}",
                           "params": {k: plain_text(v) for k, v in params.items()}})
    with open(RAW / "parsed.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=1)
    keys = {}
    for p in parsed:
        for k in p["params"]:
            keys[k] = keys.get(k, 0) + 1
    print(f"parsed {len(parsed)} pages, parameters by use: {sorted(keys.items(), key=lambda kv: -kv[1])[:40]}")

if __name__ == "__main__":
    {"fetch": fetch, "parse": parse}[sys.argv[1] if len(sys.argv) > 1 else "fetch"]()
