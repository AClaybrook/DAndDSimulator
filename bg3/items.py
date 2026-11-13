""" Items, their effects, and applying effects to a character's attacks.
    Named items come from bg3/data/items.json, base weapons (non-unique, sold by vendors) from the weapon table """
import json
from dataclasses import dataclass, field, fields, replace
from functools import cache
from pathlib import Path

from computations.models import STATS, Attack
from game_data import weapons
from game_data.classes import FIGHTS_PER_LONG_REST

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
    "main_weapon": lambda a: a.is_weapon and not a.offhand, # A spell cast on one weapon, i.e. Magic Weapon
    "melee_weapon": lambda a: a.type == "weapon (melee)",
    "ranged_weapon": lambda a: a.type in ("weapon (ranged)", "thrown"),
    "thrown": lambda a: a.type == "thrown",
    "unarmed": lambda a: a.type == "unarmed",
    "spell": lambda a: a.type == "spell",
    "booming_blade": lambda a: "booming_blade" in a.tags, # The weapon attack Booming Blade makes
    "necromancy": lambda a: a.type == "spell" and "necromancy" in a.tags,
}

@dataclass
class Effect:
    """ One modelled effect of an item or buff.
        kind: ability_min (stat becomes at least value), ability_bonus (+value, up to max_value), attack_bonus, attack_dice,
              damage_bonus (same type as the attack), damage_bonus_ability (the stat's modifier, the attack's own stat for 'spellcasting', the items' casting ability for 'casting'),
              extra_damage (typed, i.e. '1d4 fire'), crit_damage (extra damage on a crit), crit_range (crit on value lower),
              advantage, damage_reroll (reroll damage dice at or below value), miss_damage_ability (the stat's modifier on a miss, Tenacity),
              once_per_turn_bonus (more Sneak Attack damage), spell_dc, extra_action (Haste), lightning_charges (gained on hits of applies_to),
              flag (turns on a Character option, i.e. savage_attacker), save_disadvantage (enemies roll saves against these attacks twice
              and keep the lower), free_cast (value more casts a fight of the limited spell it applies to), channel_divinity (value more
              Channel Divinity charges per long rest), advantage_chance (advantage on that share of the attack rolls), limited_haste
              (value more actions a fight from a Haste the item casts, unless Haste is already on), main_hand_bonus_attack (in the off hand, the
              bonus action attack is made with the main hand weapon: Belm). An attack_bonus of 'proficiency'
              adds the proficiency bonus again (The Dead Shot)
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
    # Effects of one item that share a condition are one toggle (the id of the first)
    on = {e.condition for ii, e in enumerate(effects) if e.condition and condition_id(owner_key, ii) in conditions}
    return [e for e in effects if not e.condition or e.condition in on]

def _attacks_for(character, effect, own_attacks):
    if effect.applies_to == "self":
        return own_attacks
    applies = APPLIES_TO.get(effect.applies_to, APPLIES_TO["all"])
    attacks = [a for a in character.attacks if applies(a)]
    if (effect.condition or "").startswith("First weapon hit after"):
        # Ring of Elemental Infusion: one weapon attack a turn, the first after the elemental cantrip (Booming Blade) or spell
        weapons = [a for a in attacks if a.is_weapon and not a.uses_per_fight]
        after = next((ii for ii, a in enumerate(weapons) if "booming_blade" in a.tags), None)
        pick = weapons[after + 1:after + 2] if after is not None else weapons[:1]
        return pick
    # Elemental cantrip effects (Necklace of Elemental Augmentation) don't count Booming Blade: its weapon attack isn't a spell (seen in game)
    return attacks

# Elixir of Bloodlust: once per turn, a kill gives an extra action. Against a group that is about every other turn of a 3 round fight
# (an estimate; against one enemy the kill ends the fight, so it adds nothing)
BLOODLUST_KILLS_PER_FIGHT = 1.5

def _action_attacks(character):
    """ The attacks of one Attack action (or cantrip cast): not bonus action, reaction, off hand or limited use attacks """
    def plain(a):
        waits = a.fallback_for and "after_cast" not in a.tags # After a spell cast with the action (Spirit Guardians) is still a plain attack
        return a.action == "action" and not (a.offhand or a.uses_per_fight or waits or a.min_enemies > 1)
    weapons = [a for a in character.attacks if (a.is_weapon or a.type == "unarmed") and plain(a)]
    return weapons or [a for a in character.attacks if a.type == "spell" and plain(a)]

def extra_action(character, label, honour_mode=False, uses=0):
    """ Another action each turn (Haste) or after a kill (Bloodlust): outside Honour Mode a whole Attack action, Extra Attack included;
        in Honour Mode one attack (bg3.wiki, Hastened: 'can not use Extra Attack with its additional action'). Casters get another cantrip """
    attacks = _action_attacks(character)
    if honour_mode and attacks and attacks[0].type != "spell":
        attacks = attacks[:1]
    # The extra action attacks from round 1, even when the action itself goes to casting a spell first
    character.attacks += [a.variant(label, action="extra", uses_per_fight=uses, fallback_for="", tags=[t for t in a.tags if t != "after_cast"])
                          for a in attacks]

def apply_effect(character, effect, own_attacks=(), honour_mode=False):
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
    elif kind == "extra_action_on_kill":
        # Another Attack action whenever a kill happens on your turn
        extra_action(character, "Bloodlust", honour_mode, uses=float(value))
    elif kind == "main_hand_bonus_attack":
        pass # Belm in the off hand: the bonus action attack is made with the main hand weapon (bg3.build.compile_build)
    elif kind == "channel_divinity":
        # One more charge a long rest for whatever spends them (Touch of Death)
        more = float(value) / FIGHTS_PER_LONG_REST
        for a in character.attacks:
            if "channel_divinity" in a.tags:
                a.uses_per_fight = round(a.uses_per_fight + more, 2)
                # A limited spell carrying the charge is cast as often as before: the cast moves over from the ones without a charge
                rest = next((b for b in character.attacks if b.fallback_for == a.name and b.uses_per_fight), None)
                if rest is not None:
                    rest.uses_per_fight = max(round(rest.uses_per_fight - more, 2), 0.01)
    elif kind == "free_cast":
        # More casts of the build's limited spell of that kind, i.e. the Staff of Cherished Necromancy's Life Essence
        spell = next((a for a in _attacks_for(character, effect, own_attacks) if a.uses_per_fight and a.action == "action" and not {"setup", "recharge", "channel_divinity"} & set(a.tags)), None)
        if spell is not None:
            spell.uses_per_fight = round(spell.uses_per_fight + float(value), 2)
    elif kind == "once_per_turn_bonus":
        # Only adds to once per turn damage the character already has every round, i.e. Sneak Attack (not to limited smites)
        if character.once_per_turn_die_mod_list and not character.once_per_turn_uses_per_fight:
            character.once_per_turn_die_mod_list = [*character.once_per_turn_die_mod_list, str(value)]
    else:
        for a in _attacks_for(character, effect, own_attacks):
            if kind in ("attack_bonus", "attack_dice"):
                bonus = character.proficiency_bonus if value == "proficiency" else value
                a.bonus_attack_die_mod_list = [*a.bonus_attack_die_mod_list, str(bonus)]
            elif kind == "damage_bonus":
                a.bonus_damage_die_mod_list = [*a.bonus_damage_die_mod_list, str(value)]
            elif kind == "damage_bonus_ability":
                if effect.stat == "casting":
                    # Arcane Synergy: the modifier of the ability the character's items cast with, on top of the weapon's own
                    stat = getattr(character, "casting_stat", "") or max(("intelligence", "wisdom", "charisma"), key=character.ability_modifier)
                    amount = max(character.ability_modifier(stat), 0)
                else:
                    amount = character.ability_modifier(a.ability_stat if effect.stat in ("", "spellcasting") else effect.stat)
                a.bonus_damage_die_mod_list = [*a.bonus_damage_die_mod_list, str(amount)]
            elif kind == "crit_damage":
                a.bonus_crit_die_mod_list = [*a.bonus_crit_die_mod_list, str(value)]
            elif kind == "extra_damage":
                a.extra_damage_list = [*a.extra_damage_list, str(value)]
            elif kind == "crit_range":
                a.crit_on = max(2, min(a.crit_on, character.crit_on) - int(value))
            elif kind == "advantage":
                a.advantage = True
            elif kind == "advantage_chance":
                a.advantage_chance = max(a.advantage_chance, float(value))
            elif kind == "save_disadvantage":
                a.save_disadvantage = True
            elif kind == "miss_damage_ability":
                a.bonus_miss_die_mod_list = [*a.bonus_miss_die_mod_list, str(max(1, character.ability_modifier(effect.stat or a.ability_stat)))]
            elif kind == "damage_reroll":
                a.damage_reroll_on = max(a.damage_reroll_on, int(value))

def apply_lightning_charges(character, sources):
    """ Lightning Charges (bg3.wiki): +1 to attack rolls and 1 extra lightning damage while you have any. Hits that gain charges keep at
        least one most of the fight, so they count on every attack once any attack can gain them. sources are (effect, own attacks) pairs.
        The 1d8 lightning when 5 charges are consumed isn't modelled """
    if not any(_attacks_for(character, effect, own) for effect, own in sources):
        return
    for a in character.attacks:
        a.bonus_attack_die_mod_list = [*a.bonus_attack_die_mod_list, "1"]
        a.extra_damage_list = [*a.extra_damage_list, "1 lightning"]

