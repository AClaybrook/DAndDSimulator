""" Builds the Act 1 and Act 2 item maps: where notable items are found, placed on the game's minimap images.

    python -m bg3.build_map    -> assets/maps/*.webp (map images), bg3/data/map_act1.json and bg3/data/map_act2.json

    Item locations are the "where to find" x/y from bg3.wiki item pages (in-game minimap coordinates), read from bg3/data/raw/parsed.json
    (python -m bg3.scrape_wiki fetch && python -m bg3.scrape_wiki parse). Location pages are fetched for their region and entrance coordinates.
    Map images are the game's minimap textures as uploaded to bg3.wiki; they belong to Larian Studios.
    Each image is calibrated to minimap coordinates (pixel = (x - x0) * sx, (y0 - y) * sy), fitted to waypoints and checked by eye
    (Act 2: fitted to the marker positions on bg3.wiki's "Shadow-Cursed Lands (Map)" page, then checked with the item spots).
    Items inside a building or dungeon have coordinates of that interior level, which don't fit the outdoor map, so they are placed at
    the entrance instead """
import json
import re
import urllib.request
from pathlib import Path

from bg3.scrape_wiki import RAW, USER_AGENT, api, plain_text

DATA = Path(__file__).parent / "data"
ASSETS = Path(__file__).parent.parent / "assets" / "maps"

ACT1_MAPS = {
    "wilderness": {"label": "Wilderness", "image": "wilderness.webp", "wiki_file": "Map_Wilderness_A_Terrain_Tex.webp",
                   "width": 1438, "height": 1222, "x0": -178, "y0": 648, "sx": 2.64, "sy": 2.64},
    "underdark": {"label": "Underdark", "image": "underdark.webp", "wiki_file": "Map_Underdark_A_Terrain_Tex.webp",
                  "width": 896, "height": 896, "x0": -156, "y0": 29.5, "sx": 2.3, "sy": 2.3},
    "creche": {"label": "Crèche Y'llek", "image": "creche.webp", "wiki_file": "Map_Crèche_Y'llek_A_Terrain_Tex.webp",
               "width": 1280, "height": 1280, "x0": 1253.7, "y0": -628.5, "sx": 6.0, "sy": 5.5},
    # No minimap image on the wiki: plotted on a plain grid of minimap coordinates
    "grymforge": {"label": "Grymforge", "image": None},
    "mountain": {"label": "Mountain Pass & Monastery", "image": None},
    "nautiloid": {"label": "Nautiloid (prologue)", "image": None},
}
ACT2_MAPS = {
    "shadowcursed": {"label": "Shadow-Cursed Lands", "image": "shadowcursed.webp", "wiki_file": "Map_Shadow-Cursed_Lands_A_Terrain_Tex.webp",
                     "width": 1408, "height": 1536, "x0": -375.2, "y0": 338.8, "sx": 2.273, "sy": 2.214},
    "gauntlet": {"label": "Gauntlet of Shar", "image": None},
    "shadowfell": {"label": "Shadowfell & Cloister", "image": None},
    "colony": {"label": "Mind Flayer Colony", "image": None},
}
MAPS = {**ACT1_MAPS, **ACT2_MAPS}
# Location page region -> map, following each location's "region" up to one of these
ACT1_REGIONS = {"Wilderness": "wilderness", "Emerald Grove": "wilderness", "Forest": "wilderness", "Sunlit Wetlands": "wilderness",
              "Blighted Village": "wilderness", "Goblin Camp": "wilderness", "Shattered Sanctum": "wilderness", "Waukeen's Rest": "wilderness",
              "Riverside Teahouse": "wilderness", "Risen Road Toll House": "wilderness", "Decrepit Sanctuary": "wilderness", "Nautiloid": "nautiloid",
              "Underdark": "underdark", "Crèche Y'llek": "creche", "Grymforge": "grymforge", "Adamantine Forge": "grymforge",
              "Mountain Pass": "mountain", "Rosymorn Monastery Trail": "mountain", "Rosymorn Monastery": "mountain"}
