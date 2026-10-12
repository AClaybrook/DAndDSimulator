""" Game database: weapons, spells, monsters and class presets, used to prefill the generic simulator inputs """
from functools import cache
import json
from pathlib import Path

from computations.models import Attack, Enemy, STATS

DATA_DIR = Path(__file__).parent

RULESETS = {
    "bg3": {"label": "Baldur's Gate 3", "max_level": 12, "cantrip_levels": (5, 10)},
    "5e": {"label": "D&D 5e (2014)", "max_level": 20, "cantrip_levels": (5, 11, 17)},
}

@cache
def _load(name):
    with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)

def weapons():
    """ All weapons keyed by name """
    return {w["name"]: w for w in _load("weapons")["weapons"]}

def spells():
    """ All spells keyed by name """
    return {s["name"]: s for s in _load("spells")["spells"]}

def monsters():
    """ All monsters keyed by name """
    return {m["name"]: m for m in _load("monsters")["monsters"]}

def cantrip_tier(level, ruleset="bg3"):
    """ Number of damage dice (or beams) a cantrip has at a given character level """
    return 1 + sum(level >= lvl for lvl in RULESETS[ruleset]["cantrip_levels"])

def _scale_dice(dice, multiplier):
    """ '1d10' * 2 -> '2d10', keeps any flat modifier as is """
    num, rest = dice.lower().split("d", 1)
    return f"{int(num or 1) * multiplier}d{rest}"

def _add_dice(dice, extra, times):
    """ '8d6' + 2 * '1d6' -> '10d6' when the die sizes match """
    if times <= 0 or not extra:
        return dice
    num, rest = dice.lower().split("d", 1)
    size, *mod = rest.replace("-", "+-").split("+", 1)
    extra_num, extra_size = extra.lower().split("d")
    if size == extra_size:
        return f"{int(num) + int(extra_num) * times}d{size}" + (f"+{mod[0]}".replace("+-", "-") if mod else "")
    return dice

def weapon_attack(name, ability_stat=None, two_handed=None, offhand=False, enhancement=0, bonus_damage=None, attack_name=None):
    """ Builds an Attack from a weapon in the database
        ability_stat defaults to strength for melee and dexterity for ranged weapons
        two_handed uses the versatile damage die when True """
    w = weapons()[name]
    props = w.get("properties", [])
    attack_type = "weapon (ranged)" if w["kind"] == "ranged" else "weapon (melee)"
    if ability_stat is None:
        ability_stat = "dexterity" if w["kind"] == "ranged" else "strength"
    if two_handed is None:
        two_handed = "two-handed" in props
    damage = w["damage"]
    if two_handed and "versatile" in props:
        damage = w["versatile_damage"]
    return Attack(
        name=attack_name or (f"{name} (Offhand)" if offhand else name),
        type=attack_type,
        ability_stat=ability_stat,
        damage=damage,
        damage_type=w["damage_type"],
        two_handed=bool(two_handed),
        heavy="heavy" in props,
        offhand=offhand,
        weapon_enhancement=enhancement,
        bonus_damage_die_mod_list=list(bonus_damage or []),
    )

def spell_attacks(name, ability_stat="charisma", character_level=1, slot_level=None, ruleset="bg3", bonus_damage=None):
    """ Builds the Attacks for a spell (one per beam/ray/dart), scaled by character level (cantrips) or slot level """
    s = spells()[name]
    damage = s["damage"]
    projectiles = s.get("projectiles", 1)
    if s["level"] == 0:
        tier = cantrip_tier(character_level, ruleset)
        if s.get("scaling") == "projectiles":
            projectiles *= tier
        else:
            damage = _scale_dice(damage, tier)
    else:
        upcast = max((slot_level or s["level"]) - s["level"], 0)
        damage = _add_dice(damage, s.get("upcast"), upcast)
        projectiles += s.get("upcast_projectiles", 0) * upcast
    label = name if s["level"] == 0 or not slot_level or slot_level == s["level"] else f"{name} (Level {slot_level})"
    attack = Attack(
        name=label,
        type="spell",
        ability_stat=ability_stat,
        damage=damage,
        damage_type=s["damage_type"],
        always_hit=s["attack"] == "auto",
        saving_throw=s["attack"] == "save",
        saving_throw_stat=s.get("save", "dexterity"),
        saving_throw_success_multiplier=s.get("on_save", 0),
        bonus_damage_die_mod_list=list(bonus_damage or []),
    )
    return [attack] + [Attack(**{**attack.to_dict(), "bonus_damage_die_mod_list": list(attack.bonus_damage_die_mod_list)}) for _ in range(projectiles - 1)]