# Items whose wielder makes every reaction attack roll with advantage (bg3.wiki)
REACTION_ADVANTAGE = {"bg3:halberd_of_vigilance"}

def equip_weapon(attack, item):
    """ The attack made with a weapon item instead of the preset's weapon (dice, type, enhancement, properties) """
    w = item.weapon
    props = w.get("properties", [])
    two_handed = "two-handed" in props or (attack.two_handed and "versatile" in props and not attack.offhand)
    damage = w.get("versatile_damage") if two_handed and "versatile" in props and w.get("versatile_damage") else w["damage"]
    # BG3's Great Weapon Master counts any melee weapon held in both hands, a versatile one included (bg3.wiki, All In): the engine's
    # test for it is the heavy flag
    heavy = "heavy" in props or (two_handed and w.get("kind") == "melee")
    suffix = f" ({attack.label})" if attack.label else ""
    if "butt_end" in attack.tags: # The other end of the new polearm: its enhancement and properties, still 1d4 bludgeoning
        return replace(attack, base=w.get("base") or attack.base, weapon_enhancement=int(w.get("enhancement", 0)), two_handed=two_handed, heavy=heavy,
                       bonus_attack_die_mod_list=list(attack.bonus_attack_die_mod_list), bonus_damage_die_mod_list=list(attack.bonus_damage_die_mod_list),
                       extra_damage_list=list(attack.extra_damage_list))
    return replace(attack, name=item.name + suffix, base=w.get("base") or attack.base, damage=damage, damage_type=w["damage_type"],
                   weapon_enhancement=int(w.get("enhancement", 0)),
                   two_handed=two_handed, heavy=heavy,
                   bonus_attack_die_mod_list=list(attack.bonus_attack_die_mod_list), bonus_damage_die_mod_list=list(attack.bonus_damage_die_mod_list),
                   extra_damage_list=list(attack.extra_damage_list))