# Interiors whose location pages give no outdoor entrance: placed at this location instead
ACT1_ENTRANCES = {"Shattered Sanctum": "Goblin Camp", "Worg Pens": "Goblin Camp", "Defiled Temple": "Goblin Camp", "Bloodied Shrine": "Goblin Camp",
               "Secluded Chamber": "Goblin Camp", "Dank Crypt": "Overgrown Ruins", "Hidden Vault": "Emerald Grove", "Creche Y'llek": "Crèche Y'llek"}
ACT1_WAYPOINTS = {"Goblin Camp": ("wilderness", -74, 445), "Blighted Village": ("wilderness", 34, 394), "Riverside Teahouse": ("wilderness", -10, 250),
                  "Waukeen's Rest": ("wilderness", -77, 570), "Emerald Grove": ("wilderness", 246, 423), "Overgrown Ruins": ("wilderness", 276, 298)}
ACT2_REGIONS = {"Shadow-Cursed Lands": "shadowcursed", "Last Light Inn": "shadowcursed", "Reithwin Town": "shadowcursed", "Ruined Battlefield": "shadowcursed",
                "Moonrise Towers": "shadowcursed", "Reithwin Graveyard": "shadowcursed", "Gauntlet of Shar": "gauntlet", "Shadowfell": "shadowfell",
                "Cloister of Sombre Embrace": "shadowfell", "Mind Flayer Colony": "colony", "Necrotic Laboratory": "colony", "Tadpoling Centre": "colony"}
# Interiors (their own coordinates don't fit the outdoor map) shown at the building's door
ACT2_ENTRANCES = {"House of Healing Morgue": "House of Healing", "Last Light Inn - Cellar": "Last Light Inn", "Moonrise Towers Prison": "Moonrise Towers",
                  "Moonrise Towers Rooftop": "Moonrise Towers", "Oubliette": "Moonrise Towers", "High Hall": "Moonrise Towers",
                  "Reithwin Graveyard": "Grand Mausoleum"}
# From the wiki's map markers, each matched to a coordinate on the location's page
ACT2_WAYPOINTS = {"Last Light Inn": ("shadowcursed", -10, 166), "Grand Mausoleum": ("shadowcursed", -174, 102), "Reithwin Town": ("shadowcursed", -78, -46),
                  "Sharran Sanctuary": ("shadowcursed", -152, -30), "Reithwin Tollhouse": ("shadowcursed", -107, -100),
                  "Ruined Battlefield": ("shadowcursed", 68, 36), "Mason's Guild": ("shadowcursed", -127, 26),
                  "House of Healing": ("shadowcursed", -199, 67), "Moonrise Towers": ("shadowcursed", -179, -198)}
WAYPOINTS = {**ACT1_WAYPOINTS, **ACT2_WAYPOINTS}
ACTS = {
    1: {"maps": ACT1_MAPS, "regions": ACT1_REGIONS, "entrances": ACT1_ENTRANCES, "waypoints": ACT1_WAYPOINTS, "cache": "locations.json",
        "categories": ["Category:Act One Locations", "Category:Prologue Locations"], "checklist": True},
    2: {"maps": ACT2_MAPS, "regions": ACT2_REGIONS, "entrances": ACT2_ENTRANCES, "waypoints": ACT2_WAYPOINTS, "cache": "locations_act2.json",
        "categories": ["Category:Act Two Locations"], "checklist": False},
}
RARITY_ORDER = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Story"]
# Community "BG3 Every Item Run (ACT 1)" checklist (published Google Sheet): location text with minimap coordinates and playthrough notes
CHECKLIST_URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vTKfLHIXxsRwE9ad533L8-HbkmaWyfXpOs4RFLqe6xc7PERdFm1VuQzueFT0Gepo4JD5fiW5IrLZ_mE"
                 "/pubhtml/sheet?headers=false&gid=0")
