""" Items, their effects, and applying effects to a character's attacks.
    Named items come from bg3/data/items.json, base weapons (non-unique, sold by vendors) from the weapon table """
import json
from dataclasses import dataclass, field, fields, replace
from functools import cache
from pathlib import Path

from computations.models import STATS
from game_data import weapons

DATA = Path(__file__).parent / "data"

# Equipment slots: (key, label, item slot that fits)
SLOTS = [
    ("melee_main", "Melee Main Hand", "weapon"),
    ("melee_off", "Melee Off Hand", "weapon"),
    ("ranged_main", "Ranged Main Hand", "weapon"),
    ("ranged_off", "Ranged Off Hand", "weapon"),
    ("helmet", "Helmet", "helmet"),
    ("cloak", "Cloak", "cloak"),
    ("armour", "Armour", "armour"),
    ("gloves", "Gloves", "gloves"),
    ("boots", "Boots", "boots"),
    ("amulet", "Amulet", "amulet"),
    ("ring_1", "Ring", "ring"),
    ("ring_2", "Ring", "ring"),
]
SLOT_LABELS = {key: label for key, label, _ in SLOTS}
SLOT_FITS = {key: fits for key, _, fits in SLOTS}

# Which attacks an effect applies to
APPLIES_TO = {
    "all": lambda a: True,
    "weapon": lambda a: a.is_weapon,
    "melee_weapon": lambda a: a.type == "weapon (melee)",
    "ranged_weapon": lambda a: a.type in ("weapon (ranged)", "thrown"),
    "thrown": lambda a: a.type == "thrown",
    "unarmed": lambda a: a.type == "unarmed",
    "spell": lambda a: a.type == "spell",
}

@dataclass
class Effect:
    """ One modelled effect of an item or buff.
        kind: ability_min (stat becomes at least value), ability_bonus (+value, up to max_value), attack_bonus, attack_dice,
              damage_bonus (same type as the attack), damage_bonus_ability (the stat's modifier, or the attack's own stat for 'spellcasting'),
              extra_damage (typed, i.e. '1d4 fire'), crit_damage (extra damage on a crit), crit_range (crit on value lower),
              advantage, damage_reroll (reroll damage dice at or below value), miss_damage_ability (the stat's modifier on a miss, Tenacity),
              once_per_turn_bonus (more Sneak Attack damage), spell_dc, extra_attack (Haste),
              flag (turns on a Character option, i.e. savage_attacker)
        applies_to: a key of APPLIES_TO, or 'self' for the attacks made with the item's own weapon
        condition: when set, the effect only counts while the condition is toggled on, i.e. 'while raging' """
    kind: str
    value: int | str = 0
    stat: str = ""
    max_value: int = 30
    applies_to: str = "all"
    condition: str = ""

@dataclass
class Item:
    key: str
    name: str
    slot: str # weapon, helmet, cloak, armour, gloves, boots, amulet, ring, shield
    act: int | None = None # Act the item is first found in, None if unknown
    rarity: str = ""
    unique: bool = True
    # Weapons: base, kind (melee/ranged), damage, damage_type, enhancement, properties
    weapon: dict | None = None
    effects: list[Effect] = field(default_factory=list)
    notes: str = "" # Effects that are not modelled, shown in the UI
    location: str = ""
    source: str = ""
    reviewed: bool = False # Effects checked by hand, others are parsed from the item text

    @property
    def two_handed(self):
        return bool(self.weapon) and "two-handed" in self.weapon.get("properties", [])

    def fits(self, slot):
        fits = SLOT_FITS[slot]
        if self.slot == "shield":
            return slot == "melee_off"
        if fits != "weapon":
            return self.slot == fits
        if self.slot != "weapon" or not self.weapon:
            return False
        if slot.endswith("_off") and self.two_handed:
            return False # Two-handed weapons can't go in the off hand
        return (self.weapon.get("kind") == "ranged") == slot.startswith("ranged")

    @classmethod
    def from_dict(cls, data):
        names = {f.name for f in fields(cls)}
        data = {k: v for k, v in data.items() if k in names}
        data["effects"] = [Effect(**e) for e in data.get("effects", [])]
        return cls(**data)

