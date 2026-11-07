""" Exports the community BG3 unique item checklist (a Google Sheet with one tab per area, built from bg3.wiki) as a cross reference.

    python -m bg3.scrape_sheet   -> bg3/data/raw/sheet_items.json (not committed)

    build_items.py uses its tab (area) to check and fill in the act an item is found in, and reports items it lists that the wiki export lacks """
import csv
import io
import json
import re
import time
import urllib.request

from bg3.scrape_wiki import RAW, USER_AGENT

SHEET_ID = "1_NB-e5uW8BkMlDUBMHe6E4ccRdfqbQC9Fe9gwbd5s_k"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
# Area tab: act
TAB_ACTS = {"Druid Grove": 1, "Blighted Village": 1, "Goblin Camp": 1, "Waukeen's Rest": 1, "Underdark": 1, "Grymforge": 1,
            "Rosymorn Monastery": 1, "Shadow-Cursed Lands": 2, "Reithwin Town": 2, "Moonrise Towers": 2, "Gauntlet of Shar": 2,
            "Rivington": 3, "Wyrm's Rock": 3, "Lower City - East": 3, "House of Hope": 3, "Lower City - West": 3, "Lower City Sewers": 3}

def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")

def tabs():
    """ (tab name, gid) from the sheet's html view """
    html = get(f"{SHEET_URL}/htmlview")
    found = re.findall(r'\{name: "([^"]+)", pageUrl: "[^"]+", gid: "(\d+)"', html)
    return [(name.encode().decode("unicode_escape"), gid) for name, gid in found]

def fetch():
    items = []
    for name, gid in tabs():
        if name not in TAB_ACTS:
            continue
        rows = list(csv.reader(io.StringIO(get(f"{SHEET_URL}/gviz/tq?tqx=out:csv&gid={gid}"))))
        section = ""
        for row in rows:
            if len(row) >= 6 and row[1] == "Name": # Each area has sections with their own header row
                section = row[0].strip()
            elif len(row) >= 6 and row[1].strip():
                items.append({"tab": name, "act": TAB_ACTS[name], "section": section, "name": row[1].strip(), "type": row[2].strip(),
                              "enchantment": row[3].strip(), "description": row[4].strip(), "location": row[5].strip()})
        time.sleep(0.5)
    RAW.mkdir(parents=True, exist_ok=True)
    with open(RAW / "sheet_items.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=1, ensure_ascii=False)
    print(f"{len(items)} items from {len(TAB_ACTS)} areas")

if __name__ == "__main__":
    fetch()
