""" The BG3 party planner as JSON: options for every picker, and evaluating a party (damage, AC and score per act, conflicts, warnings,
    variants), party roles, synergies and a party fight, gear advice, kits and example builds """
from bg3.abilities import point_buy_cost, point_buy_problems
from bg3.analysis import item_values, shared_item_gains, slot_suggestions
from bg3.buffs import BUFFS
from bg3.build import ACT_KEYS, ASSUMPTIONS, Bg3Build, compile_build, equipment_at, main_weapon_finesse
from bg3.character import (CANTRIPS, CLASSES, FEATS, FIGHTING_STYLES, LEVELLED_SPELLS, RACES, ROUTINES, SUBCLASSES, TOGGLE_DEFAULTS, TOGGLES, Bg3Character,
                           class_levels, class_order, compile_character, feat_opportunities, relevant_toggles)
from bg3.checkpoints import ACTS, act_level
from bg3.defence import armour_class, attack_bonus_for, hit_chance
from bg3.items import SLOT_LABELS, SLOTS, catalog, condition_id
from bg3.kits import QUICK_VARIANTS, apply_kit, kits, taken_by_others, variant_build, variant_builds
from bg3.party import MAX_PARTY_SIZE, party_conflicts
from bg3.parties import saved_parties
from bg3.presets import DEFAULT_PARTY, PRESETS, examples
from bg3.roles import CORE_ROLES, ROLE_LABELS, party_roles
from bg3.score import WEIGHTS, score
from dataclasses import asdict

from computations.analytic import expected_damage_vs_enemies, hit_and_crit_chance
from computations.models import STATS, Enemy, calculate_attack_and_damage_context
from game_data.classes import BUILDS

ENEMY_COUNTS = [1, 2, 3, 4]

# ---------- Item lists and labels

def effect_text(effect):
    target = "" if effect.applies_to in ("all", "self") else f" ({effect.applies_to.replace('_', ' ')})"
    what = {"ability_min": f"{effect.stat.title()} {effect.value}", "ability_bonus": f"{effect.stat.title()} +{effect.value}",
            "attack_bonus": "proficiency bonus added twice to hit" if effect.value == "proficiency" else f"+{effect.value} to hit", "attack_dice": f"+{effect.value} to hit", "damage_bonus": f"+{effect.value} damage",
            "damage_bonus_ability": f"+{effect.stat.title()} modifier to damage", "extra_damage": f"+{effect.value} damage",
            "crit_damage": f"+{effect.value} on a crit", "crit_range": f"crit range +{effect.value}", "advantage": "advantage",
            "advantage_chance": f"advantage on about {round(float(effect.value or 0) * 100)}% of attacks" if effect.kind == "advantage_chance" else "",
            "limited_haste": f"its own Haste: {effect.value} more actions a fight",
            "main_hand_bonus_attack": "in the off hand, the bonus action attack is made with the main hand weapon",
            "spell_dc": f"+{effect.value} spell DC", "damage_reroll": f"reroll damage dice of {effect.value} or less",
            "miss_damage_ability": f"{effect.stat.title()} modifier damage on a miss", "once_per_turn_bonus": f"+{effect.value} Sneak Attack damage", "extra_action": "another action each turn", "save_disadvantage": "enemies have disadvantage on the save",
            "free_cast": f"{effect.value} more cast a fight", "channel_divinity": f"+{effect.value} Channel Divinity charge", "extra_action_on_kill": "another action after a kill", "flag": str(effect.value),
            "lightning_charges": f"{effect.value} Lightning Charges on a hit: +1 to hit and 1 lightning damage on every attack"}.get(effect.kind, effect.kind)
    return what + target + (f" [toggle: {effect.condition}]" if effect.condition else "")

def item_summary(item):
    """ Hover text: modelled effects, other effects, where it's found """
    parts = []
    if item.weapon:
        w = item.weapon
        parts.append(f"{w['damage']} {w['damage_type']}" + (f" +{w['enhancement']}" if w.get("enhancement") else "") +
                     (f", {', '.join(w['properties'])}" if w.get("properties") else ""))
    parts += [effect_text(e) for e in item.effects]
    if item.notes:
        parts.append(f"Not counted in the damage: {item.notes}")
    if item.location:
        parts.append(f"Found: {item.location}")
    return "\n".join(parts)

