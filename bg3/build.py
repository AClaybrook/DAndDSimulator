""" A BG3 build: a class preset with equipment, buffs and toggled conditions for each act.
    compile_build turns it into a plain Character at an act checkpoint, which the simulator uses as is """
from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields

from bg3.buffs import BUFFS
from bg3.character import Bg3Character, compile_character, is_proficient, weapon_proficiencies
from bg3.checkpoints import ACTS, act_level
from bg3.items import (REACTION_ADVANTAGE, SLOT_LABELS, SLOTS, active_effects, apply_effect, apply_lightning_charges, apply_reverberation, catalog,
                       equip_weapon, extra_action)
from game_data.classes import BUILDS, build_character

ACT_KEYS = [str(a) for a in ACTS]

@dataclass
class Bg3Build:
    name: str
    preset: str # A key of game_data.classes.BUILDS, which handles class features, feats and attacks per level
    # Act ("1", "2", "3"): slot: item key. Empty slots keep the item from the act before
    equipment: dict[str, dict[str, str]] = field(default_factory=dict)
    buffs: dict[str, list[str]] = field(default_factory=dict) # Act: buff keys
    conditions: list[str] = field(default_factory=list) # Conditional effects that are toggled on
    levels: dict[str, int] = field(default_factory=dict) # Act: level, overrides the default checkpoints
    # A custom character (bg3.character.Bg3Character as a dict) used instead of the class preset
    character: dict | None = None
    carried: list[str] = field(default_factory=list) # Items carried rather than worn, i.e. the Resonance Stone
    roles: list[str] = field(default_factory=list) # Party roles from the build's source, added to the ones worked out from its classes
    # Named "what ifs" compared next to the build (bg3.kits): {"name", "kit", "act", "buffs", "toggles", "conditions"}. They never change the gear
    variants: list[dict] = field(default_factory=list)
    advantage: bool = False # Attacks with advantage (for class presets; custom characters have the "advantage" toggle)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})

def equipment_at(build, act):
    """ Slot: item key at an act, items carry over from earlier acts until replaced. An empty string clears a slot """
    gear = {}
    for a in ACT_KEYS[:ACT_KEYS.index(str(act)) + 1]:
        gear.update(build.equipment.get(a, {}))
    return {slot: key for slot, key in gear.items() if key}

def buffs_at(build, act):
    return [BUFFS[b] for b in build.buffs.get(str(act), []) if b in BUFFS]

def _weapon_slot(attack):
    """ The equipment slot an attack is made with, None for unarmed attacks, spells and conjured weapons (Shadow Blade) """
    if "conjured" in attack.tags:
        return None
    if attack.type == "weapon (melee)":
        return "melee_off" if attack.offhand else "melee_main"
    if attack.type in ("weapon (ranged)", "thrown"):
        if attack.type == "thrown":
            return "melee_main"
        return "ranged_off" if attack.offhand else "ranged_main"
    return None

def compile_build(build, act, items=None):
    """ The build's Character at an act checkpoint, with gear, buffs and toggled conditions applied """
    items = items or catalog()
    level = act_level(act, build.levels)
    gear = {slot: items[key] for slot, key in equipment_at(build, act).items() if key in items and items[key].fits(slot)}
    if build.character:
        # A finesse or ranged weapon from gear decides Sneak Attack and Flick o' the Wrist (i.e. The Dancing Breeze, a finesse glaive)
        bg3_character = Bg3Character.from_dict(build.character)
        weapon = (gear.get("ranged_main") if bg3_character.routine in ("ranged", "dual_hand_crossbows") else gear.get("melee_main"))
        weapon = weapon.weapon if weapon is not None and weapon.weapon else None
        finesse = None if weapon is None else weapon.get("kind") == "ranged" or "finesse" in (weapon.get("properties") or [])
        character, _ = compile_character(bg3_character, level, finesse)
    else:
        character = build_character(build.preset, level, "bg3")

    # Weapons replace the preset's weapon for the attacks made with them. Custom characters lose the proficiency bonus with weapons they
    # aren't proficient with (presets are assumed proficient)
    profs = weapon_proficiencies(Bg3Character.from_dict(build.character), level) if build.character else None
    own_attacks = {slot: [] for slot in gear}
    names = {} # Old: new attack names, so fallbacks still point at their limited attack
    attacks = []
    for attack in character.attacks:
        slot = _weapon_slot(attack)
        item = gear.get(slot)
        if item is not None and item.weapon:
            renamed = equip_weapon(attack, item)
            names[attack.name] = renamed.name
            attack = renamed
            # A finesse weapon from gear hits with the higher of Strength and Dexterity (unless the build hits with Charisma, i.e. a pact weapon)
            if "finesse" in (item.weapon.get("properties") or []) and attack.ability_stat in ("strength", "dexterity"):
                attack.ability_stat = "dexterity" if character.dexterity > character.strength else "strength"
            if profs is not None:
                attack.proficient = is_proficient(item.weapon.get("base"), profs)
            own_attacks[slot].append(attack)
        else:
            attack = deepcopy(attack)
        attacks.append(attack)
    if any(item.key in REACTION_ADVANTAGE for item in gear.values()):
        for attack in attacks:
            if attack.action == "reaction":
                attack.advantage = True
    for attack in attacks:
        if attack.fallback_for in names:
            attack.fallback_for = names[attack.fallback_for]
    character.attacks = attacks

    # Ability scores first, so later effects see the final stats
    sources = [(item.key, item.effects, own_attacks.get(slot, [])) for slot, item in gear.items()]
    sources += [(f"buff:{b.key}", b.effects, []) for b in buffs_at(build, act)]
    effects = [(e, own) for key, effects_, own in sources for e in active_effects(key, effects_, build.conditions)]
    effects.sort(key=lambda pair: not pair[0].kind.startswith("ability"))
    honour_mode = bool(build.character) and Bg3Character.from_dict(build.character).toggle("honour_mode")
    extra_actions = 0
    for effect, own in effects:
        if effect.kind == "extra_action":
            extra_actions += int(effect.value)
        elif effect.kind != "lightning_charges":
            apply_effect(character, effect, own, honour_mode)
    # Charges from several items don't stack their bonuses
    apply_lightning_charges(character, [(e, own) for e, own in effects if e.kind == "lightning_charges"])
    apply_reverberation(character, {item.key for item in gear.values()})

    # Haste: one more action each round (the Hastened condition doesn't stack, so one at most)
    if extra_actions:
        extra_action(character, "Haste", honour_mode)

    if build.advantage:
        character.advantage = True
    label = ACTS[int(act)][0]
    character.name = f"{build.name} ({label})" if build.name else label
    worn = ", ".join(f"{SLOT_LABELS[slot]}: {item.name}" for slot, item in gear.items())
    base = character.description if build.character else f"{BUILDS[build.preset].label}, level {level}"
    character.description = f"{base}. {worn or 'No equipment'}" + \
        (f". Buffs: {', '.join(b.name for b in buffs_at(build, act))}" if buffs_at(build, act) else "")
    # Gear is part of the build, so level sweeps should not rebuild the preset without it
    character.preset = ""
    return character

def slot_order():
    return [key for key, _, _ in SLOTS]