# Words in a checklist location that name the map it's on, checked in order
CHECKLIST_MAPS = [("nautiloid wreck", "wilderness"), ("grymforge", "grymforge"), ("adamantine", "grymforge"), ("crèche", "creche"), ("creche", "creche"), ("nautiloid", "nautiloid"),
                  ("mountain pass", "mountain"), ("rosymorn", "mountain"), ("underdark", "underdark"), ("ebonlake", "underdark"),
                  ("arcane tower", "underdark"), ("myconid", "underdark"), ("selûnite", "underdark")]

def to_pixel(map_key, x, y):
    m = MAPS[map_key]
    if not m["image"]:
        return None
    px, py = (x - m["x0"]) * m["sx"], (m["y0"] - y) * m["sy"]
    return (round(px, 1), round(py, 1)) if 0 <= px < m["width"] and 0 <= py < m["height"] else None

def download_images():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for m in MAPS.values():
        if not m["image"] or (ASSETS / m["image"]).exists():
            continue
        info = api(action="query", titles=f"File:{m['wiki_file']}", prop="imageinfo", iiprop="url")
        url = info["query"]["pages"][0]["imageinfo"][0]["url"]
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            (ASSETS / m["image"]).write_bytes(response.read())

def opaque_check():
    """ (map, x, y) -> whether that point is on the drawn part of the map image (the rest is transparent) """
    from PIL import Image
    alpha = {}
    for key, m in MAPS.items():
        if m["image"]:
            image = Image.open(ASSETS / m["image"]).convert("RGBA")
            alpha[key] = image
    def check(map_key, x, y):
        pixel = to_pixel(map_key, x, y)
        if pixel is None:
            return False
        r, g, b, a = alpha[map_key].getpixel((int(pixel[0]), int(pixel[1])))
        return a > 200 and r + g + b > 60
    return check

def fetch_locations(act=1):
    """ {location title: wikitext} for an act's locations, cached in bg3/data/raw """
    cache = RAW / ACTS[act]["cache"]
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    titles = []
    for category in ACTS[act]["categories"]:
        result = api(action="query", list="categorymembers", cmtitle=category, cmlimit=500)
        titles += [m["title"] for m in result["query"]["categorymembers"]]
    pages = {}
    for start in range(0, len(titles), 50):
        result = api(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[start:start + 50]), redirects=1)
        for page in result["query"]["pages"]:
            if page.get("revisions"):
                pages[page["title"]] = page["revisions"][0]["slots"]["main"]["content"]
    cache.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    return pages

def region_of(location, regions, act=1):
    """ The map a location is on, following location page regions """
    seen = set()
    name = ACTS[act]["entrances"].get(location, location)
    while name and name not in seen:
        seen.add(name)
        if name in ACTS[act]["regions"]:
            return ACTS[act]["regions"][name]
        name = regions.get(name, "")
    return None

def entrances(pages, regions, on_map, act=1):
    """ {location: (map, x, y)} the first coordinates on each location page that fall on the outdoor map """
    found = dict(ACTS[act]["waypoints"])
    for title, text in pages.items():
        map_key = region_of(title, regions, act)
        if title in found or map_key is None:
            continue
        for x, y in re.findall(r"\{\{\s*[Cc]oords\s*\|\s*(-?\d+)\s*\|\s*(-?\d+)", text):
            if MAPS[map_key]["image"] is None or on_map(map_key, int(x), int(y)):
                found[title] = (map_key, int(x), int(y))
                break
    return found