def enemy_from_monster(name):
    """ Builds an Enemy from the monster database """
    m = monsters()[name]
    abilities = dict(zip(STATS, m["abilities"]))
    saves = {f"{stat}_save": mod for stat, mod in m.get("saves", {}).items()}
    return Enemy(
        name=name,
        armor_class=m["armor_class"],
        hit_points=m["hit_points"],
        challenge_rating=m["cr"],
        resistances=list(m.get("resistances", [])),
        vulnerabilities=list(m.get("vulnerabilities", [])),
        immunities=list(m.get("immunities", [])),
        **abilities,
        **saves,
    )

# Dungeon Master's Guide "Monster Statistics by Challenge Rating": (armor class, (min hit points, max hit points))
CR_BASELINES = {
    0.125: (13, (7, 35)), 0.25: (13, (36, 49)), 0.5: (13, (50, 70)),
    1: (13, (71, 85)), 2: (13, (86, 100)), 3: (13, (101, 115)), 4: (14, (116, 130)), 5: (15, (131, 145)),
    6: (15, (146, 160)), 7: (15, (161, 175)), 8: (16, (176, 190)), 9: (16, (191, 205)), 10: (17, (206, 220)),
    11: (17, (221, 235)), 12: (17, (236, 250)), 13: (18, (251, 265)), 14: (18, (266, 280)), 15: (18, (281, 295)),
    16: (18, (296, 310)), 17: (19, (311, 325)), 18: (19, (326, 340)), 19: (19, (341, 355)), 20: (19, (356, 400)),
}

def cr_label(cr):
    return {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}.get(cr, str(int(cr)))

def enemy_from_challenge_rating(cr):
    """ A generic enemy with the typical armor class and hit points for a challenge rating (DMG guidelines) """
    armor_class, (hp_min, hp_max) = CR_BASELINES[cr]
    return Enemy(name=f"CR {cr_label(cr)} Baseline", armor_class=armor_class, hit_points=(hp_min + hp_max) // 2, challenge_rating=cr)

def enemy_presets():
    """ Options for the enemy preset dropdown: (label, value) """
    options = [(f"{m['name']} (CR {cr_label(m['cr']) if m['cr'] else 0}, AC {m['armor_class']})", f"monster:{m['name']}") for m in monsters().values()]
    options += [(f"CR {cr_label(cr)} Baseline (AC {ac}, HP {(lo + hi) // 2})", f"cr:{cr}") for cr, (ac, (lo, hi)) in CR_BASELINES.items()]
    return options

def enemy_from_preset(value):
    kind, key = value.split(":", 1)
    if kind == "monster":
        return enemy_from_monster(key)
    return enemy_from_challenge_rating(float(key) if "." in key else int(key))

def attack_templates():
    """ Options for the attack template dropdown: (label, value) """
    options = []
    for w in weapons().values():
        if "versatile" in w.get("properties", []):
            options.append((f"Weapon: {w['name']} (one-handed, {w['damage']})", f"weapon:{w['name']}:1h"))
            options.append((f"Weapon: {w['name']} (two-handed, {w['versatile_damage']})", f"weapon:{w['name']}:2h"))
        else:
            options.append((f"Weapon: {w['name']} ({w['damage']})", f"weapon:{w['name']}:"))
    for s in spells().values():
        level = "Cantrip" if s["level"] == 0 else f"Level {s['level']}"
        options.append((f"Spell: {s['name']} ({level})", f"spell:{s['name']}:"))
    return options

def attacks_from_template(value, ability_stat=None, character_level=1, ruleset="bg3"):
    """ Builds the attack(s) for an attack template dropdown value """
    kind, name, grip = value.split(":", 2)
    if kind == "weapon":
        finesse_or_ranged = weapons()[name]["kind"] == "ranged" or "finesse" in weapons()[name].get("properties", [])
        stat = ability_stat if ability_stat in ("strength", "dexterity") and finesse_or_ranged else None
        return [weapon_attack(name, ability_stat=stat, two_handed=True if grip == "2h" else None)]
    spell_stat = ability_stat if ability_stat in ("intelligence", "wisdom", "charisma") else "charisma"
    return spell_attacks(name, ability_stat=spell_stat, character_level=character_level, ruleset=ruleset)
