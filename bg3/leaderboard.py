""" A damage leaderboard of every example build (presets, imported doc builds, Reddit approximations) at each act checkpoint, under the
    same conditions for everyone, and a saved snapshot to see what changed.

    python -m bg3.leaderboard    -> bg3/data/leaderboard.json (the snapshot, with each build's full spec) and docs/leaderboard.md

    Fair by construction:
      - one reference enemy per act (AC and saves typical for the act, no resistances), single target, 3 round fights
      - scenarios apply the same outside help to everyone: none, advantage, Bless, Bless and advantage. A build's own buffs are removed
        except spells it casts on itself (SELF_BUFFS); "As planned" keeps the build exactly as written
      - each build's own gear per act, as planned (items change a lot between acts, that is part of the ranking)
    A build's fingerprint is a hash of its spec (classes, feats, gear, buffs, toggles; not its name), so a changed build shows up as
    changed, and the same fingerprint with different numbers means the damage model changed """
import hashlib
import json
from copy import deepcopy
from datetime import date
from pathlib import Path

from bg3.build import ACT_KEYS, compile_build, equipment_at
from bg3.character import Bg3Character
from bg3.checkpoints import act_level
from bg3.items import DATA, catalog
from computations.analytic import expected_damage_vs_enemies
from computations.models import Enemy

SNAPSHOT = DATA / "leaderboard.json"
DOC = Path(__file__).parent.parent / "docs" / "leaderboard.md"
ROUNDS_PER_FIGHT = 3
# Typical enemies by act checkpoint: AC and saving throws of the DMG's CR 3, 6 and 10 to 12 monsters
REFERENCE_ENEMIES = {
    "1": dict(name="Act 1 reference (AC 14)", armor_class=14, hit_points=60, strength_save=2, dexterity_save=2, constitution_save=3,
              intelligence_save=0, wisdom_save=1, charisma_save=0),
    "2": dict(name="Act 2 reference (AC 16)", armor_class=16, hit_points=110, strength_save=3, dexterity_save=3, constitution_save=5,
              intelligence_save=1, wisdom_save=3, charisma_save=1),
    "3": dict(name="Act 3 reference (AC 18)", armor_class=18, hit_points=200, strength_save=5, dexterity_save=4, constitution_save=7,
              intelligence_save=3, wisdom_save=5, charisma_save=3),
}
SCENARIOS = {
    "plain": ("No buffs", [], False),
    "advantage": ("Advantage", [], True),
    "bless": ("Bless", ["bless"], False),
    "bless_advantage": ("Bless + advantage", ["bless"], True),
    "planned": ("As planned", None, None),
}
SELF_BUFFS = {"hex", "divine_favour"} # Cast by the character on itself, kept in every scenario

def reference_enemy(act):
    return Enemy(**REFERENCE_ENEMIES[str(act)])

def spec(build):
    """ What makes the build itself: everything but its name and its variants """
    data = build.to_dict()
    for key in ("name", "variants"):
        data.pop(key, None)
    if data.get("character"):
        data["character"] = {k: v for k, v in data["character"].items() if k != "name"}
    return data

def fingerprint(build):
    return hashlib.sha1(json.dumps(spec(build), sort_keys=True).encode()).hexdigest()[:8]

def scenario_build(build, scenario):
    """ The build under a scenario's outside help """
    _, extra, advantage = SCENARIOS[scenario]
    if extra is None:
        return build
    out = deepcopy(build)
    out.buffs = {act: [b for b in out.buffs.get(act, []) if b in SELF_BUFFS] + extra for act in ACT_KEYS}
    if out.character:
        out.character = {**out.character, "toggles": {**out.character.get("toggles", {}), "advantage": advantage}}
    out.advantage = advantage
    return out

def damage(build, scenario, act):
    return expected_damage_vs_enemies(compile_build(scenario_build(build, scenario), act), reference_enemy(act), ROUNDS_PER_FIGHT, 1)

def describe(build):
    """ A one line spec: classes, feats, routine and the gear at each act """
    items = catalog()
    parts = []
    if build.character:
        character = Bg3Character.from_dict(build.character)
        parts.append(" / ".join(f"{cls.title()} {n}" + (f" ({sub})" if sub else "") for cls, sub, n in character.classes))
        parts.append(f"{character.race}; routine {character.routine}" + (f", {character.cantrip}" if character.routine == "cantrip" else "") +
                     (f", spell {character.spell}" if character.spell else ""))
        feats = [f for f in character.feats if "+" not in f]
        if feats or character.fighting_styles:
            parts.append("feats " + ", ".join([*feats, *character.fighting_styles]))
    else:
        parts.append(f"class preset {build.preset}")
    for act in ACT_KEYS:
        gear = [items[k].name for k in equipment_at(build, act).values() if k in items]
        if gear:
            parts.append(f"Act {act}: {', '.join(gear)}")
    return ". ".join(parts)

def source_of(name):
    from bg3.presets import PRESETS # pylint: disable=import-outside-toplevel
    from bg3.reddit_builds import REDDIT # pylint: disable=import-outside-toplevel
    if name in PRESETS:
        return "Preset"
    if name in REDDIT:
        return "Reddit (approx.)"
    return "Build doc"

def all_builds():
    """ Every example build by name: presets, the build doc import and the Reddit approximations """
    from bg3.presets import examples # pylint: disable=import-outside-toplevel
    from bg3.reddit_builds import REDDIT # pylint: disable=import-outside-toplevel
    return {**examples(), **REDDIT}

