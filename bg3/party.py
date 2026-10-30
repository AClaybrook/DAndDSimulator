""" Party checks: which unique items more than one character wants at the same act, and gear that doesn't fit a build.
    It only reports conflicts, choosing who gets an item is left to the player """
from collections import defaultdict
from dataclasses import dataclass

from bg3.build import ACT_KEYS, buffs_at, equipment_at
from bg3.character import Bg3Character, is_proficient, weapon_proficiencies
from bg3.checkpoints import act_level
from bg3.items import SLOT_LABELS, catalog

MAX_PARTY_SIZE = 4

@dataclass
class Conflict:
    act: str
    kind: str # shared (several characters), duplicate (one character, two slots), two_handed, wrong_slot, too_early, unknown, elixirs, concentration, proficiency
    item: str # Item key
    members: list[str]
    message: str

def build_conflicts(build, act, items=None):
    """ Problems with one character's gear at an act """
    items = items or catalog()
    act = str(act)
    gear = equipment_at(build, act)
    conflicts = []
    seen = defaultdict(list)
    for slot, key in gear.items():
        item = items.get(key)
        if item is None:
            conflicts.append(Conflict(act, "unknown", key, [build.name], f"{build.name}: unknown item '{key}' in {SLOT_LABELS[slot]}"))
            continue
        if not item.fits(slot):
            conflicts.append(Conflict(act, "wrong_slot", key, [build.name], f"{build.name}: {item.name} doesn't fit {SLOT_LABELS[slot]}"))
        if item.act is not None and item.act > int(act):
            conflicts.append(Conflict(act, "too_early", key, [build.name], f"{build.name}: {item.name} is found in Act {item.act}, not by Act {act}"))
        if item.unique:
            seen[key].append(slot)
    for key, slots in seen.items():
        if len(slots) > 1:
            conflicts.append(Conflict(act, "duplicate", key, [build.name],
                                      f"{build.name}: {items[key].name} is unique but equipped in {' and '.join(SLOT_LABELS[s] for s in slots)}"))
    if build.character:
        profs = weapon_proficiencies(Bg3Character.from_dict(build.character), act_level(act, build.levels))
        for key in gear.values():
            item = items.get(key)
            if item is not None and item.weapon and not is_proficient(item.weapon.get("base"), profs):
                conflicts.append(Conflict(act, "proficiency", key, [build.name],
                                          f"{build.name}: not proficient with {item.name} ({item.weapon.get('base')}), no proficiency bonus to hit"))
    own_concentration = [b.name for b in buffs_at(build, act) if b.concentration and b.self_cast]
    if len(own_concentration) > 1:
        conflicts.append(Conflict(act, "concentration", "", [build.name],
                                  f"{build.name}: can only concentrate on one of {', '.join(own_concentration)}"))
    exclusive = [b.name for b in buffs_at(build, act) if b.exclusive]
    if len(exclusive) > 1:
        conflicts.append(Conflict(act, "elixirs", "", [build.name],
                                  f"{build.name}: only one of {', '.join(exclusive)} works at a time, each ends the elixir drunk before"))
    for hand in ("melee", "ranged"):
        main, off = items.get(gear.get(f"{hand}_main", "")), gear.get(f"{hand}_off")
        if main is not None and main.two_handed and off:
            conflicts.append(Conflict(act, "two_handed", main.key, [build.name],
                                      f"{build.name}: {main.name} is two-handed, so the {hand} off hand must be empty"))
    return conflicts

def party_conflicts(builds, items=None, acts=None):
    """ Every conflict in a party, per act: unique items wanted by several characters, plus each character's own gear problems """
    items = items or catalog()
    conflicts = []
    for act in acts or ACT_KEYS:
        users = defaultdict(list)
        for build in builds:
            conflicts += build_conflicts(build, act, items)
            for key in set(equipment_at(build, act).values()):
                if key in items and items[key].unique:
                    users[key].append(build.name)
        conflicts += concentration_conflicts(builds, act)
        for key, members in users.items():
            if len(members) > 1:
                conflicts.append(Conflict(str(act), "shared", key, members, f"{items[key].name} is wanted by {', '.join(members)}"))
    return conflicts

def concentration_conflicts(builds, act):
    """ Each party member can concentrate on one spell. Buffs cast by others need a concentrating caster per cast
        (Bless covers up to 3 targets), and characters concentrating on their own spell (i.e. Hex) can't also cast them """
    act = str(act)
    casts, busy = {}, 0
    for build in builds:
        buffs = buffs_at(build, act)
        busy += any(b.concentration and b.self_cast for b in buffs)
        for b in buffs:
            if b.concentration and not b.self_cast:
                casts.setdefault(b.name, [0, b.targets])[0] += 1
    needed = sum(-(-count // targets) for count, targets in casts.values())
    if needed + busy > len(builds):
        wanted = ", ".join(f"{name} on {count}" for name, (count, _) in casts.items())
        return [Conflict(act, "concentration", "", [b.name for b in builds],
                         f"{wanted} need {needed} concentrating caster{'s' if needed != 1 else ''}, but only {len(builds) - busy} "
                         f"party member{'s are' if len(builds) - busy != 1 else ' is'} free to concentrate")]
    return []

def conflicting_items(conflicts, act=None):
    """ Item keys involved in shared conflicts (optionally at one act), used to highlight them """
    return {c.item for c in conflicts if c.kind == "shared" and (act is None or c.act == str(act))}
