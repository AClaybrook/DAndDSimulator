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
    characters = [Character.from_dict(c) for c in session["characters"]]
    _, df_by_rounds, _ = simulate_rounds_from_characters(characters, Enemy.from_dict(session["enemy"]), num_rounds=5000, save_memory=True,
                                                         rng=set_seed(4), rounds_per_fight=3)
    means = {c.name: df["Damage"].mean() for c, df in zip(characters, df_by_rounds)}
    assert {v["name"]: v["value"] for v in result["headline"]["values"]} == pytest.approx({k: round(v, 2) for k, v in means.items()})
    assert result["figure"]["data"] and any(t["name"].endswith("(exact)") for t in result["figure"]["data"] if t.get("name"))
    assert [t["title"] for t in result["tables"]] == ["Leaderboard", "Attack breakdown"]

@pytest.mark.parametrize("graph", ["DPA Distribution", "DPR Sweep", "DPA Sweep", "Rounds to Kill", "Damage per Fight"])
def test_every_graph(session, graph):
    result = client.post("/api/simulator/simulate", json={**session, "graph": graph, "num_rounds": 2000}).json()
    assert result["figure"]["data"] and result["headline"]["values"] and result["tables"]

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
    assert client.post("/api/planner/import-doc", json={"source": "https://example.com"}).json()["problems"]
