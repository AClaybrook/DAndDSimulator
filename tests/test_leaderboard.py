""" Damage leaderboard: fair scenarios, fingerprints, change detection and the doc build repairs """
from copy import deepcopy

from bg3.leaderboard import SCENARIOS, compare, entry, fingerprint, key, leaderboard, overall, ranked, scenario_build
from bg3.presets import PRESETS

def test_scenarios_give_everyone_the_same_help():
    build = deepcopy(PRESETS["Lae'zel (Champion, GWM)"])
    build.buffs = {"1": ["haste", "hex"]}
    plain = scenario_build(build, "plain")
    assert plain.buffs["1"] == ["hex"] and not plain.advantage # Party buffs go, self cast ones stay
    blessed = scenario_build(build, "bless_advantage")
    assert blessed.buffs["2"] == ["bless"] and blessed.advantage
    assert scenario_build(build, "planned") is build
    values = entry("x", build)["damage"]
    for act in "123":
        assert values["advantage"][act] > values["plain"][act]
        assert values["bless_advantage"][act] >= values["advantage"][act]

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

def test_every_build_ranks():
    entries = leaderboard()
    assert len(entries) >= 60
    assert all(e["damage"]["plain"][act] is not None for e in entries for act in "123")
    totals = overall(entries, "advantage")
    assert max(totals.values()) <= 1 and min(totals.values()) > 0
    best = ranked(entries, "plain", "3")
    assert best[0]["damage"]["plain"]["3"] >= best[-1]["damage"]["plain"]["3"]
    assert len({key(e) for e in entries}) == len(entries)
    assert {e["source"] for e in entries} == {"Preset", "Build doc", "Reddit (approx.)"}
    assert set(SCENARIOS) == set(entries[0]["damage"])

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

def test_planner_table():
    from bg3.build import Bg3Build
    from components.bg3_planner import DEFAULT_PARTY, leaderboard_entries, leaderboard_table
    from components.static_html import to_html
    entries = leaderboard_entries([Bg3Build.from_dict(b) for b in DEFAULT_PARTY])
    html_ = to_html(leaderboard_table(entries, "advantage", "overall", ["Your party", "Preset"]))
    assert "not saved" in html_ and "Lae&#x27;zel" in html_
    assert "Reddit" not in html_
