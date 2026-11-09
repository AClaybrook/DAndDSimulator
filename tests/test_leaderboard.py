""" Damage leaderboard: fair scenarios, enemy counts, gear variants, fingerprints, the database and the doc build repairs """
from copy import deepcopy

from bg3.leaderboard import (SCENARIOS, area_options, compare, entries_for, entry, fingerprint, key, overall, ranked, reliable_advantage,
                             scenario_build, view)
from bg3.presets import PRESETS

def test_scenarios_give_everyone_the_same_help():
    build = deepcopy(PRESETS["Lae'zel (Champion, GWM)"])
    build.buffs = {"1": ["haste", "hex"]}
    plain, rounds, held = scenario_build(build, "plain")
    assert plain.buffs["1"] == ["hex"] and not plain.advantage and rounds == 3 and not held # Party buffs go, self cast ones stay
    blessed, _, _ = scenario_build(build, "bless_advantage")
    assert blessed.buffs["2"] == ["bless"] and blessed.advantage
    reliable, _, _ = scenario_build(build, "reliable")
    assert reliable.buffs["1"] == ["haste", "hex", "bless"] and not reliable.advantage # Its own buffs and Bless, a Champion has no reliable advantage
    nova, rounds, held = scenario_build(build, "nova")
    assert {"bless", "haste", "phalar_sing"} <= set(nova.buffs["3"]) and nova.advantage and rounds == 1 and held
    assert scenario_build(build, "planned")[0] is build
    values = entry("x", build)["damage"]
    for act in "123":
        assert values[view("advantage")][act] > values[view("plain")][act]
        assert values[view("bless_advantage")][act] >= values[view("advantage")][act]
        assert values[view("nova")][act] > 1.5 * values[view("reliable")][act]

def test_reliable_advantage_sources():
    assert reliable_advantage(PRESETS["Astarion (Assassin, dual wield)"], "1")
    assert reliable_advantage(PRESETS["Karlach (Berserker)"], "1") == "Reckless Attack"
    assert not reliable_advantage(PRESETS["Gale (Evoker)"], "1")
    from bg3.presets import examples
    assert "Shadow Blade" in reliable_advantage(examples()["1. The Godblade"], "1")

def test_more_enemies_use_area_options():
    from bg3.presets import examples
    builds = examples()
    cleric = builds["14. Death Cleric Necromancer"]
    assert "Spirit Guardians" in [label for label, _ in area_options(cleric)]
    row = entry(cleric.name, cleric)
    assert row["damage"][view("reliable", 3)]["1"] > 3 * row["damage"][view("reliable", 1)]["1"]
    assert row["area"][view("reliable", 3)]["1"] == "Spirit Guardians"
    from bg3.reddit_builds import REDDIT
    hunter = REDDIT["Filthy Harold Hunter (Hunter 11 / War Cleric 1)"]
    assert [label for label, _ in area_options(hunter)] == ["Horde Breaker"] # One Cleric level can't learn Spirit Guardians

def test_fingerprint_ignores_the_name_and_sees_changes():
    build = deepcopy(PRESETS["Karlach (Berserker)"])
    renamed = deepcopy(build)
    renamed.name = "Someone else"
    assert fingerprint(renamed) == fingerprint(build)
    changed = deepcopy(build)
    changed.equipment["1"]["ring_1"] = "bg3:crusher_s_ring"
    assert fingerprint(changed) != fingerprint(build)
    saved = entry("Karlach", build)
    assert compare(entry("Karlach", build), saved)[0] == "same"
    assert compare(entry("Karlach", changed), saved)[0] == "build changed"
    assert compare(saved, None)[0] == "new"

def test_gear_variants():
    from bg3.optimize import proficiencies
    build = PRESETS["Karlach (Berserker)"]
    rows, specs = entries_for(build.name, build)
    by_kind = {r["variant"]: r for r in rows}
    assert set(by_kind) == {"planned", "max_damage", "max_ac", "best_score"} and len(specs) >= 2
    for act in "123":
        assert by_kind["max_damage"]["damage"][view("reliable")][act] >= by_kind["planned"]["damage"][view("reliable")][act] - 0.01
        assert by_kind["max_ac"]["ac"][act] >= by_kind["planned"]["ac"][act]
        assert by_kind["best_score"]["score"][act] >= by_kind["planned"]["score"][act] - 0.05
    assert all(r["base"] == fingerprint(build) for r in rows)
    assert "heavy" not in proficiencies(build, "3") and "medium" in proficiencies(build, "3")
    assert proficiencies(PRESETS["Monk (Open Hand)"], "1") == set()

def test_ranking_helpers():
    builds = {n: PRESETS[n] for n in ["Karlach (Berserker)", "Gale (Evoker)", "Lae'zel (Champion, GWM)"]}
    entries = [entry(n, b) for n, b in builds.items()]
    totals = overall(entries, view("reliable"))
    assert max(totals.values()) <= 1 and min(totals.values()) > 0
    assert ranked(entries, view("plain"), "1")[0]["name"] == "Karlach (Berserker)"
    assert len({key(e) for e in entries}) == 3
    assert {k.split("@")[0] for k in entries[0]["damage"]} == set(SCENARIOS)

def test_database(tmp_path):
    from bg3 import db
    build = PRESETS["Gale (Evoker)"]
    rows = [entry(build.name, build)]
    path = tmp_path / "test.sqlite"
    run = db.save_run(rows, {fingerprint(build): build}, "party", "test", path=path)
    assert db.runs(path=path)[0]["id"] == run and db.runs("examples", path=path) == []
    assert db.load_run(run, path=path)[0]["damage"] == rows[0]["damage"]
    assert db.build_by_fingerprint(fingerprint(build), path=path)["name"] == build.name

def test_doc_builds_are_repaired():
    from bg3.doc_import import load
    builds = {d["build"]["name"]: d for d in load()}
    sorlock = builds["18. The 11/1 Fire Sorlock"]["build"]["character"]
    assert sorlock["scores"]["charisma"] == 15 and sorlock["bonus"]["charisma"] == 2 # Not the generic Strength spread
    monk = builds["22. Tavern Brawler Open Hand Monk"]["build"]["character"]
    assert [c for c, _, _ in monk["classes"]] == ["monk", "rogue"] and monk["routine"] == "unarmed" and "Tavern Brawler" in monk["feats"]
    blade = builds["10. Pure 12 Bladesinging Wizard & 10 Bladesinger / 2 Stars Druid"]["build"]["character"]
    assert blade["classes"][0][:2] == ["wizard", "Bladesinging"]
    godblade = builds["1. The Godblade"]
    assert not any(n.startswith(("Ability scores guessed", "Feats guessed")) for n in godblade["notes"]) # Complete builds are left alone

def test_party_rows_replace_identical_examples():
    from api.leaderboard import entries
    from bg3.presets import DEFAULT_PARTY, PRESETS
    rows = entries([PRESETS[name].to_dict() for name in DEFAULT_PARTY])
    mine = [r for r in rows if r["source"] == "Your party"]
    assert len(mine) == 4 and all(r["same_as"].endswith("(Preset)") for r in mine)
    assert not any(r["source"] == "Preset" and r["fingerprint"] in {m["fingerprint"] for m in mine} for r in rows)