def item_label(item):
    if not item.unique:
        return f"{item.name} (common)"
    details = " · ".join(x for x in [item.rarity, f"Act {item.act}" if item.act else "Act ?"] if x)
    # ✦ every effect is in the damage, ◐ some are, ○ none (the item's effects are only notes)
    counted = item.effects or (item.weapon and item.weapon.get("enhancement"))
    marker = (" ◐" if counted else " ○") if item.notes else (" ✦" if counted else "")
    return f"{item.name}{marker} · {details}"

def item_options(slot, act, include_unknown=True):
    """ Items that fit a slot and are found by an act, named items first """
    items = [i for i in catalog().values() if i.fits(slot) and ((i.act is None and include_unknown) or (i.act or 9) <= int(act))]
    items.sort(key=lambda i: (not i.unique, i.act or 9, i.name))
    return [{"label": item_label(i), "value": i.key, "title": item_summary(i)} for i in items]

# Slots that share an item list, the browser fills each dropdown from its group, filtered by act
# The off hand takes melee weapons and shields, so its list is both groups
OPTION_GROUPS = {"melee_main": "melee", "melee_off": "melee+shield", "ranged_main": "ranged", "ranged_off": "ranged", "ring_1": "ring", "ring_2": "ring"}

def option_group(slot):
    return OPTION_GROUPS.get(slot, slot)

def _missable():
    """ {item key: why it can be missed}, from the item maps (story choices, one-of rewards, time limits) """
    from api.map import DATA
    reasons = {}
    for p in [*DATA["points"], *DATA["unplaced"]]:
        if p.get("key") and p.get("missable"):
            reasons.setdefault(p["key"], p["missable"])
    return reasons

def grouped_item_options():
    """ {group: options} with every item's act, sent to the browser once instead of in every dropdown.
        Missable items get a ⚠ and the reason in their hover text """
    missable = _missable()
    def mark(o):
        reason = missable.get(o["value"])
        if not reason:
            return o
        return {**o, "label": f"{o['label']} ⚠", "title": f"{o['title']}\n⚠ Missable: {reason}"}
    groups = {}
    for slot, _, _ in SLOTS:
        group = option_group(slot)
        if "+" not in group and group not in groups:
            groups[group] = [mark({**o, "act": catalog()[o["value"]].act}) for o in item_options(slot, 3, include_unknown=True)]
    groups["shield"] = [mark({**o, "act": catalog()[o["value"]].act}) for o in item_options("melee_off", 3) if catalog()[o["value"]].slot == "shield"]
    return groups

def conditional_options(build):
    """ Toggles for the conditional effects of everything the build equips in any act """
    items, options, seen = catalog(), [], set()
    for act in ACT_KEYS:
        for key in equipment_at(build, act).values():
            item = items.get(key)
            if item is None or key in seen:
                continue
            seen.add(key)
            first = {}
            for ii, e in enumerate(item.effects):
                if e.condition:
                    first.setdefault(e.condition, ii) # Effects sharing a condition are one toggle
            options += [{"label": f"{item.name}: {condition}", "value": condition_id(key, ii)} for condition, ii in first.items()]
    return options

PART_LABELS = {"damage": "Damage", "aoe": "AoE", "defence": "Defence", "control": "Control", "support": "Support", "utility": "Utility"}

