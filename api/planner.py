""" The BG3 party planner as JSON: options for every picker, and evaluating a party (damage, AC and score per act, conflicts, warnings,
    variants), party roles, synergies and a party fight, gear advice, kits and example builds """
from bg3.abilities import point_buy_cost, point_buy_problems
from bg3.analysis import item_values, shared_item_gains, slot_suggestions
from bg3.buffs import BUFFS
from bg3.build import ACT_KEYS, Bg3Build, compile_build, equipment_at
from bg3.character import (CANTRIPS, CLASSES, FEATS, FIGHTING_STYLES, LEVELLED_SPELLS, RACES, ROUTINES, SUBCLASSES, TOGGLES, Bg3Character,
                           class_levels, class_order, compile_character, feat_opportunities, relevant_toggles)
from bg3.checkpoints import ACTS, act_level
from bg3.defence import armour_class, attack_bonus_for, hit_chance
from bg3.items import SLOT_LABELS, SLOTS, catalog
from bg3.kits import QUICK_VARIANTS, apply_kit, kits, taken_by_others, variant_build, variant_damage
from bg3.party import MAX_PARTY_SIZE, party_conflicts
from bg3.presets import DEFAULT_PARTY, PRESETS, examples
from bg3.roles import CORE_ROLES, ROLE_LABELS, party_roles
from bg3.score import WEIGHTS, score
from components.bg3_planner import conditional_options, grouped_item_options, item_summary, option_group
from computations.analytic import expected_damage_vs_enemies
from computations.models import STATS, Enemy
from game_data.classes import BUILDS

ENEMY_COUNTS = [1, 2, 3, 4]
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
        "builder": {"races": RACES, "classes": CLASSES, "subclasses": SUBCLASSES, "improvements": improvements, "fightingStyles": FIGHTING_STYLES,
                    "routines": [{"value": k, "label": v} for k, v in ROUTINES.items()], "cantrips": CANTRIPS, "spells": LEVELLED_SPELLS,
                    "toggles": [{"value": k, "label": v} for k, v in TOGGLES.items()], "defaultCharacter": Bg3Character().to_dict()},
        "scoreWeights": WEIGHTS,
        "partLabels": PART_LABELS,
        "roleLabels": ROLE_LABELS,
        "coreRoles": list(CORE_ROLES),
        "defaultParty": [PRESETS[name].to_dict() for name in DEFAULT_PARTY],
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
    _, notes = compile_character(character, max(levels))
    return {"pointBuy": cost, "featLevels": [lv for lv, _ in feat_opportunities(character)],
            "split": {a: class_levels(character, lv) for a, lv in zip(ACT_KEYS, levels)}, "problems": problems, "notes": notes,
            "toggles": [{"value": k, "label": TOGGLES[k]} for k in relevant_toggles(character.classes)]}

def _member(build, enemy, rounds, attack_bonus, flagged):
    acts = {}
    items = catalog()
    for act in ACT_KEYS:
        character = compile_build(build, act)
        ac, ac_parts = armour_class(build, act)
        result = score(build, act, enemy, rounds, attack_bonus)
        gear = equipment_at(build, act)
        before = equipment_at(build, ACT_KEYS[ACT_KEYS.index(act) - 1]) if act != "1" else {}
        acts[act] = {
            "level": act_level(act, build.levels),
            "damage": [round(expected_damage_vs_enemies(character, enemy, rounds, n), 2) for n in ENEMY_COUNTS],
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
    return {"attackBonus": bonus, "members": [_member(b, enemy, rounds, bonus, flagged.get(b.name, set())) for b in builds], "conflicts": out}

def variants(build_dict, enemy_dict=None, rounds=3, enemies=1, attack_bonus=6):
    """ The build and each of its variants: damage, AC and score by act """
    build = Bg3Build.from_dict(build_dict)
    enemy = _enemy(enemy_dict)
    rows = []
    for name, description, values, built in variant_damage(build, enemy, rounds, enemies):
        rows.append({"name": name, "description": description, "damage": [round(v, 2) for v in values],
                     "ac": [armour_class(built, a)[0] for a in ACT_KEYS], "score": [score(built, a, enemy, rounds, attack_bonus).total for a in ACT_KEYS]})
    return rows

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

def advice(build_dict, party_dicts, act="1", slot="melee_main", enemy_dict=None, rounds=3):
    """ What each worn item adds at an act, and the best items for a slot """
    build = Bg3Build.from_dict(build_dict)
    enemy = _enemy(enemy_dict)
    builds = [Bg3Build.from_dict(b) for b in party_dicts]
    return {
        "values": [{"slot": SLOT_LABELS[s], "item": i.name, "summary": item_summary(i), "gain": round(g, 2)} for s, i, g in item_values(build, act, enemy, rounds)],
        "suggestions": [{"key": i.key, "item": i.name, "summary": item_summary(i), "gain": round(g, 2), "act": i.act, "users": users}
                        for i, g, users in slot_suggestions(build, act, slot, enemy, rounds, party=builds)],
    }
