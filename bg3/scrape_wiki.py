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
TEMPLATES = ["Template:Weapon page", "Template:Equipment page"]
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
    """ Top level |key=value parameters of the first use of a template, nested templates and links are kept as text.
        The name matches any case and with or without spaces, i.e. 'Weapon page' matches {{WeaponPage and {{weapon page """
    pattern = r"\{\{\s*" + r"\s*".join(re.escape(word) for word in template_name.split()) + r"\s*(?=[|\n}])"
    match = re.search(pattern, text, re.I)
    if match is None and " " not in template_name:
        match = re.search(r"\{\{\s*" + re.escape(template_name) + r"\s*(?=[|\n}])", text, re.I)
    if match is None:
        return {}
    start = match.start()
    depth, ii, body_start = 0, start, match.end()
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
    value = re.sub(r"\s*see (?:bugs|notes)\b", "", value) # Footnote markers
    return re.sub(r"'{2,}", "", value).strip()

def parse():
    parsed = []
    with open(RAW / "pages.jsonl", encoding="utf-8") as f:
        for line in f:
            page = json.loads(line)
            # Pages use the template's short names, i.e. {{WeaponPage for Template:Weapon page
            name = page["template"].split(":", 1)[1]
            params = template_params(page["wikitext"], name)
            parsed.append({"title": page["title"], "template": page["template"], "timestamp": page["timestamp"],
                           "source": f"https://bg3.wiki/wiki/{urllib.parse.quote(page['title'].replace(' ', '_'))}",
                           "params": {k: plain_text(v) for k, v in params.items()},
                           "categories": re.findall(r"\[\[Category:([^\]|]+)", page["wikitext"]),
                           # Items that can't be found in a normal playthrough
                           "unobtainable": bool(re.search(r"\{\{\s*(?:unobtainable|inaccessible|unusable)\s*\}\}", page["wikitext"], re.I))})
    with open(RAW / "parsed.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=1)
    keys = {}
    for p in parsed:
        for k in p["params"]:
            keys[k] = keys.get(k, 0) + 1
    print(f"parsed {len(parsed)} pages, parameters by use: {sorted(keys.items(), key=lambda kv: -kv[1])[:40]}")

def fetch_passives():
    """ The passive feature pages the parsed items use, most item effects are described there """
    with open(RAW / "parsed.json", encoding="utf-8") as f:
        parsed = json.load(f)
    names = sorted({n.strip() for p in parsed for k in ("passives", "passives main hand", "passives off hand")
                    for n in (p["params"].get(k) or "").split(",") if n.strip()})
    passives = {}
    for ii in range(0, len(names), BATCH):
        passives.update({title: text for title, (text, _) in wikitext(names[ii:ii + BATCH]).items()})
        time.sleep(0.5)
    with open(RAW / "passives.json", "w", encoding="utf-8") as f:
        json.dump(passives, f)
    print(f"fetched {len(passives)} of {len(names)} passive features")

def act_categories():
    """ Locations and characters by act, used to work out where items are found """
    def members(category):
        out, params = [], {"action": "query", "list": "categorymembers", "cmtitle": category, "cmlimit": 500}
        while True:
            data = api(**params)
            out += [m["title"] for m in data["query"]["categorymembers"]]
            if "continue" not in data:
                return out
            params.update(data["continue"])
            time.sleep(0.3)
    categories = ["Category:Prologue Locations", "Category:Act One Locations", "Category:Act Two Locations", "Category:Act Three Locations",
                  "Category:Characters in Act One", "Category:Characters in Act Two", "Category:Characters in Act Three"]
    with open(RAW / "act_categories.json", "w", encoding="utf-8") as f:
        json.dump({c: members(c) for c in categories}, f)

def fetch_elixirs():
    """ Elixir pages, some are damage buffs """
    data = api(action="query", list="categorymembers", cmtitle="Category:Elixirs", cmlimit=500)
    titles = [m["title"] for m in data["query"]["categorymembers"]]
    pages = {}
    for ii in range(0, len(titles), BATCH):
        pages.update({title: text for title, (text, _) in wikitext(titles[ii:ii + BATCH]).items()})
    with open(RAW / "elixirs.json", "w", encoding="utf-8") as f:
        json.dump(pages, f)
    print(f"fetched {len(pages)} elixirs")

if __name__ == "__main__":
    steps = {"fetch": fetch, "parse": parse, "passives": fetch_passives, "acts": act_categories, "elixirs": fetch_elixirs}
    for step in sys.argv[1:] or ["fetch", "parse", "passives", "acts", "elixirs"]:
        steps[step]()