def options():
    short = {s: s[:3].title() for s in STATS}
    improvements = ([{"value": f"{s}+2", "label": f"+2 {short[s]}"} for s in STATS] + [{"value": f, "label": f} for f in FEATS if f != "Ability Improvement"]
                    + [{"value": f"{a}+1,{b}+1", "label": f"+1 {short[a]} / +1 {short[b]}"} for i, a in enumerate(STATS) for b in STATS[i + 1:]])
    return {
        "maxPartySize": MAX_PARTY_SIZE,
        "acts": [{"key": a, "label": ACTS[int(a)][0], "level": ACTS[int(a)][1]} for a in ACT_KEYS],
        "presets": [{"key": k, "label": b.label} for k, b in BUILDS.items()],
        "examples": [{"name": n, "source": "Preset" if n in PRESETS else "Build doc"} for n in examples()],
        "slots": [{"key": k, "label": label, "group": option_group(k)} for k, label, _ in SLOTS],
        "items": grouped_item_options(),
        "buffs": [{"key": k, "name": b.name, "act": b.act, "notes": b.notes, "modelled": bool(b.effects)} for k, b in BUFFS.items()],
        "kits": [{"key": k, "name": k_["name"], "act": k_["act"], "theme": k_.get("theme", ""), "trigger": k_.get("trigger", ""),
                  "fits": k_.get("fits", ""), "synergy": k_.get("synergy", ""), "notes": k_.get("notes", ""),
                  "slots": {slot: [catalog()[i].name for i in options_ if i in catalog()] for slot, options_ in k_["slots"].items()}}
                 for k, k_ in kits().items()],
        "quickVariants": [{"key": k, **v} for k, v in QUICK_VARIANTS.items()],
        "builder": {"races": RACES, "classes": CLASSES, "subclasses": SUBCLASSES, "improvements": improvements, "fightingStyles": list(FIGHTING_STYLES),
                    "routines": [{"value": k, "label": v} for k, v in ROUTINES.items()], "cantrips": CANTRIPS, "spells": LEVELLED_SPELLS,
                    "toggles": [{"value": k, "label": v, "on": TOGGLE_DEFAULTS.get(k, True)} for k, v in TOGGLES.items()],
                    "defaultCharacter": Bg3Character().to_dict()},
        "assumptions": [{"key": k, "label": label, "default": default, "help": text} for k, (label, default, text) in ASSUMPTIONS.items()],
        "scoreWeights": WEIGHTS,
        "partLabels": PART_LABELS,
        "roleLabels": ROLE_LABELS,
        "coreRoles": list(CORE_ROLES),
        "defaultParty": [PRESETS[name].to_dict() for name in DEFAULT_PARTY],
        "savedParties": [{"name": p["name"], "notes": p["notes"], "builds": [b.to_dict() for b in p["builds"]]} for p in saved_parties()],
    }

def _enemy(enemy_dict):
    return Enemy.from_dict(enemy_dict) if enemy_dict else Enemy()

def _builder_summary(build):
    """ Point buy, the class split at each act, feat levels and problems for a custom character """
    if not build.character:
        return None
    character = Bg3Character.from_dict(build.character)
    levels = [act_level(a, build.levels) for a in ACT_KEYS]
    problems = point_buy_problems(character.scores, character.bonus)
    total = len(class_order(character))
    if total < max(levels):
        problems.append(f"{total} class levels, the last act checkpoint needs {max(levels)}")
    try:
        cost = point_buy_cost(character.scores)
    except ValueError:
        cost = None
    items = catalog()
    last = equipment_at(build, ACT_KEYS[-1])
    _, notes = compile_character(character, max(levels), main_weapon_finesse(character, {s: items[k] for s, k in last.items() if k in items}))
    return {"pointBuy": cost, "featLevels": [lv for lv, _ in feat_opportunities(character)],
            "split": {a: class_levels(character, lv) for a, lv in zip(ACT_KEYS, levels)}, "problems": problems, "notes": notes,
            "toggles": [{"value": k, "label": TOGGLES[k], "on": TOGGLE_DEFAULTS.get(k, True)} for k in relevant_toggles(character.classes)]}

def saving_throws(character, enemy):
    """ The saving throws a build forces on the enemy, one line per spell, and its spell save DC (None when nothing uses it) """
    contexts, _ = calculate_attack_and_damage_context(character, enemy)
    lines = {}
    for attack, a in zip(character.attacks, contexts):
        if a.saving_throw and attack.name not in lines:
            lines[attack.name] = {"name": attack.name, "stat": attack.saving_throw_stat, "dc": a.difficulty_class, "fixed": bool(attack.save_dc),
                                  "fail": round(hit_and_crit_chance(**asdict(a))[0], 3), "disadvantage": bool(a.disadvantage)}
    own = [line["dc"] for line in lines.values() if not line["fixed"]]
    return list(lines.values()), max(own) if own else None