def entry(name, build, source=None, scenarios=SCENARIOS):
    values = {}
    for scenario in scenarios:
        values[scenario] = {}
        for act in ACT_KEYS:
            try:
                values[scenario][act] = round(damage(build, scenario, act), 2)
            except Exception: # pylint: disable=broad-exception-caught
                values[scenario][act] = None # A build that doesn't compile is listed without numbers
    return {"name": name, "source": source or source_of(name), "fingerprint": fingerprint(build), "spec": describe(build), "damage": values,
            "levels": {act: act_level(act, build.levels) for act in ACT_KEYS}}

def leaderboard(builds=None, extra=()):
    """ Entries for the builds (default: all_builds()), plus extra (name, build, source) like the planner party """
    builds = all_builds() if builds is None else builds
    return [entry(name, b) for name, b in builds.items()] + [entry(name, b, source) for name, b, source in extra]

def ranked(entries, scenario, act):
    """ Entries with a number for the scenario and act, best first """
    rows = [e for e in entries if e["damage"].get(scenario, {}).get(act) is not None]
    return sorted(rows, key=lambda e: -e["damage"][scenario][act])

def key(entry_):
    """ Entries are told apart by name and source: a party member can share an example's name """
    return f"{entry_['name']}|{entry_['source']}"

def overall(entries, scenario):
    """ {key(entry): average share of the act's best damage over the three acts}, so every act counts the same """
    best = {act: max([e["damage"][scenario][act] or 0 for e in entries] + [1e-9]) for act in ACT_KEYS}
    return {key(e): sum((e["damage"][scenario][act] or 0) / best[act] for act in ACT_KEYS) / len(ACT_KEYS) for e in entries}

def load_snapshot():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {"entries": []}

_CACHE = {}

def cached_entry(name, build, source=None):
    """ entry(), remembered by name and fingerprint: the example builds don't change while the app runs """
    key = (name, fingerprint(build), source)
    if key not in _CACHE:
        _CACHE[key] = entry(name, build, source)
    return _CACHE[key]

def compare(entry_, saved, scenario="plain"):
    """ How an entry differs from its saved version: (status, change in damage per act for the scenario) """
    if saved is None:
        return "new", {}
    delta = {act: round((entry_["damage"][scenario][act] or 0) - (saved["damage"].get(scenario, {}).get(act) or 0), 2) for act in ACT_KEYS}
    if entry_["fingerprint"] != saved["fingerprint"]:
        return "build changed", delta
    if any(abs(d) > 0.05 for d in delta.values()):
        return "model changed", delta
    return "same", delta

def write_snapshot(entries):
    builds = all_builds()
    data = {"_about": "Damage leaderboard snapshot (python -m bg3.leaderboard). Each entry keeps the full build, so a ranking can be "
                      "reproduced or compared later", "date": date.today().isoformat(), "rounds_per_fight": ROUNDS_PER_FIGHT,
            "enemies": REFERENCE_ENEMIES, "scenarios": {k: v[0] for k, v in SCENARIOS.items()},
            "entries": [{**e, "build": builds[e["name"]].to_dict()} for e in entries]}
    SNAPSHOT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")

def write_doc(entries):
    lines = ["# Damage leaderboard", "",
             f"Expected damage per round of every example build ({len(entries)}) at each act checkpoint, against one reference enemy per act "
             f"({', '.join(v['name'] for v in REFERENCE_ENEMIES.values())}; no resistances), single target, {ROUNDS_PER_FIGHT} round fights. "
             "Every build gets the same outside help in each scenario; its own buffs are removed except Hex and Divine Favour. "
             "Each build uses its own planned gear for the act. Generated by `python -m bg3.leaderboard`; the full specs are in "
             "`bg3/data/leaderboard.json` and the planner has the same leaderboard with your party in it.", "",
             "Reddit (approx.) builds are rebuilt from the Reddit index (classes and key items only), so treat them as rough. "
             "Area damage (Fireball, Spirit Guardians) counts one enemy here, so casters rank low; see the planner's enemies setting.", ""]
    for scenario in ("plain", "bless_advantage"):
        totals = overall(entries, scenario)
        lines += [f"## {SCENARIOS[scenario][0]}", "", "| # | Build | Source | Act 1 | Act 2 | Act 3 | Overall |", "|---|---|---|---|---|---|---|"]
        for rank, e in enumerate(sorted(entries, key=lambda e: -totals[key(e)]), start=1):
            acts = []
            for act in ACT_KEYS:
                value = e["damage"][scenario][act]
                place = next((ii for ii, r in enumerate(ranked(entries, scenario, act), start=1) if key(r) == key(e)), None)
                acts.append(f"{value:.1f} (#{place})" if value is not None else "?")
            lines.append(f"| {rank} | {e['name']} | {e['source']} | {' | '.join(acts)} | {100 * totals[key(e)]:.0f} |")
        lines.append("")
    lines += ["Overall: the average over the three acts of the build's damage as a share of the best build at that act (100 = best in "
              "every act).", "", "## Build specs", "", "| Build | Fingerprint | Spec |", "|---|---|---|"]
    lines += [f"| {e['name']} | `{e['fingerprint']}` | {e['spec'].replace('|', '/')} |" for e in sorted(entries, key=lambda e: e["name"])]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    ENTRIES = leaderboard()
    write_snapshot(ENTRIES)
    write_doc(ENTRIES)
    TOTALS = overall(ENTRIES, "plain")
    TOP = sorted(ENTRIES, key=lambda e: -TOTALS[key(e)])[:10]
    for E in TOP:
        print(f"{E['name']:55s} {E['damage']['plain']}")