# Reverberation (bg3.wiki): each turn of it is -1 to STR/DEX/CON saves; at 5 or more the target takes 1d4 thunder, makes a CON save
# (DC 10, with the penalty effectively 15) or falls Prone, and the condition ends
REVERBERATION_TYPES = ("thunder", "lightning", "radiant")
ASSUMED_HIT_CHANCE = 0.65 # Items are compiled before the enemy is known, so stacks per round assume a typical chance to hit

def reverberation_hits(character):
    """ Attacks per round that deal thunder, lightning or radiant damage (the damage type or a rider) """
    def elemental(a):
        return a.damage_type in REVERBERATION_TYPES or any(t in r for r in a.extra_damage_list for t in REVERBERATION_TYPES)
    return sum(1 for a in character.attacks if elemental(a) and (not a.fallback_for or "after_cast" in a.tags) and "setup" not in a.tags)

def reverberation_per_round(character, gear_keys):
    """ Expected turns of Reverberation added per round: Gloves of Belligerent Skies add 2 per thunder, lightning or radiant hit, and Boots of
        Stormy Clamour 2 more whenever a condition (Reverberation included) is inflicted """
    if "bg3:gloves_of_belligerent_skies" not in gear_keys:
        return 0.0
    per_hit = 2 + 2 * ("bg3:boots_of_stormy_clamour" in gear_keys)
    return ASSUMED_HIT_CHANCE * reverberation_hits(character) * per_hit

def apply_reverberation(character, gear_keys):
    """ Adds the 5 stack burst as an attack: 1d4 thunder that always lands, in the share of rounds the target reaches 5 stacks (stacks drop by
        one each turn). Returns that share, which the party's Prone synergy uses """
    added = reverberation_per_round(character, gear_keys)
    if added <= 1:
        return 0.0
    share = min(1.0, (added - 1) / 5)
    # Uses per fight: bursts in a typical 3 round fight
    character.attacks = [*character.attacks, Attack(name="Reverberation (5 stacks)", type="spell", damage="1d4", damage_type="thunder",
                                                    always_hit=True, once_per_turn_eligible=False, uses_per_fight=round(3 * share, 2))]
    return share
