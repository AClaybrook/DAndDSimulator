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
