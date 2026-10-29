""" Party checks: which unique items more than one character wants at the same act, and gear that doesn't fit a build.
    It only reports conflicts, choosing who gets an item is left to the player """
from collections import defaultdict
from dataclasses import dataclass

from bg3.build import ACT_KEYS, equipment_at
from bg3.items import SLOT_LABELS, catalog

MAX_PARTY_SIZE = 4

@dataclass
class Conflict:
    act: str
    kind: str # shared (several characters), duplicate (one character, two slots), two_handed, wrong_slot, too_early, unknown
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
        for key, members in users.items():
            if len(members) > 1:
                conflicts.append(Conflict(str(act), "shared", key, members, f"Act {act}: {items[key].name} is wanted by {', '.join(members)}"))
    return conflicts

def conflicting_items(conflicts, act=None):
    """ Item keys involved in shared conflicts (optionally at one act), used to highlight them """
    return {c.item for c in conflicts if c.kind == "shared" and (act is None or c.act == str(act))}
