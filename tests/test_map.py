""" Act 1 map: data, calibration and figures """
from bg3.build_map import MAPS, WAYPOINTS, opaque_check, to_pixel
from components.bg3_map import DATA, DEFAULT_RARITIES, POINTS, details, figure, groups, visible

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

def test_filters():
    rare = next(p for p in POINTS if p["rarity"] == "Rare" and not p["builds"])
    assert visible(rare, DEFAULT_RARITIES, [], [])
    assert not visible(rare, ["Legendary"], [], [])
    assert not visible(rare, DEFAULT_RARITIES, ["builds"], [])
    assert visible(rare, ["Legendary"], [], [rare["name"]]) # Searched items always show
    common = [p for p in POINTS if p["rarity"] == "Common"]
    assert all(not visible(p, DEFAULT_RARITIES, [], []) for p in common)

def test_figures_and_details():
    for map_key in MAPS:
        fig = figure(map_key, [*DEFAULT_RARITIES, "Uncommon", "Common"], [], [])
        assert fig.data, map_key
        assert bool(fig.layout.images) == bool(MAPS[map_key]["image"])
    spot, points = groups("wilderness", DEFAULT_RARITIES, [], [])[0]
    assert details(points)
    assert DATA["unplaced"]
