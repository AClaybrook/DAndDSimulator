""" A damage leaderboard of every example build (presets, imported doc builds, Reddit approximations) and gear variants of each, at each act
    checkpoint, under the same conditions for everyone. Runs are saved in the local database (bg3.db).

    python -m bg3.leaderboard    -> a run in local_data/bg3.sqlite and docs/leaderboard.md
                                    (about a minute on 4 cores: the gear variants try every item)

    Fair by construction:
      - one reference enemy per act (AC and saves typical for the act, no resistances), 3 round fights, 1 to 4 enemies in reach
      - scenarios give everyone the same outside help: none, advantage, Bless, Bless and advantage. A build's own buffs are removed except
        spells it casts on itself (SELF_BUFFS). "Reliable" is what a party can count on every fight: Bless, the build's own planned buffs, and
        advantage only for builds with a dependable source (hiding, Shadow Blade in dim light, Reckless Attack, Trip Attack...).
        "Max nova" is the best case first round: Bless, Haste, Phalar Aluve's Sing, advantage, the target held (melee hits crit) and every
        limited resource spent in that round. "As planned" keeps the build exactly as written
      - gear: as planned, or the variants bg3.optimize finds (max damage, max AC, best overall score)
    A build's fingerprint is a hash of its spec (classes, feats, gear, buffs, toggles; not its name), so a changed build shows up as
    changed, and the same fingerprint with different numbers means the damage model changed """
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

from bg3.build import ACT_KEYS, compile_build, equipment_at
from bg3.character import Bg3Character, class_levels, subclass_of
from bg3.checkpoints import act_level
from bg3.defence import armour_class
from bg3.items import catalog
from bg3.optimize import VARIANTS, ac_objective, variant
from bg3.score import score
from computations.analytic import expected_damage_vs_enemies
from computations.models import Enemy

DOC = Path(__file__).parent.parent / "docs" / "leaderboard.md"
ROUNDS_PER_FIGHT = 3
ENEMY_COUNTS = (1, 2, 3, 4)
# Typical enemies by act checkpoint: AC, saving throws and attack bonus of the DMG's CR 3, 6 and 10 to 12 monsters
REFERENCE_ENEMIES = {
    "1": dict(name="Act 1 reference (AC 14)", armor_class=14, hit_points=60, strength_save=2, dexterity_save=2, constitution_save=3,
              intelligence_save=0, wisdom_save=1, charisma_save=0),
    "2": dict(name="Act 2 reference (AC 16)", armor_class=16, hit_points=110, strength_save=3, dexterity_save=3, constitution_save=5,
              intelligence_save=1, wisdom_save=3, charisma_save=1),
    "3": dict(name="Act 3 reference (AC 18)", armor_class=18, hit_points=200, strength_save=5, dexterity_save=4, constitution_save=7,
              intelligence_save=3, wisdom_save=5, charisma_save=3),
}
REFERENCE_ATTACK = {"1": 5, "2": 6, "3": 7}
SCENARIOS = {
    "plain": "No buffs",
    "advantage": "Advantage",
    "bless": "Bless",
    "bless_advantage": "Bless + advantage",
    "reliable": "Reliable buffs",
    "nova": "Max nova (round 1)",
    "planned": "As planned",
}
SCENARIO_NOTES = {
    "plain": "No outside help. Self cast Hex and Divine Favour stay, Reckless Attack still gives Barbarians advantage",
    "advantage": "Everyone attacks with advantage",
    "bless": "Everyone is Blessed",
    "bless_advantage": "Everyone is Blessed and attacks with advantage",
    "reliable": "Bless, the build's own planned buffs, and advantage only with a dependable source of it (hover the Act cells)",
    "nova": "Round 1, everything: Bless, Haste, Phalar Aluve's Sing, advantage, the target held (melee hits crit), every limited resource spent",
    "planned": "The build exactly as written: its buffs and toggles",
}
SELF_BUFFS = {"hex", "divine_favour"} # Cast by the character on itself, kept in every scenario
NOVA_BUFFS = ["bless", "haste", "phalar_sing"]
MELEE = ("weapon (melee)", "unarmed")

def reference_enemy(act):
    return Enemy(**REFERENCE_ENEMIES[str(act)])

def view(scenario, enemies=1):
    """ The key of a damage column: a scenario against a number of enemies """
    return f"{scenario}@{enemies}"

