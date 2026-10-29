""" Gear advice from the exact expected damage (instant, no simulation): what each item adds, the best items for a slot,
    and who gains most from an item several characters want """
from copy import deepcopy

from bg3.build import compile_build, equipment_at
from bg3.items import catalog
from computations.analytic import expected_damage_per_round

def damage(build, act, enemy, rounds_per_fight=None, items=None):
    return expected_damage_per_round(compile_build(build, act, items), enemy, rounds_per_fight)

def with_slot(build, act, slot, key):
    """ A copy of the build with a slot set at an act, '' empties it """
    changed = deepcopy(build)
    changed.equipment.setdefault(str(act), {})[slot] = key
    return changed

def item_gain(build, act, slot, key, enemy, rounds_per_fight=None, items=None, base=None):
    """ Expected damage per round gained by wearing an item in a slot at an act, compared to the slot being empty """
    empty = base if base is not None else damage(with_slot(build, act, slot, ""), act, enemy, rounds_per_fight, items)
    return damage(with_slot(build, act, slot, key), act, enemy, rounds_per_fight, items) - empty

def item_values(build, act, enemy, rounds_per_fight=None, items=None):
    """ (slot, item, damage gained) for everything worn at an act, most valuable first """
    items = items or catalog()
    full = damage(build, act, enemy, rounds_per_fight, items)
    values = []
    for slot, key in equipment_at(build, act).items():
        if key in items:
            values.append((slot, items[key], full - damage(with_slot(build, act, slot, ""), act, enemy, rounds_per_fight, items)))
    return sorted(values, key=lambda v: -v[2])

def slot_suggestions(build, act, slot, enemy, rounds_per_fight=None, items=None, party=(), top=10):
    """ The items that add the most damage in a slot at an act: (item, damage gained, other characters using it at that act).
        Only items found by that act are considered, items of unknown act only for Act 3 """
    items = items or catalog()
    base = damage(with_slot(build, act, slot, ""), act, enemy, rounds_per_fight, items)
    users = {}
    for other in party:
        if other.name != build.name:
            for key in equipment_at(other, act).values():
                users.setdefault(key, []).append(other.name)
    candidates = [i for i in items.values() if i.fits(slot) and (i.act or 3) <= int(act) and (i.effects or i.weapon)]
    ranked = [(i, item_gain(build, act, slot, i.key, enemy, rounds_per_fight, items, base)) for i in candidates]
    ranked = [(i, gain) for i, gain in ranked if gain > 0.005]
    ranked.sort(key=lambda r: -r[1])
    return [(i, gain, users.get(i.key, []) if i.unique else []) for i, gain in ranked[:top]]

def shared_item_gains(builds, conflict, enemy, rounds_per_fight=None, items=None):
    """ For a shared item conflict: {character: damage gained from the item} at the conflict's act """
    by_name = {b.name: b for b in builds}
    gains = {}
    for name in conflict.members:
        build = by_name[name]
        slot = next(s for s, k in equipment_at(build, conflict.act).items() if k == conflict.item)
        gains[name] = item_gain(build, conflict.act, slot, conflict.item, enemy, rounds_per_fight, items)
    return gains