def base_weapon_items():
    """ Base weapons from the weapon table, which BG3 shares with 5e. Vendors sell them, so they are not unique """
    items = []
    for name, w in weapons().items():
        weapon = {"base": name, "kind": w["kind"], "damage": w["damage"], "damage_type": w["damage_type"], "enhancement": 0,
                  "properties": w.get("properties", []), "versatile_damage": w.get("versatile_damage")}
        items.append(Item(key=f"base:{name.lower()}", name=name, slot="weapon", act=1, rarity="Common", unique=False, weapon=weapon))
    return items

@cache
def catalog():
    """ Every item by key """
    with open(DATA / "items.json", encoding="utf-8") as f:
        named = [Item.from_dict(i) for i in json.load(f)["items"]]
    return {i.key: i for i in base_weapon_items() + named}

def condition_id(owner_key, index):
    """ Id of a conditional effect, used for its toggle """
    return f"{owner_key}#{index}"

def active_effects(owner_key, effects, conditions):
    """ The effects that count: unconditional ones, and conditional ones that are toggled on """
    return [e for ii, e in enumerate(effects) if not e.condition or condition_id(owner_key, ii) in conditions]

def _attacks_for(character, effect, own_attacks):
    if effect.applies_to == "self":
        return own_attacks
    applies = APPLIES_TO.get(effect.applies_to, APPLIES_TO["all"])
    return [a for a in character.attacks if applies(a)]

def apply_effect(character, effect, own_attacks=()):
    """ Applies one effect to a character (in place). own_attacks are the attacks made with the item's weapon """
    kind, value = effect.kind, effect.value
    if kind == "ability_min" and effect.stat in STATS:
        setattr(character, effect.stat, max(getattr(character, effect.stat), int(value)))
    elif kind == "ability_bonus" and effect.stat in STATS:
        current = getattr(character, effect.stat)
        setattr(character, effect.stat, max(current, min(current + int(value), effect.max_value)))
    elif kind == "spell_dc":
        character.additional_spell_dc += int(value)
    elif kind == "flag":
        setattr(character, str(value), True)
    elif kind == "once_per_turn_bonus":
        # Only adds to once per turn damage the character already has, i.e. Sneak Attack
        if character.once_per_turn_die_mod_list:
            character.once_per_turn_die_mod_list = [*character.once_per_turn_die_mod_list, str(value)]
    else:
        for a in _attacks_for(character, effect, own_attacks):
            if kind in ("attack_bonus", "attack_dice"):
                a.bonus_attack_die_mod_list = [*a.bonus_attack_die_mod_list, str(value)]
            elif kind == "damage_bonus":
                a.bonus_damage_die_mod_list = [*a.bonus_damage_die_mod_list, str(value)]
            elif kind == "damage_bonus_ability":
                stat = a.ability_stat if effect.stat in ("", "spellcasting") else effect.stat
                a.bonus_damage_die_mod_list = [*a.bonus_damage_die_mod_list, str(character.ability_modifier(stat))]
            elif kind == "crit_damage":
                a.bonus_crit_die_mod_list = [*a.bonus_crit_die_mod_list, str(value)]
            elif kind == "extra_damage":
                a.extra_damage_list = [*a.extra_damage_list, str(value)]
            elif kind == "crit_range":
                a.crit_on = max(2, min(a.crit_on, character.crit_on) - int(value))
            elif kind == "advantage":
                a.advantage = True
            elif kind == "miss_damage_ability":
                a.bonus_miss_die_mod_list = [*a.bonus_miss_die_mod_list, str(max(1, character.ability_modifier(effect.stat or a.ability_stat)))]
            elif kind == "damage_reroll":
                a.damage_reroll_on = max(a.damage_reroll_on, int(value))

def equip_weapon(attack, item):
    """ The attack made with a weapon item instead of the preset's weapon (dice, type, enhancement, properties) """
    w = item.weapon
    props = w.get("properties", [])
    two_handed = "two-handed" in props or (attack.two_handed and "versatile" in props and not attack.offhand)
    damage = w.get("versatile_damage") if two_handed and "versatile" in props and w.get("versatile_damage") else w["damage"]
    suffix = attack.name[attack.name.index(" ("):] if " (" in attack.name else ""
    return replace(attack, name=item.name + suffix, damage=damage, damage_type=w["damage_type"], weapon_enhancement=int(w.get("enhancement", 0)),
                   two_handed=two_handed, heavy="heavy" in props,
                   bonus_attack_die_mod_list=list(attack.bonus_attack_die_mod_list), bonus_damage_die_mod_list=list(attack.bonus_damage_die_mod_list),
                   extra_damage_list=list(attack.extra_damage_list))
