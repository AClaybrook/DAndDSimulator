""" The FastAPI backend returns the engine's numbers """
import pytest
from fastapi.testclient import TestClient

from api.main import app
from computations.analytic import expected_damage_per_round
from computations.models import Character, Enemy
from computations.numerical_simulation import set_seed, simulate_rounds_from_characters

client = TestClient(app)

@pytest.fixture(scope="module")
def session():
    return client.get("/api/simulator/default").json()

def test_options():
    options = client.get("/api/simulator/options").json()
    assert {p["key"] for p in options["presets"]} >= {"fighter_gwm", "paladin_smite"}
    assert any(e["value"] == "monster:Mind Flayer" for e in options["enemies"])
    assert [g["key"] for g in options["graphs"]][:2] == ["DPR Distribution", "DPA Distribution"]

def test_expected_matches_the_engine(session):
    result = client.post("/api/simulator/expected", json={**session, "rounds_per_fight": 3}).json()
    enemy = Enemy.from_dict(session["enemy"])
    for raw, row in zip(session["characters"], result["characters"]):
        assert row["damagePerRound"] == pytest.approx(expected_damage_per_round(Character.from_dict(raw), enemy, 3))
        assert sum(a["damage"] for a in row["attacks"]) == pytest.approx(row["damagePerRound"])

def test_simulation_matches_the_engine(session):
    result = client.post("/api/simulator/simulate", json={**session, "num_rounds": 5000, "seed": 4}).json()
    characters, enemy = [Character.from_dict(c) for c in session["characters"]], Enemy.from_dict(session["enemy"])
    _, df_by_rounds, _ = simulate_rounds_from_characters(characters, enemy, num_rounds=5000, save_memory=True,
                                                         rng=set_seed(4), rounds_per_fight=3)
    means = {c.name: df["Damage"].mean() for c, df in zip(characters, df_by_rounds)}
    # The headline is the exact expected damage (the number on each card), the simulated rounds agree with it
    headline = {v["name"]: v["value"] for v in result["headline"]["values"]}
    exact = {c.name: expected_damage_per_round(c, enemy, 3) for c in characters}
    assert headline == pytest.approx({k: round(v, 2) for k, v in exact.items()}) and headline == pytest.approx(dict(means), rel=0.03)
    chart = result["chart"]
    assert chart["kind"] == "distribution" and [s["name"] for s in chart["series"]] == [c.name for c in characters]
    assert all(s["curve"]["kind"] == "exact" and sum(s["percent"]) == pytest.approx(100, abs=0.1) for s in chart["series"])
    assert [t["title"] for t in result["tables"]] == ["Simulated rounds", "Attack breakdown"]

@pytest.mark.parametrize("graph", ["DPA Distribution", "DPR Sweep", "DPA Sweep", "Rounds to Kill", "Damage per Fight"])
def test_every_graph(session, graph):
    result = client.post("/api/simulator/simulate", json={**session, "graph": graph, "num_rounds": 2000}).json()
    assert result["chart"]["series"] and result["headline"]["values"] and result["tables"]

def test_problems_are_readable(session):
    broken = {**session, "characters": [{**session["characters"][0], "strength": None}]}
    assert client.post("/api/simulator/simulate", json=broken).json() == {"problems": ["Fighter: Strength is empty"]}
    twins = {**session, "characters": [session["characters"][0]] * 2}
    assert "unique" in client.post("/api/simulator/expected", json=twins).json()["problems"][0]

def test_presets_and_templates():
    paladin = client.post("/api/simulator/preset", json={"preset": "paladin_smite", "level": 8}).json()
    assert paladin["level"] == 8 and paladin["attacks"]
    attacks = client.post("/api/simulator/template", json={"value": "weapon:Greatsword:", "ability_stat": "strength"}).json()
    assert attacks[0]["damage"] == "2d6"
    assert client.get("/api/simulator/enemy", params={"value": "cr:5"}).json()["armor_class"] > 10