def spec(build):
    """ What makes the build itself: everything but its name and its variants """
    data = build.to_dict()
    for k in ("name", "variants"):
        data.pop(k, None)
    if data.get("character"):
        data["character"] = {k: v for k, v in data["character"].items() if k != "name"}
    return data

def fingerprint(build):
    return hashlib.sha1(json.dumps(spec(build), sort_keys=True).encode()).hexdigest()[:8]

def reliable_advantage(build, act):
    """ Why a build can count on advantage every fight at an act, or '' """
    from bg3.synergy import casts_darkness, sees_in_darkness # pylint: disable=import-outside-toplevel
    if build.advantage or (build.character or {}).get("toggles", {}).get("advantage"):
        return "planned (advantage toggle)"
    level = act_level(act, build.levels)
    if build.character:
        character = Bg3Character.from_dict(build.character)
        levels = class_levels(character, level)
        subs = {cls: subclass_of(character, cls, n) for cls, n in levels.items()}
        routine = character.routine
    else:
        levels, subs, routine = {build.preset.split("_")[0]: level}, {}, ""
        if build.preset == "ranger_gloom_stalker":
            subs = {"ranger": "Gloom Stalker"}
        if build.preset == "monk_open_hand":
            subs = {"monk": "Way of the Open Hand"}
    if routine == "shadow_blade":
        return "Shadow Blade in dim light or darkness"
    if levels.get("barbarian", 0) >= 2:
        return "Reckless Attack"
    if levels.get("rogue", 0) >= 2:
        return "hiding (Cunning Action), surprise rounds"
    if subs.get("fighter") == "Battle Master":
        return "Trip Attack"
    if subs.get("monk") == "Way of the Open Hand" and levels.get("monk", 0) >= 3:
        return "Topple (Flurry of Blows)"
    if casts_darkness(build, act) and sees_in_darkness(build, act):
        return "Darkness with Devil's Sight"
    if subs.get("ranger") == "Gloom Stalker":
        return "Umbral Sight in darkness"
    return ""

def scenario_build(build, scenario, act="1"):
    """ (build under the scenario, rounds the limited resources are spread over, whether the target is held) """
    if scenario == "planned":
        return build, ROUNDS_PER_FIGHT, False
    out = deepcopy(build)
    own = {a: list(out.buffs.get(a, [])) for a in ACT_KEYS}
    if scenario == "reliable":
        buffs, advantage = (lambda a: list(dict.fromkeys(own[a] + ["bless"]))), bool(reliable_advantage(build, act))
    elif scenario == "nova":
        buffs, advantage = (lambda a: list(dict.fromkeys(own[a] + NOVA_BUFFS))), True
    else:
        extra = ["bless"] if scenario.startswith("bless") else []
        buffs, advantage = (lambda a: [b for b in own[a] if b in SELF_BUFFS] + extra), "advantage" in scenario
    out.buffs = {a: buffs(a) for a in ACT_KEYS}
    if out.character:
        out.character = {**out.character, "toggles": {**out.character.get("toggles", {}), "advantage": advantage}}
    out.advantage = advantage
    return out, (1 if scenario == "nova" else ROUNDS_PER_FIGHT), scenario == "nova"

def damage_by_count(build, scenario, act, counts=ENEMY_COUNTS):
    """ {enemies: expected damage per round} for a scenario at an act """
    changed, rounds, held = scenario_build(build, scenario, act)
    character, enemy = compile_build(changed, act), reference_enemy(act)
    if held:
        # Paralysed (Hold Person): attacks have advantage, melee hits within 3 m crit, Strength and Dexterity saves fail
        character = deepcopy(character)
        for attack in character.attacks:
            if not attack.saving_throw:
                attack.advantage = True
                attack.hits_crit = attack.hits_crit or attack.type in MELEE
        enemy.strength_save = enemy.dexterity_save = -100
    return {n: expected_damage_vs_enemies(character, enemy, rounds, n) for n in counts}

