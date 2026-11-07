""" The Act 1 map's data for the browser, which filters and draws it (so every filter change is instant), and the party's gear on it """
from bg3.build import Bg3Build, equipment_at
from bg3.items import SLOT_LABELS, catalog
from components.bg3_map import COLORS, DATA, DEFAULT_RARITIES, MAPS, MISSABLE_COLOR, PARTY_COLOR, POINTS, RARITIES

def data():
    return {
        "maps": [{"key": k, "label": m["label"], "image": f"/assets/maps/{m['image']}" if m["image"] else None,
                  "width": m.get("width"), "height": m.get("height")} for k, m in MAPS.items()],
        "points": POINTS,
        "unplaced": [u for u in DATA["unplaced"] if u["rarity"] != "Uncommon"],
        "rarities": RARITIES,
        "defaultRarities": DEFAULT_RARITIES,
        "colors": COLORS,
        "partyColor": PARTY_COLOR,
        "missableColor": MISSABLE_COLOR,
    }

def party_gear(party_dicts, act):
    """ The party's planned gear at an act: [{key, name, users, where, missable, placed}], items on the maps first """
    items = catalog()
    users = {}
    for raw in party_dicts or []:
        build = Bg3Build.from_dict(raw)
        for slot, key in equipment_at(build, str(act)).items():
            if key and not key.startswith("base:"):
                users.setdefault(key, []).append(f"{build.name} ({SLOT_LABELS.get(slot, slot)})")
    rows = []
    for key, who in users.items():
        spots = [p for p in POINTS if p["key"] == key]
        unplaced = next((u for u in DATA["unplaced"] if u["key"] == key), None)
        where = "; ".join(sorted({f"{p['location']} ({MAPS[p['map']]['label']})" for p in spots})) or \
            ((unplaced["where"] or unplaced["location"]) if unplaced else "") or "not on the Act 1 maps"
        missable = next((p["missable"] for p in [*spots, *([unplaced] if unplaced else [])] if p.get("missable")), "")
        rows.append({"key": key, "name": items[key].name if key in items else key, "users": who, "where": where, "missable": missable,
                     "placed": bool(spots), "maps": sorted({p["map"] for p in spots})})
    return sorted(rows, key=lambda r: (not r["placed"], r["name"]))