def _party_enemies(builds, enemy, synergies=True):
    """ {act: (the enemy with the synergies the party sets up every fight, their names)}: a Resonance Stone doubles psychic damage,
        Reverberation lowers saves. The plain enemy when synergies is off """
    from bg3 import synergy # pylint: disable=import-outside-toplevel
    out = {}
    for act in ACT_KEYS:
        boosted, active = synergy.party_enemy(builds, act, enemy) if synergies else (enemy, [])
        out[act] = (boosted, [synergy.SYNERGIES[k].name for k in active])
    return out

def _member(build, enemy, rounds, attack_bonus, flagged, together):
    acts = {}
    items = catalog()
    for act in ACT_KEYS:
        character = compile_build(build, act)
        damage = [round(expected_damage_vs_enemies(character, enemy, rounds, n), 2) for n in ENEMY_COUNTS]
        boosted, names = together[act]
        ac, ac_parts = armour_class(build, act)
        result = score(build, act, enemy, rounds, attack_bonus)
        gear = equipment_at(build, act)
        before = equipment_at(build, ACT_KEYS[ACT_KEYS.index(act) - 1]) if act != "1" else {}
        saves, spell_dc = saving_throws(character, enemy)
        acts[act] = {
            "spellDc": spell_dc, "saves": saves,
            "level": act_level(act, build.levels),
            "damage": damage,
            "together": [round(expected_damage_vs_enemies(character, boosted, rounds, n), 2) for n in ENEMY_COUNTS] if names else damage,
            "ac": ac, "acParts": [{"source": s, "value": v} for s, v in ac_parts], "hitChance": round(hit_chance(ac, attack_bonus), 3),
            "score": result.total, "scoreParts": result.parts, "scoreNotes": result.notes,
            "inherited": {slot: items[key].name for slot, key in before.items() if key in items and slot not in build.equipment.get(act, {})},
            "flagged": [slot for slot, key in gear.items() if (act, key) in flagged],
        }
    return {"name": build.name, "acts": acts, "conditions": conditional_options(build), "builder": _builder_summary(build)}

def evaluate(party_dicts, enemy_dict=None, rounds=3, attack_bonus=None):
    """ Everything the planner shows for a party: per member and act, and the party's conflicts """
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    enemy = _enemy(enemy_dict)
    bonus = int(attack_bonus) if attack_bonus not in (None, "") else attack_bonus_for(enemy)
    conflicts = party_conflicts(builds)
    flagged = {}
    for c in conflicts:
        for name in c.members:
            flagged.setdefault(name, set()).update((c.act, k) for k in (c.items or [c.item]))
    out = []
    for c in conflicts:
        gains = shared_item_gains(builds, c, enemy, rounds) if c.kind == "shared" else {}
        out.append({"act": c.act, "kind": c.kind, "message": c.message, "members": c.members, "item": c.item,
                    "gains": {k: round(v, 2) for k, v in gains.items()}})
    together = _party_enemies(builds, enemy)
    return {"attackBonus": bonus, "members": [_member(b, enemy, rounds, bonus, flagged.get(b.name, set()), together) for b in builds], "conflicts": out,
            "synergies": {act: names for act, (_, names) in together.items()}}