# Area spells each class can cast in the builder (BG3 spell lists, subclass expanded lists)
AREA_SPELLS = {"wizard": ["Burning Hands", "Thunderwave", "Shatter", "Fireball", "Lightning Bolt", "Cone of Cold", "Chain Lightning"],
               "sorcerer": ["Burning Hands", "Thunderwave", "Shatter", "Fireball", "Lightning Bolt", "Cone of Cold", "Chain Lightning"],
               "bard": ["Thunderwave", "Shatter"], "druid": ["Thunderwave"], "warlock": ["Shatter"],
               ("warlock", "The Fiend"): ["Burning Hands", "Fireball"], ("cleric", "Light Domain"): ["Burning Hands", "Fireball"],
               ("cleric", "Tempest Domain"): ["Thunderwave", "Shatter"]}

def area_options(build):
    """ [(label, build)] ways a build can hit more enemies than its planned routine: an area spell for casters, Spirit Guardians for
        clerics (an aura on top of any routine), Horde Breaker for Hunters. Martial cleaves (Cleave, Whirlwind) aren't modelled yet """
    from game_data import spells # pylint: disable=import-outside-toplevel
    character = build.character
    if not character:
        return []
    classes = [(cls, sub) for cls, sub, _ in character["classes"]]
    levels = {cls: int(n) for cls, _, n in character["classes"]}
    def learns(cls, spell):
        # A class learns spells of a level its own levels reach (level 3 spells at class level 5), multiclass slots don't teach spells
        return levels.get(cls, 0) >= 2 * spells()[spell]["level"] - 1
    options = []
    def changed(**fields):
        out = deepcopy(build)
        out.character = {**out.character, **fields}
        return out
    if learns("cleric", "Spirit Guardians") and character.get("spell") != "Spirit Guardians":
        options.append(("Spirit Guardians", changed(spell="Spirit Guardians")))
    if character["routine"] == "cantrip":
        found = []
        for cls, sub in classes:
            found += [sp for sp in AREA_SPELLS.get(cls, []) + AREA_SPELLS.get((cls, sub), []) if learns(cls, sp)]
        options += [(spell, changed(spell=spell)) for spell in dict.fromkeys(found) if spell != character.get("spell")]
    if any(sub == "Hunter" for _, sub in classes) and not character.get("toggles", {}).get("horde_breaker"):
        options.append(("Horde Breaker", changed(toggles={**character.get("toggles", {}), "horde_breaker": True})))
    return options

def best_by_count(build, scenario, act):
    """ ({enemies: damage}, {enemies: what it used}): against 2+ enemies the best of the build as planned and its area options """
    best = damage_by_count(build, scenario, act)
    choice = {}
    for label, option in area_options(build):
        try:
            values = damage_by_count(option, scenario, act, ENEMY_COUNTS[1:])
        except Exception: # pylint: disable=broad-exception-caught
            continue
        for n, value in values.items():
            if value > best[n] + 0.05:
                best[n], choice[n] = value, label
    return best, choice

def damage(build, scenario, act, enemies=1):
    return damage_by_count(build, scenario, act, (enemies,))[enemies]

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

def gear_changes(build, planned):
    """ 'Act 1: Item, Item; Act 3: ...' for the items a variant wears that the planned build doesn't """
    items, parts = catalog(), []
    for act in ACT_KEYS:
        mine, theirs = equipment_at(build, act), equipment_at(planned, act)
        changed = [items[k].name for s, k in mine.items() if k in items and theirs.get(s) != k]
        if changed:
            parts.append(f"Act {act}: {', '.join(changed)}")
    return "; ".join(parts)

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

def entry(name, build, source=None, variant_kind="planned", planned=None):
    """ One leaderboard row: damage for every scenario, enemy count and act, AC, overall score and why advantage is reliable """
    values, area = {}, {}
    for scenario in SCENARIOS:
        for act in ACT_KEYS:
            try:
                by_count, choice = best_by_count(build, scenario, act)
            except Exception: # pylint: disable=broad-exception-caught
                by_count, choice = dict.fromkeys(ENEMY_COUNTS), {} # A build that doesn't compile is listed without numbers
            for n, value in by_count.items():
                values.setdefault(view(scenario, n), {})[act] = round(value, 2) if value is not None else None
                if n in choice:
                    area.setdefault(view(scenario, n), {})[act] = choice[n]
    ac, overall_score = {}, {}
    for act in ACT_KEYS:
        try:
            ac[act] = armour_class(build, act)[0]
            overall_score[act] = score(build, act, reference_enemy(act), ROUNDS_PER_FIGHT, REFERENCE_ATTACK[act]).total
        except Exception: # pylint: disable=broad-exception-caught
            ac[act], overall_score[act] = None, None
    return {"name": name, "source": source or source_of(name), "variant": variant_kind, "fingerprint": fingerprint(build),
            "spec": describe(build), "area": area, "gear_changes": gear_changes(build, planned) if planned is not None else "", "damage": values,
            "ac": ac, "score": overall_score, "advantage_source": {act: reliable_advantage(build, act) for act in ACT_KEYS},
            "levels": {act: act_level(act, build.levels) for act in ACT_KEYS}}

