""" Act 1 map: data, calibration and the party's gear on it """
from api.map import DATA, POINTS, data, party_gear
from bg3.build_map import MAPS, WAYPOINTS, opaque_check, to_pixel
from bg3.presets import DEFAULT_PARTY, PRESETS

def test_waypoints_land_on_the_map():
    on_map = opaque_check()
    for name, (map_key, x, y) in WAYPOINTS.items():
        assert on_map(map_key, x, y), name

def test_points_are_placed():
    assert len(POINTS) > 200
    for p in POINTS:
        assert p["map"] in MAPS
        if MAPS[p["map"]]["image"]:
            assert (p["px"], p["py"]) == to_pixel(p["map"], p["x"], p["y"])
    names = {p["name"] for p in POINTS}
    for item in ["Phalar Aluve", "Sword of Justice", "Caustic Band", "Auntie Ethel's Hair", "The Blood of Lathander"]:
        assert item in names
    assert DATA["unplaced"]

def test_browser_data():
    d = data()
    assert {m["key"] for m in d["maps"]} == set(MAPS)
    assert all(m["image"] for m in d["maps"] if MAPS[m["key"]]["image"])
    assert not any(u["rarity"] == "Uncommon" for u in d["unplaced"])

def test_party_gear():
    gear = {r["key"]: r for r in party_gear([PRESETS[name].to_dict() for name in DEFAULT_PARTY], "1")}
    assert len(gear["bg3:caustic_band"]["users"]) == 2 # Lae'zel and Karlach both wear it
    assert gear["bg3:caustic_band"]["placed"] and gear["bg3:caustic_band"]["maps"]

def test_missables():
    missable = {p["name"]: p["missable"] for p in POINTS if p.get("missable")}
    assert "Story choice" in missable["Sussur Greatsword"] and "Story choice" in missable["The Sparky Points"]
    assert "Phalar Aluve" in missable and "Svartlebee's Woundseeker" in missable
    assert not any(p.get("missable") for p in POINTS if p["rarity"] == "Common" and p["map"] == "nautiloid" and not p.get("tip"))

def test_act2_spots():
    """ Act 2 items land in their places on the Shadow-Cursed Lands image: the Last Light Inn's island in the north, Moonrise Towers in the south """
    spots = {}
    for p in POINTS:
        if p["act"] == 2:
            spots.setdefault(p["name"], []).append(p)
    inn = spots["Hat of Fire Acuity"][0]
    moonrise = spots["Hat of Storm Scion's Power"][0]
    assert inn["map"] == moonrise["map"] == "shadowcursed"
    assert inn["py"] < 500 < 1100 < moonrise["py"]
    assert spots["Boots of Brilliance"][0]["map"] == "gauntlet" and spots["Infernal Rapier"][0]["map"] == "colony"
    assert {m["act"] for m in data()["maps"]} == {1, 2}