def variants(build_dict, enemy_dict=None, rounds=3, enemies=1, attack_bonus=6, party_dicts=(), synergies=False):
    """ The build and each of its variants: damage (against the chosen number of enemies, and against 1 to 4), spell save DC, AC and score
        by act. synergies: damage against the enemy as the party (party_dicts) leaves it """
    build = Bg3Build.from_dict(build_dict)
    enemy = _enemy(enemy_dict)
    at = _party_enemies([Bg3Build.from_dict(b) for b in party_dicts], enemy, synergies and bool(party_dicts))
    rows = []
    for name, description, built in variant_builds(build):
        compiled = [compile_build(built, a) for a in ACT_KEYS]
        by_enemies = [[round(expected_damage_vs_enemies(c, at[a][0], rounds, n), 2) for n in ENEMY_COUNTS] for a, c in zip(ACT_KEYS, compiled)]
        rows.append({"name": name, "description": description, "damage": [values[min(max(int(enemies), 1), len(ENEMY_COUNTS)) - 1] for values in by_enemies],
                     "byEnemies": by_enemies, "spellDc": [saving_throws(c, enemy)[1] for c in compiled],
                     "ac": [armour_class(built, a)[0] for a in ACT_KEYS], "score": [score(built, a, enemy, rounds, attack_bonus).total for a in ACT_KEYS]})
    return rows

def frontier(build_dict, act="3", enemy_dict=None, rounds=3, enemies=1, party_dicts=(), selected=0, skip_taken=True, synergies=False):
    """ Gear and elixir combinations for the build at an act, damage against AC, and which are on the Pareto frontier (bg3.frontier) """
    from bg3.buffs import BUFFS # pylint: disable=import-outside-toplevel
    from bg3.frontier import solve # pylint: disable=import-outside-toplevel
    build = Bg3Build.from_dict(build_dict)
    party = [Bg3Build.from_dict(b) for b in party_dicts]
    act = str(act)
    at = _party_enemies(party, _enemy(enemy_dict), synergies and bool(party))
    exclude = taken_by_others(party, selected, act) if skip_taken and party else ()
    result = solve(build, act, at[act][0], rounds, max(int(enemies), 1), exclude)
    items = catalog()
    on = {id(p) for p in result["frontier"]}
    def name(key):
        return items[key].name if key in items else BUFFS[key].name if key in BUFFS else "Nothing"
    def point(p):
        return {"damage": round(p["damage"], 2), "ac": p["ac"], "drawbacks": p["drawbacks"], "frontier": id(p) in on,
                "changes": [{"slot": s, "key": k, "name": name(k)} for s, k in p["changes"]]}
    return {"current": point(result["current"]), "points": [point(p) for p in result["points"]]}

def use_variant(build_dict, index):
    """ The build with variant index copied into its gear, buffs and toggles (the variant is removed from the list) """
    build = Bg3Build.from_dict(build_dict)
    used = variant_build(build, build.variants[index])
    used.name, used.variants = build.name, [v for ii, v in enumerate(build.variants) if ii != index]
    return used.to_dict()

def apply_kit_to(party_dicts, selected, kit_key, act, skip_taken=True, only_empty=False):
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    taken = taken_by_others(builds, selected, act) if skip_taken else ()
    member, placed, blocked = apply_kit(builds[selected], kit_key, act, taken, only_empty=only_empty)
    items = catalog()
    return {"build": member.to_dict(), "placed": [items[k].name for k in placed.values()], "blocked": [SLOT_LABELS.get(s, s) for s in blocked]}

def best_gear_for(party_dicts, selected, acts, goal="damage", enemy_dict=None, rounds=3, enemies=1, attack_bonus=None, weapons=True, skip_taken=True,
                  synergies=False, keep_uncounted=True):
    """ The best gear a member can wear at the acts (bg3.loadout): the build with it, the gear on its own (to keep as a variant) and
        what changed """
    from bg3.loadout import GOALS, best_gear # pylint: disable=import-outside-toplevel
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    enemy = _enemy(enemy_dict)
    bonus = int(attack_bonus) if attack_bonus not in (None, "") else attack_bonus_for(enemy)
    goal = goal if goal in GOALS else "damage"
    at = _party_enemies(builds, enemy, synergies)
    gear, changes, kept = best_gear(builds, selected, [a for a in ACT_KEYS if a in acts], goal, enemy, rounds, enemies, bonus, weapons, skip_taken,
                                    enemy_at=lambda act: at[act][0], keep_uncounted=keep_uncounted)
    build = builds[selected]
    for act, slots in gear.items():
        build.equipment[act] = {**build.equipment.get(act, {}), **slots}
    return {"build": build.to_dict(), "gear": gear, "changes": changes, "kept": kept, "goal": GOALS[goal]}