def objective(kind, act):
    """ What a gear variant maximises at an act """
    enemy = reference_enemy(act)
    def reliable(b):
        return damage(b, "reliable", act)
    if kind == "max_damage":
        return reliable
    if kind == "max_ac":
        return ac_objective(act, reliable)
    return lambda b: score(b, act, enemy, ROUNDS_PER_FIGHT, REFERENCE_ATTACK[act]).total

def variants_of(build):
    """ {variant kind: build} for the planned gear and each gear variant """
    return {kind: variant(build, kind, lambda act, kind=kind: objective(kind, act)) for kind in VARIANTS}

def entries_for(name, build, source=None, with_variants=True):
    """ The planned row and, with_variants, a row per gear variant; also returns {fingerprint: build} for the database """
    builds = variants_of(build) if with_variants else {"planned": build}
    rows = [{**entry(name, b, source, kind, None if kind == "planned" else build), "base": fingerprint(build)} for kind, b in builds.items()]
    return rows, {fingerprint(b): b for b in builds.values()}

def _entries_for_name(name):
    return entries_for(name, all_builds()[name])

def leaderboard(builds=None, with_variants=False, processes=1):
    """ Entries for the builds (default: all_builds()); returns (entries, {fingerprint: build}) """
    every = builds is None
    builds = all_builds() if every else builds
    if processes > 1 and with_variants and every: # Workers look the builds up by name
        from multiprocessing import Pool # pylint: disable=import-outside-toplevel
        with Pool(processes) as pool:
            results = pool.map(_entries_for_name, list(builds))
    else:
        results = [entries_for(name, b, with_variants=with_variants) for name, b in builds.items()]
    entries, specs = [], {}
    for rows, fps in results:
        entries += rows
        specs.update(fps)
    return entries, specs

def ranked(entries, view_key, act):
    """ Entries with a number for the view and act, best first """
    rows = [e for e in entries if e["damage"].get(view_key, {}).get(act) is not None]
    return sorted(rows, key=lambda e: -e["damage"][view_key][act])

def key(entry_):
    """ Entries are told apart by name, source and gear variant: a party member can share an example's name """
    return f"{entry_['name']}|{entry_['source']}|{entry_.get('variant', 'planned')}"

def overall(entries, view_key):
    """ {key(entry): average share of the act's best damage over the three acts}, so every act counts the same """
    best = {act: max([e["damage"].get(view_key, {}).get(act) or 0 for e in entries] + [1e-9]) for act in ACT_KEYS}
    return {key(e): sum((e["damage"].get(view_key, {}).get(act) or 0) / best[act] for act in ACT_KEYS) / len(ACT_KEYS) for e in entries}

_CACHE = {}

def cached_entry(name, build, source=None):
    """ entry(), remembered by name and fingerprint: the example builds don't change while the app runs """
    k = (name, fingerprint(build), source)
    if k not in _CACHE:
        _CACHE[k] = entry(name, build, source)
    return _CACHE[k]

def compare(entry_, saved, view_key=None):
    """ How an entry differs from its saved version: (status, change in damage per act for the view) """
    if saved is None:
        return "new", {}
    view_key = view_key or view("plain")
    delta = {act: round((entry_["damage"].get(view_key, {}).get(act) or 0) - (saved["damage"].get(view_key, {}).get(act) or 0), 2)
             for act in ACT_KEYS}
    if entry_["fingerprint"] != saved["fingerprint"]:
        return "build changed", delta
    if any(abs(d) > 0.05 for d in delta.values()):
        return "model changed", delta
    return "same", delta

def example_entries():
    """ The example builds' rows, with gear variants: the latest database run, else computed (planned gear only) """
    from bg3 import db # pylint: disable=import-outside-toplevel
    _, entries = db.latest("examples")
    return entries or [cached_entry(name, b) for name, b in all_builds().items()]