def test_planner_endpoints():
    options = client.get("/api/planner/options").json()
    party = options["defaultParty"]
    assert len(party) == 4 and options["items"]["melee"] and options["kits"]
    evaluation = client.post("/api/planner/evaluate", json={"party": party}).json()
    first = evaluation["members"][0]["acts"]
    assert set(first) == {"1", "2", "3"} and len(first["1"]["damage"]) == 4 and first["3"]["damage"][0] > first["1"]["damage"][0]
    assert any(c["kind"] == "shared" for c in evaluation["conflicts"]) # The default party shares a Caustic Band on purpose
    rows = client.post("/api/planner/variants", json={"build": {**party[0], "variants": [{"name": "Bless", "buffs": ["bless"]}]}}).json()
    assert [r["name"] for r in rows][1] == "Bless" and rows[1]["damage"][0] > rows[0]["damage"][0]
    assert all(len(r["byEnemies"]) == 3 and len(r["byEnemies"][0]) == 4 and r["byEnemies"][0][0] == r["damage"][0] for r in rows)
    # A caster: its spell save DC per act, each saving throw with the enemy's chance to fail, and play modes as variants
    reaper = client.get("/api/planner/example", params={"name": "4. Deathreaper"}).json()
    acts = client.post("/api/planner/evaluate", json={"party": [reaper]}).json()["members"][0]["acts"]
    assert acts["3"]["spellDc"] > acts["1"]["spellDc"] >= 13
    toll = next(s for s in acts["3"]["saves"] if s["name"] == "Toll the Dead")
    assert toll["stat"] == "wisdom" and toll["dc"] == acts["3"]["spellDc"] and toll["disadvantage"] and 0.5 < toll["fail"] <= 1
    modes = client.post("/api/planner/variants", json={"build": reaper, "enemies": 3}).json()
    by_name = {r["name"]: r for r in modes}
    assert {"Build as planned", "Circle of Death", "Thorn Whip"} <= set(by_name) and by_name["Circle of Death"]["spellDc"] == modes[0]["spellDc"]
    assert by_name["Thorn Whip"]["byEnemies"][2][0] > modes[0]["byEnemies"][2][0] # Touch of Death on one target
    assert by_name["Circle of Death"]["byEnemies"][2][3] > modes[0]["byEnemies"][2][3] # The area spell against four
    assert by_name["Circle of Death"]["damage"][2] == by_name["Circle of Death"]["byEnemies"][2][2]
    kit = client.post("/api/planner/kit", json={"party": party, "selected": 0, "kit": "thunder"}).json()
    assert kit["placed"] and kit["build"]["equipment"]["1"]
    analysis = client.post("/api/planner/party", json={"party": party, "act": "2"}).json()
    assert len(analysis["damage"]) == 4 and analysis["fight"]["down_by_round"]
    advice = client.post("/api/planner/advice", json={"party": party, "build": party[0], "slot": "gloves"}).json()
    assert advice["suggestions"]
    assert client.get("/api/planner/example", params={"name": "nope"}).status_code == 404

def test_leaderboard_and_map_endpoints():
    party = client.get("/api/planner/options").json()["defaultParty"]
    rows = client.post("/api/leaderboard/entries", json={"party": party}).json()
    mine = [r for r in rows if r["source"] == "Your party"]
    assert len(mine) >= 4 and all("reliable@1" in r["damage"] for r in mine)
    assert len({r["key"] for r in rows}) == len(rows)
    data = client.get("/api/map/data").json()
    assert len(data["points"]) > 200 and data["maps"][0]["image"].startswith("/assets/maps/")
    assert client.get(data["maps"][0]["image"]).status_code == 200
    gear = client.post("/api/map/party-gear", params={"act": "1"}, json={"party": party}).json()
    assert any(g["name"] == "Caustic Band" and len(g["users"]) == 2 for g in gear)

def test_variant_and_raw_exports():
    defaults = client.get("/api/simulator/default").json()
    options = client.get("/api/simulator/options").json()
    assert "copy" not in {v["key"] for v in options["variants"]} # Exact copies are made in the browser
    bless = client.post("/api/simulator/variant", json={"character": defaults["characters"][0], "key": "bless"}).json()
    assert bless["character"]["name"].endswith("(Bless)")
    asi = client.post("/api/simulator/variant", json={"character": defaults["characters"][0], "key": "ability"}).json()
    assert asi["problems"] # Strength is already 20
    for kind in options["exports"]:
        response = client.post("/api/simulator/export", json={**defaults, "kind": kind, "num_rounds": 500})
        assert response.status_code == 200 and response.headers["content-type"].startswith("text/csv"), kind
        assert len(response.text.splitlines()) > 2, kind

def test_party_to_simulator():
    party = client.get("/api/planner/options").json()["defaultParty"]
    at_act = client.post("/api/planner/to-simulator", json={"party": party, "act": "2"}).json()
    assert len(at_act) == 4 and all(c["attacks"] for c in at_act)
    every_act = client.post("/api/planner/to-simulator", json={"party": party, "selected": 0}).json()
    assert len(every_act) == 3 and len({c["name"] for c in every_act}) == 3