def deconflict(party_dicts, enemy_dict=None, rounds=3):
    """ The party with every shared item settled (bg3.loadout.resolve_conflicts), the swaps that did it, and how many other conflicts
        (story choices, wrong slots, concentration) are left for the player """
    from bg3.loadout import resolve_conflicts # pylint: disable=import-outside-toplevel
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    party, steps = resolve_conflicts(builds, _enemy(enemy_dict), rounds)
    return {"party": [b.to_dict() for b in party], "steps": steps, "remaining": len(party_conflicts(party))}

def example(name):
    found = examples().get(name)
    return found.to_dict() if found else None

def party(party_dicts, act="2", active=None, enemy_dict=None, rounds=3, hit_points=300):
    """ Roles, synergies, damage with and without them, and a simulated party fight at an act """
    from bg3 import synergy # pylint: disable=import-outside-toplevel
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    enemy = _enemy(enemy_dict)
    enemy.hit_points = max(int(hit_points or enemy.hit_points), 1)
    descriptions = synergy.describe(builds, act, enemy)
    active = [k for k in (active if active is not None else synergy.default_active(builds, act)) if k in descriptions]
    rows, missing, overlaps = party_roles(builds, act)
    fight = synergy.simulate_party_fight(builds, act, enemy, rounds, active)
    return {
        "roles": [{"name": name, "roles": roles} for name, roles in rows], "missing": missing, "overlaps": overlaps,
        "synergies": [{"key": k, "text": v} for k, v in descriptions.items()], "active": active,
        "damage": [{"name": n, "alone": round(a, 2), "together": round(t, 2)} for n, a, t in synergy.party_damage(builds, act, enemy, rounds, active)],
        "fight": fight,
    }

def advice(build_dict, party_dicts, act="1", slot="melee_main", enemy_dict=None, rounds=3, synergies=False):
    """ What each worn item adds at an act, and the best items for a slot """
    build = Bg3Build.from_dict(build_dict)
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    enemy = _party_enemies(builds, _enemy(enemy_dict), synergies)[str(act)][0]
    return {
        "values": [{"slot": SLOT_LABELS[s], "item": i.name, "summary": item_summary(i), "gain": round(g, 2)} for s, i, g in item_values(build, act, enemy, rounds)],
        "suggestions": [{"key": i.key, "item": i.name, "summary": item_summary(i), "gain": round(g, 2), "act": i.act, "users": users}
                        for i, g, users in slot_suggestions(build, act, slot, enemy, rounds, party=builds)],
    }

def to_simulator(party_dicts, act=None, selected=None):
    """ Simulator characters from the party: every member at an act, or one member at every act """
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    if selected is not None:
        characters = [compile_build(builds[selected], a) for a in ACT_KEYS]
    else:
        characters = [compile_build(b, act or "1") for b in builds]
    return [c.to_dict() for c in characters]

def import_doc(source):
    """ Re-imports the example builds from a build reference document link (bg3.doc_import), replacing bg3/data/doc_builds.json.
        Returns {builds: [{name, notes}]} or {problems} """
    import json
    import re
    import urllib.error
    from bg3.doc_import import OUT, fetch_text, import_text
    # Only Google Docs links: the server fetches the link itself, so it mustn't be pointed at anything else
    if not re.match(r"https://docs\.google\.com/document/d/[\w-]+", source):
        return {"problems": ["Paste a link to a Google Doc (https://docs.google.com/document/d/...)"]}
    try:
        builds = import_text(fetch_text(source))
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return {"problems": [f"Couldn't read the document: {e}"]}
    if not builds:
        return {"problems": ["No 'Build N: Title' sections found in the document"]}
    OUT.write_text(json.dumps(builds, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"builds": [{"name": b["build"]["name"], "notes": b.get("notes", [])} for b in builds]}