def _rank_table(entries, view_key, title, note):
    totals = overall(entries, view_key)
    places = {act: {key(r): ii for ii, r in enumerate(ranked(entries, view_key, act), start=1)} for act in ACT_KEYS}
    lines = [f"## {title}", "", note, "", "| # | Build | Source | Act 1 | Act 2 | Act 3 | Overall |", "|---|---|---|---|---|---|---|"]
    for rank, e in enumerate(sorted(entries, key=lambda e: -totals[key(e)]), start=1):
        acts = [f"{e['damage'][view_key][a]:.1f} (#{places[a][key(e)]})" if e["damage"][view_key][a] is not None else "?" for a in ACT_KEYS]
        lines.append(f"| {rank} | {e['name']} | {e['source']} | {' | '.join(acts)} | {100 * totals[key(e)]:.0f} |")
    return lines + [""]

def write_doc(entries):
    planned = [e for e in entries if e["variant"] == "planned"]
    lines = ["# Damage leaderboard", "",
             f"Expected damage per round of every example build ({len(planned)}) at each act checkpoint, against one reference enemy per act "
             f"({', '.join(v['name'] for v in REFERENCE_ENEMIES.values())}; no resistances), {ROUNDS_PER_FIGHT} round fights. "
             "Generated by `python -m bg3.leaderboard`; every run is kept with each build's full spec in `local_data/bg3.sqlite`, and the planner "
             "has the same leaderboard with your party in it, other scenarios and 1 to 4 enemies.", "",
             "Reddit (approx.) builds are rebuilt from the Reddit index (classes and key items only), and build doc builds without ability scores "
             "use a guessed point buy, so treat both as rough. Overall: the average over the three acts of the build's damage as a share of the "
             "best build at that act (100 = best in every act).", ""]
    for scenario, n in (("plain", 1), ("reliable", 1), ("nova", 1), ("reliable", 3)):
        title = f"{SCENARIOS[scenario]}" + (f", {n} enemies in reach" if n > 1 else "")
        lines += _rank_table(planned, view(scenario, n), title, SCENARIO_NOTES[scenario] + ("." if n == 1 else
                             ". Area spells and auras hit up to their size, weapon attacks one enemy."))
    lines += ["## Gear variants", "", "Each build with gear found by search for every act (weapons stay as planned): max damage (Reliable buffs, "
              "1 enemy), max armour class, and the best overall score (docs/scoring.md). Damage is Reliable buffs against 1 enemy.", "",
              "| Build | Gear | Damage 1 / 2 / 3 | AC 1 / 2 / 3 | Score 1 / 2 / 3 | Items that change |", "|---|---|---|---|---|---|"]
    for e in sorted(entries, key=lambda e: (e["name"], list(VARIANTS).index(e["variant"]))):
        dmg = " / ".join(f"{e['damage'][view('reliable')][a]:.1f}" if e["damage"][view("reliable")][a] is not None else "?" for a in ACT_KEYS)
        ac = " / ".join(str(e["ac"][a]) for a in ACT_KEYS)
        sc = " / ".join(f"{e['score'][a]:.0f}" if e["score"][a] is not None else "?" for a in ACT_KEYS)
        lines.append(f"| {e['name']} | {VARIANTS[e['variant']]} | {dmg} | {ac} | {sc} | {e['gear_changes'] or '-'} |")
    lines += ["", "## Build specs", "", "| Build | Fingerprint | Spec |", "|---|---|---|"]
    lines += [f"| {e['name']} | `{e['fingerprint']}` | {e['spec'].replace('|', '/')} |" for e in sorted(planned, key=lambda e: e["name"])]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main(processes=4):
    from bg3 import db # pylint: disable=import-outside-toplevel
    entries, specs = leaderboard(with_variants=True, processes=processes)
    run_id = db.save_run(entries, specs, "examples", "python -m bg3.leaderboard",
                         {"rounds_per_fight": ROUNDS_PER_FIGHT, "enemies": REFERENCE_ENEMIES, "scenarios": SCENARIOS})
    write_doc(entries)
    return run_id, entries

if __name__ == "__main__":
    RUN, ENTRIES = main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
    print(f"Run {RUN}: {len(ENTRIES)} rows")