def test_build_doc_import(monkeypatch, tmp_path):
    import bg3.doc_import as doc_import
    assert client.post("/api/planner/import-doc", json={"source": "/etc/passwd"}).json()["problems"] # Links only, never local files
    text = "Build 1: Test Champion\nClass Split: Fighter (Champion) 12\nAbility Scores: STR 17, DEX 14, CON 16, INT 8, WIS 12, CHA 8\n"
    monkeypatch.setattr(doc_import, "fetch_text", lambda source: text)
    monkeypatch.setattr(doc_import, "OUT", tmp_path / "doc_builds.json")
    result = client.post("/api/planner/import-doc", json={"source": "https://docs.google.com/document/d/x/edit"}).json()
    assert [b["name"] for b in result["builds"]] == ["1. Test Champion"] and (tmp_path / "doc_builds.json").exists()
    monkeypatch.setattr(doc_import, "fetch_text", lambda source: "nothing here")
    assert client.post("/api/planner/import-doc", json={"source": "https://docs.google.com/document/d/y/edit"}).json()["problems"]
    # The server fetches the link itself, so only Google Docs links are followed
    for link in ["https://example.com", "http://169.254.169.254/latest/meta-data", "https://docs.google.com.evil.example/document/d/x"]:
        assert "Google Doc" in client.post("/api/planner/import-doc", json={"source": link}).json()["problems"][0]

def test_a_shared_copy_is_read_only(monkeypatch):
    """ With DAMAGE_LAB_READ_ONLY set (a hosted copy), visitors can't replace the example builds or write leaderboard runs """
    import api.main as main
    monkeypatch.setattr(main, "READ_ONLY", True)
    assert client.post("/api/planner/import-doc", json={"source": "https://docs.google.com/document/d/x/edit"}).status_code == 403
    assert client.post("/api/leaderboard/save", json={"party": [], "label": "x"}).status_code == 403
    assert client.get("/api/planner/options").json()["readOnly"] is True
    assert client.post("/api/planner/evaluate", json={"party": []}).status_code == 200 # Everything that only computes still works

def test_front_end_types_are_current():
    """ frontend/src/api-types.ts is generated from the API's schema; after a change to api/schemas.py run `uv run python -m api.openapi` """
    from api.openapi import PATH, types_text
    assert PATH.read_text(encoding="utf-8") == types_text(), "Run: uv run python -m api.openapi"

def test_builds_are_checked_on_the_way_in():
    """ A malformed build is refused with what is wrong, instead of failing somewhere inside the planner """
    response = client.post("/api/planner/evaluate", json={"party": [{"name": "Tav", "equipment": {"1": "a sword"}}]})
    assert response.status_code == 422 and "equipment" in response.text
    ok = client.post("/api/planner/evaluate", json={"party": [{"name": "Tav", "preset": "fighter_gwm", "unknown_field": 1}]})
    assert ok.status_code == 200 and ok.json()["members"][0]["name"] == "Tav"

def test_best_gear_and_deconflict():
    options = client.get("/api/planner/options").json()
    party = options["defaultParty"]
    best = client.post("/api/planner/best-gear", json={"party": party, "selected": 0, "acts": ["3"], "goal": "damage"}).json()
    assert best["changes"] and all(c["act"] == "3" for c in best["changes"]) and best["goal"] == "Most damage"
    before = client.post("/api/planner/evaluate", json={"party": party}).json()
    after = client.post("/api/planner/evaluate", json={"party": [best["build"], *party[1:]]}).json()
    assert after["members"][0]["acts"]["3"]["damage"][0] > before["members"][0]["acts"]["3"]["damage"][0]
    assert after["members"][0]["acts"]["1"]["damage"] == before["members"][0]["acts"]["1"]["damage"] # Only the act asked for
    # Nothing the rest of the party wears is taken, so no new conflicts
    assert len([c for c in after["conflicts"] if c["kind"] == "shared"]) <= len([c for c in before["conflicts"] if c["kind"] == "shared"])
    fixed = client.post("/api/planner/deconflict", json={"party": party}).json()
    assert fixed["steps"] and fixed["steps"][0]["item"] == "Caustic Band" and fixed["steps"][0]["keeper"] != fixed["steps"][0]["member"]
    settled = client.post("/api/planner/evaluate", json={"party": fixed["party"]}).json()
    assert not [c for c in settled["conflicts"] if c["kind"] == "shared"] and before["conflicts"]