def fetch_checklist():
    """ {item name: {"location": text, "notes": text}} from the Act 1 checklist, cached in bg3/data/raw/act1_checklist.json """
    cache = RAW / "act1_checklist.json"
    if not cache.exists():
        import html
        request = urllib.request.Request(CHECKLIST_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            page = response.read().decode("utf-8")
        rows = {}
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
            cells = [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            cells = [c for c in cells if c and c not in ("TRUE", "FALSE")]
            # Item rows are name, rarity, location and optional notes; one cell rows are section headings
            if len(cells) >= 3 and cells[0] != "Name":
                rows.setdefault(cells[0], {"location": cells[2], "notes": " ".join(cells[3:])})
        cache.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return json.loads(cache.read_text(encoding="utf-8"))

def checklist_spot(text, on_map):
    """ (map, x, y) from a checklist location like "Grymforge X: -643 Y: 215: ...", or None """
    match = re.search(r"X\s*:?\s*(-?\d+)\s*,?\s*Y\s*:?\s*(-?\d+)", text)
    if not match:
        return None
    x, y = int(match.group(1)), int(match.group(2))
    lower = text.lower()
    named = next((m for word, m in CHECKLIST_MAPS if word in lower), None)
    for map_key in [named] if named else ["wilderness"]:
        if MAPS[map_key]["image"] is None or on_map(map_key, x, y):
            return map_key, x, y
    return None

# Checklist notes that mean an item can be missed: one-of rewards, time limits, a check or a choice to make
MISSABLE_NOTE = re.compile(r"mutually exclusive|before (?:leaving|the first|beginning)|must (?:succeed|return|be|complete)|return the chest unopened|"
                           r"easily missable|only (?:obtainable|be obtained|revealed|be bought)|can only (?:make|be obtained|be bought)|"
                           r"only two adamantine|^pickpocket|disarm|they drink them", re.I)

def missable_reasons():
    """ {item key: reason} from the story choices (bg3/data/story_choices.json) """
    from bg3.party import story_choices # pylint: disable=import-outside-toplevel
    reasons = {}
    for choice in story_choices():
        paths = choice["paths"]
        for path, keys in paths.items():
            others = [p for p in paths if p != path]
            for key in keys:
                reasons[key] = f"Story choice ({choice['quest']}): only with '{path}', not with {' / '.join(others)}"
    return reasons

def missable(point, reasons):
    """ Why an item can be missed, or "" """
    if point.get("key") in reasons:
        return reasons[point["key"]]
    tip = point.get("tip", "")
    if tip and MISSABLE_NOTE.search(tip) and "underwear" not in point["name"].lower():
        return tip
    if point.get("map") == "nautiloid" and point.get("rarity") not in ("Common", None):
        return "Prologue: take it before leaving the Nautiloid"
    return ""

def builds_using():
    """ {item key: [example build names]} for gear in the planner's example and doc builds """
    from bg3.presets import examples
    users = {}
    for name, build in examples().items():
        keys = {key for act in build.equipment.values() for key in act.values() if key}
        for key in keys:
            users.setdefault(key, []).append(name)
    return users

def short(text, limit=220):
    # Leftover template options from the wiki text (radius m=1.5 ft=5, level=0) and coordinate pairs
    text = re.sub(r"\b[a-z]+\s*=\s*\S+", "", text)
    text = re.sub(r"\s+-?\d+\s+-?\d+\s*$", "", text)
    text = re.sub(r"\b(\w+(?: \w+)?) \1('s)?\b", r"\1\2", text) # Character links keep the name and its alias: "Minthara Minthara's"
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"

def build(act=1):
    download_images()
    on_map = opaque_check()
    config = ACTS[act]
    pages = fetch_locations(act)
    regions = {}
    for title, text in pages.items():
        match = re.search(r"\|\s*region\s*=\s*([^\n|}]*)", text)
        regions[title] = match.group(1).strip() if match else ""
    doors = entrances(pages, regions, on_map, act)
    items = {i["name"]: i for i in json.loads((DATA / "items.json").read_text(encoding="utf-8"))["items"]}
    parsed = {p["title"]: p for p in json.loads((RAW / "parsed.json").read_text(encoding="utf-8"))}
    users = builds_using()
    checklist = fetch_checklist() if config["checklist"] else {}

    points, unplaced = [], []
    for name, item in items.items():
        params = parsed.get(name, {}).get("params", {})
        base = {"name": name, "key": item["key"], "rarity": item["rarity"] or "Common", "slot": item["slot"], "kind": "item",
                "source": item["source"], "notes": short(item.get("notes") or "", 260), "builds": users.get(item["key"], []),
                "tip": checklist.get(name, {}).get("notes", "")}
        placed = False
        for suffix in ("", "2", "3", "4", "5"):
            where = params.get(f"where to find{suffix}", "")
            location = params.get(f"where to find{suffix} location", "").strip()
            x, y = params.get(f"where to find{suffix} x", ""), params.get(f"where to find{suffix} y", "")
            if not (where or location):
                continue
            map_key = region_of(location, regions, act) if location else None
            if map_key is None:
                continue
            point = {**base, "location": location, "where": short(plain_text(where)), "trader": bool(re.match(r"\s*(sold|traded) by", where, re.I)),
                     "map": map_key, "inside": False}
            if x and y and (MAPS[map_key]["image"] is None or on_map(map_key, int(x), int(y))):
                point.update(x=int(x), y=int(y))
            elif (door := doors.get(config["entrances"].get(location, location))) and door[0] == map_key:
                point.update(x=door[1], y=door[2], inside=True)
            else:
                continue
            points.append(point)
            placed = True
        # Items without a usable wiki location, placed from the checklist's coordinates
        if not placed and name in checklist and (spot := checklist_spot(checklist[name]["location"], on_map)):
            text = checklist[name]["location"]
            # Checklist text starts with a place name ("Grymforge X: ..."), or is a sentence that doesn't
            location = re.split(r"\s*[(:]|\s+X\s*:", text)[0].strip()
            if len(location.split()) > 4 or not location[:1].isupper():
                location = MAPS[spot[0]]["label"]
            points.append({**base, "location": location, "where": short(text), "trader": bool(re.match(r"\s*sold by", text, re.I)),
                           "map": spot[0], "inside": False, "x": spot[1], "y": spot[2], "from_checklist": True})
            placed = True
        if not placed and item["act"] == act and item["rarity"] not in ("Common", "", None):
            unplaced.append({**base, "location": item.get("location") or "", "where": short(plain_text(params.get("where to find", "")))})

    for pickup in json.loads((DATA / "map_pickups.json").read_text(encoding="utf-8"))["pickups"]:
        if pickup["region"] not in config["maps"]:
            continue
        points.append({"key": None, "rarity": "Key", "slot": None, "trader": False, "inside": False, "notes": "", "builds": [], "tip": "",
                       "map": pickup["region"], **pickup})
    reasons = missable_reasons()
    for point in [*points, *unplaced]:
        point["missable"] = missable(point, reasons)
    for point in points:
        pixel = to_pixel(point["map"], point["x"], point["y"])
        point["px"], point["py"] = pixel if pixel else (None, None)
    maps = {key: {k: v for k, v in m.items() if k != "wiki_file"} for key, m in config["maps"].items()}
    sources = "bg3.wiki (CC BY-NC-SA 4.0)" + (" and the community BG3 Every Item Run (ACT 1) checklist" if config["checklist"] else "")
    output = {"_source": f"Item locations from {sources}; map images are the game's minimap textures (Larian Studios) via bg3.wiki", "act": act,
              "maps": maps, "points": points, "unplaced": sorted(unplaced, key=lambda p: -RARITY_ORDER.index(p["rarity"]))}
    (DATA / f"map_act{act}.json").write_text(json.dumps(output, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"Act {act}: {len(points)} points, {len(unplaced)} notable items without a location on a map")

if __name__ == "__main__":
    for act_number in ACTS:
        build(act_number)
