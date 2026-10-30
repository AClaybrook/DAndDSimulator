""" A BG3 build: a class preset with equipment, buffs and toggled conditions for each act.
    compile_build turns it into a plain Character at an act checkpoint, which the simulator uses as is """
from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields, replace

from bg3.buffs import BUFFS
from bg3.character import Bg3Character, compile_character, is_proficient, weapon_proficiencies
from bg3.checkpoints import ACTS, act_level
from bg3.items import SLOT_LABELS, SLOTS, active_effects, apply_effect, catalog, equip_weapon
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
    """ The equipment slot an attack is made with, None for unarmed attacks and spells """
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
    if build.character:
        character, _ = compile_character(Bg3Character.from_dict(build.character), level)
    else:
        character = build_character(build.preset, level, "bg3")
    gear = {slot: items[key] for slot, key in equipment_at(build, act).items() if key in items and items[key].fits(slot)}

    # Weapons replace the preset's weapon for the attacks made with them. Custom characters lose the proficiency bonus with weapons they
    # aren't proficient with (presets are assumed proficient)
    profs = weapon_proficiencies(Bg3Character.from_dict(build.character), level) if build.character else None
    own_attacks = {slot: [] for slot in gear}
    attacks = []
    for attack in character.attacks:
        slot = _weapon_slot(attack)
        item = gear.get(slot)
        if item is not None and item.weapon:
            attack = equip_weapon(attack, item)
            if profs is not None:
                attack.proficient = is_proficient(item.weapon.get("base"), profs)
            own_attacks[slot].append(attack)
        else:
            attack = deepcopy(attack)
        attacks.append(attack)
    character.attacks = attacks

    # Ability scores first, so later effects see the final stats
    sources = [(item.key, item.effects, own_attacks.get(slot, [])) for slot, item in gear.items()]
    sources += [(f"buff:{b.key}", b.effects, []) for b in buffs_at(build, act)]
    effects = [(e, own) for key, effects_, own in sources for e in active_effects(key, effects_, build.conditions)]
    effects.sort(key=lambda pair: not pair[0].kind.startswith("ability"))
    extra_attacks = 0
    for effect, own in effects:
        if effect.kind == "extra_attack":
            extra_attacks += int(effect.value)
        else:
            apply_effect(character, effect, own)

    # Haste: one more attack with the main weapon each round
    main = next((a for a in character.attacks if a.is_weapon and not a.offhand and not a.uses_per_fight and not a.fallback_for), None)
    if main is not None:
        character.attacks += [replace(main, name=f"{main.name.split(' (')[0]} (Haste)") for _ in range(extra_attacks)]

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
