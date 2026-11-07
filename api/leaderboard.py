""" The damage leaderboard as JSON: every example build and gear variant (from the latest database run), the planner party computed live,
    saved runs to compare against, and saving the party """
from bg3 import db
from bg3.build import Bg3Build
from bg3.leaderboard import (ENEMY_COUNTS, REFERENCE_ENEMIES, ROUNDS_PER_FIGHT, SCENARIO_NOTES, SCENARIOS, cached_entry, entries_for,
                             example_entries, fingerprint, key)
from bg3.optimize import VARIANTS
from bg3.score import WEIGHTS

SOURCES = ["Your party", "Preset", "Build doc", "Reddit (approx.)"]

def options():
    return {
        "scenarios": [{"key": k, "label": label, "note": SCENARIO_NOTES[k]} for k, label in SCENARIOS.items()],
        "enemyCounts": list(ENEMY_COUNTS),
        "variants": [{"key": k, "label": label} for k, label in VARIANTS.items()],
        "sources": SOURCES,
        "referenceEnemies": {act: e["name"] for act, e in REFERENCE_ENEMIES.items()},
        "roundsPerFight": ROUNDS_PER_FIGHT,
        "scoreWeights": WEIGHTS,
    }

def _party_entries(party):
    """ The party's members as rows, plus gear variants saved for them in earlier party runs (matched by their spec) """
    saved = {}
    for run in db.runs("party"):
        for e in db.load_run(run["id"]):
            if e.get("variant", "planned") != "planned" and e.get("base"):
                saved.setdefault((e["base"], e["variant"]), e)
    rows = []
    for build in party:
        own = {**cached_entry(build.name, build, "Your party"), "base": fingerprint(build)}
        rows.append(own)
        rows += [{**e, "name": build.name} for (base, _), e in saved.items() if base == own["fingerprint"]]
    return rows

def entries(party_dicts):
    """ Every row: examples (a member identical to an example replaces it, noted in same_as) and the party """
    examples = example_entries()
    mine = _party_entries([Bg3Build.from_dict(b) for b in party_dicts or []])
    prints = {e["fingerprint"] for e in mine}
    for e in mine:
        twin = next((x for x in examples if x["fingerprint"] == e["fingerprint"]), None)
        if twin:
            e["same_as"] = f"{twin['name']} ({twin['source']})"
    rows = [e for e in examples if e["fingerprint"] not in prints] + mine
    return [{**e, "key": key(e)} for e in rows]

def runs():
    return db.runs()

def run_entries(run_id):
    return [{**e, "key": key(e)} for e in db.load_run(run_id)]

def save(party_dicts, label="", with_variants=False):
    """ Saves the party (and, with_variants, gear variants found by search) as a run; returns its id and row count """
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    rows, specs = [], {}
    for b in builds:
        if with_variants:
            found, prints = entries_for(b.name, b, "Your party")
        else:
            found, prints = [{**cached_entry(b.name, b, "Your party"), "base": fingerprint(b)}], {fingerprint(b): b}
        rows += found
        specs.update(prints)
    run_id = db.save_run(rows, specs, "party", label or ("party with gear variants" if with_variants else "party"))
    return {"id": run_id, "rows": len(rows)}

def build(fingerprint_):
    return db.build_by_fingerprint(fingerprint_)
