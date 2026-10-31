""" Builds the Act 1 item map: where notable items are found, placed on the game's minimap images.

    python -m bg3.build_map    -> assets/maps/*.webp (map images) and bg3/data/map_act1.json

    Item locations are the "where to find" x/y from bg3.wiki item pages (in-game minimap coordinates), read from bg3/data/raw/parsed.json
    (python -m bg3.scrape_wiki fetch && python -m bg3.scrape_wiki parse). Location pages are fetched for their region and entrance coordinates.
    Map images are the game's minimap textures as uploaded to bg3.wiki; they belong to Larian Studios.
    Each image is calibrated to minimap coordinates (pixel = (x - x0) * sx, (y0 - y) * sy), fitted to waypoints and checked by eye.
    Items inside a building or dungeon have coordinates of that interior level, which don't fit the outdoor map, so they are placed at
    the entrance instead """
import json
import re
import urllib.request
from pathlib import Path

from bg3.scrape_wiki import RAW, USER_AGENT, api, plain_text

DATA = Path(__file__).parent / "data"
ASSETS = Path(__file__).parent.parent / "assets" / "maps"
OUT = DATA / "map_act1.json"

MAPS = {
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
# Location page region -> map, following each location's "region" up to one of these
REGION_MAP = {"Wilderness": "wilderness", "Emerald Grove": "wilderness", "Forest": "wilderness", "Sunlit Wetlands": "wilderness",
              "Blighted Village": "wilderness", "Goblin Camp": "wilderness", "Shattered Sanctum": "wilderness", "Waukeen's Rest": "wilderness",
              "Riverside Teahouse": "wilderness", "Risen Road Toll House": "wilderness", "Decrepit Sanctuary": "wilderness", "Nautiloid": "nautiloid",
              "Underdark": "underdark", "Crèche Y'llek": "creche", "Grymforge": "grymforge", "Adamantine Forge": "grymforge",
              "Mountain Pass": "mountain", "Rosymorn Monastery Trail": "mountain", "Rosymorn Monastery": "mountain"}
# Interiors whose location pages give no outdoor entrance: placed at this location instead
ENTRANCE_OF = {"Shattered Sanctum": "Goblin Camp", "Worg Pens": "Goblin Camp", "Defiled Temple": "Goblin Camp", "Bloodied Shrine": "Goblin Camp",
               "Secluded Chamber": "Goblin Camp", "Dank Crypt": "Overgrown Ruins", "Creche Y'llek": "Crèche Y'llek"}
WAYPOINTS = {"Goblin Camp": ("wilderness", -74, 445), "Blighted Village": ("wilderness", 34, 394), "Riverside Teahouse": ("wilderness", -10, 250),
             "Waukeen's Rest": ("wilderness", -77, 570), "Emerald Grove": ("wilderness", 246, 423), "Overgrown Ruins": ("wilderness", 276, 298)}
ACT1_LOCATION_CATEGORIES = ["Category:Act One Locations", "Category:Prologue Locations"]
RARITY_ORDER = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Story"]

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

def fetch_locations():
    """ {location title: wikitext} for Act 1 locations, cached in bg3/data/raw/locations.json """
    cache = RAW / "locations.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    titles = []
    for category in ACT1_LOCATION_CATEGORIES:
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

def region_of(location, regions):
    """ The map a location is on, following location page regions """
    seen = set()
    name = ENTRANCE_OF.get(location, location)
    while name and name not in seen:
        seen.add(name)
        if name in REGION_MAP:
            return REGION_MAP[name]
        name = regions.get(name, "")
    return None

def entrances(pages, regions, on_map):
    """ {location: (map, x, y)} the first coordinates on each location page that fall on the outdoor map """
    found = dict(WAYPOINTS)
    for title, text in pages.items():
        map_key = region_of(title, regions)
        if title in found or map_key is None:
            continue
        for x, y in re.findall(r"\{\{\s*[Cc]oords\s*\|\s*(-?\d+)\s*\|\s*(-?\d+)", text):
            if MAPS[map_key]["image"] is None or on_map(map_key, int(x), int(y)):
                found[title] = (map_key, int(x), int(y))
                break
    return found

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
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"

def build():
    download_images()
    on_map = opaque_check()
    pages = fetch_locations()
    regions = {}
    for title, text in pages.items():
        match = re.search(r"\|\s*region\s*=\s*([^\n|}]*)", text)
        regions[title] = match.group(1).strip() if match else ""
    doors = entrances(pages, regions, on_map)
    items = {i["name"]: i for i in json.loads((DATA / "items.json").read_text(encoding="utf-8"))["items"]}
    parsed = {p["title"]: p for p in json.loads((RAW / "parsed.json").read_text(encoding="utf-8"))}
    users = builds_using()

    points, unplaced = [], []
    for name, item in items.items():
        params = parsed.get(name, {}).get("params", {})
        base = {"name": name, "key": item["key"], "rarity": item["rarity"] or "Common", "slot": item["slot"], "kind": "item",
                "source": item["source"], "notes": short(item.get("notes") or "", 260), "builds": users.get(item["key"], [])}
        placed = False
        for suffix in ("", "2", "3", "4", "5"):
            where = params.get(f"where to find{suffix}", "")
            location = params.get(f"where to find{suffix} location", "").strip()
            x, y = params.get(f"where to find{suffix} x", ""), params.get(f"where to find{suffix} y", "")
            if not (where or location):
                continue
            map_key = region_of(location, regions) if location else None
            if map_key is None:
                continue
            point = {**base, "location": location, "where": short(plain_text(where)), "trader": bool(re.match(r"\s*(sold|traded) by", where, re.I)),
                     "map": map_key, "inside": False}
            if x and y and (MAPS[map_key]["image"] is None or on_map(map_key, int(x), int(y))):
                point.update(x=int(x), y=int(y))
            elif (door := doors.get(ENTRANCE_OF.get(location, location))) and door[0] == map_key:
                point.update(x=door[1], y=door[2], inside=True)
            else:
                continue
            points.append(point)
            placed = True
        if not placed and item["act"] == 1 and item["rarity"] not in ("Common", "", None):
            unplaced.append({**base, "location": item.get("location") or "", "where": short(plain_text(params.get("where to find", "")))})

    for pickup in json.loads((DATA / "map_pickups.json").read_text(encoding="utf-8"))["pickups"]:
        points.append({"key": None, "rarity": "Key", "slot": None, "trader": False, "inside": False, "notes": "", "builds": [],
                       "map": pickup["region"], **pickup})
    for point in points:
        pixel = to_pixel(point["map"], point["x"], point["y"])
        point["px"], point["py"] = pixel if pixel else (None, None)
    maps = {key: {k: v for k, v in m.items() if k != "wiki_file"} for key, m in MAPS.items()}
    output = {"_source": "Item locations from bg3.wiki (CC BY-NC-SA 4.0); map images are the game's minimap textures (Larian Studios) via bg3.wiki",
              "maps": maps, "points": points, "unplaced": sorted(unplaced, key=lambda p: -RARITY_ORDER.index(p["rarity"]))}
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(points)} points, {len(unplaced)} notable Act 1 items without a location on a map")

if __name__ == "__main__":
    build()
