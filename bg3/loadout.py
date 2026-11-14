""" Gear for a whole party: the best gear a character can wear at an act (best in slot from everything found by then), and settling
    the items two characters both want.

    "Best" is by search, not a fixed list (bg3.optimize): one slot at a time from the items found by that act, so it follows the build,
    its buffs and the enemy. Items the rest of the party wears can be left alone, so filling one character doesn't create conflicts """
from copy import deepcopy

from bg3.analysis import item_gain, slot_suggestions, with_slot
from bg3.build import ACT_KEYS, compile_build, equipment_at
from bg3.defence import armour_class
from bg3.items import SLOT_LABELS, catalog
from bg3.optimize import MIN_GAIN, ac_objective, optimise
from bg3.party import party_conflicts
from bg3.score import score
from computations.analytic import expected_damage_vs_enemies

GOALS = {"damage": "Most damage", "ac": "Highest armour class", "score": "Best overall score"}

def _objective(goal, act, enemy, rounds, enemies, attack_bonus):
    def damage(build):
        return expected_damage_vs_enemies(compile_build(build, act), enemy, rounds, enemies)
    if goal == "ac":
        return ac_objective(act, damage)
    if goal == "score":
        return lambda build: score(build, act, enemy, rounds, attack_bonus).total
    return damage

def worn_by_others(builds, index, act):
    """ Unique items the rest of the party wears at an act """
    items = catalog()
    return {key for ii, other in enumerate(builds) if ii != index for key in equipment_at(other, act).values() if key in items and items[key].unique}

def best_gear(builds, index, acts, goal, enemy, rounds=3, enemies=1, attack_bonus=6, weapons=True, skip_taken=True, enemy_at=None,
              keep_uncounted=True):
    """ (gear by act, changes, kept) for one party member: the gear that does best by the goal in each of the acts, each act building on
        the one before. gear: {act: {slot: item key}}, only the slots that change. changes: [{act, slot, before, after, gain}] with item
        names. keep_uncounted: a worn item with effects the damage doesn't count is harder to swap out (bg3.optimize.optimise), since
        the numbers undersell it; kept: [{act, slot, item, preferred, gain}] for the ones the numbers alone would have replaced.
        enemy_at(act): the enemy at an act when it differs (party synergies) """
    items = catalog()
    build = deepcopy(builds[index])
    gear_by_act, changes, kept = {}, [], []
    for act in [a for a in ACT_KEYS if a in acts]:
        party = [build if ii == index else b for ii, b in enumerate(builds)]
        exclude = worn_by_others(party, index, act) if skip_taken else set()
        before = equipment_at(build, act)
        # For damage, a swap may not cost armour class (no trading armour for clothes with a small bonus), and an item the build
        # already wears is only replaced for a real gain
        guard = (lambda b, act=act: armour_class(b, act)[0]) if goal == "damage" else None
        objective = _objective(goal, act, enemy_at(act) if enemy_at else enemy, rounds, enemies, attack_bonus)
        held = {} if keep_uncounted else None
        found = optimise(build, act, objective, items, exclude=exclude, weapons=weapons,
                         min_gain=MIN_GAIN, guard=guard, kept=held)
        kept += [{"act": act, "slot": SLOT_LABELS.get(slot, slot), "item": items[key].name, "preferred": items[other].name, "gain": round(gain_, 1)}
                 for slot, (key, other, gain_) in (held or {}).items()]
        changed = {slot: key for slot, key in found.items() if key != before.get(slot, "")}
        if changed:
            gear_by_act[act] = changed
            build.equipment[act] = {**build.equipment.get(act, {}), **changed}
        # What each swap adds: the goal's value with everything, less the value with that one slot put back
        total = objective(build) if changed else 0
        def gain(slot, act=act, before=before, total=total, objective=objective):
            back = deepcopy(build)
            back.equipment[act] = {**back.equipment[act], slot: before.get(slot, "")}
            return round(total - objective(back), 1)
        changes += [{"act": act, "slot": SLOT_LABELS.get(slot, slot), "before": items[before[slot]].name if before.get(slot) in items else "",
                     "after": items[key].name if key in items else "", "gain": gain(slot)} for slot, key in changed.items()]
    return gear_by_act, changes, kept

def resolve_conflicts(builds, enemy, rounds=3):
    """ (party without shared item conflicts, steps). For every unique item two or more characters wear at an act, the one who gains
        the most damage from it keeps it; each of the others gets the best item for that slot that nobody wears, or an empty slot.
        Acts are settled in order, since later acts inherit the gear. steps: [{act, item, keeper, member, slot, slotKey, replacement,
        replacementKey, cost, alternatives: [{key, item, gain}]}], cost being the damage per round the swap gives up """
    items = catalog()
    party = [deepcopy(b) for b in builds]
    steps, vacated = [], [] # vacated: (member index, slot, item, keeper) slots a swap left empty, filled once a later act has something

    def options_for(build, act, slot, contested):
        own = set(equipment_at(build, act).values())
        taken = {key for other in party for key in equipment_at(other, act).values()}
        return [(item, g) for item, g, _ in slot_suggestions(build, act, slot, enemy, rounds, items, party=party, top=40)
                if item.key != contested and item.key not in own and not (item.unique and item.key in taken)]

    def swap(act, ii, slot, contested, keeper, gain):
        build = party[ii]
        options = options_for(build, act, slot, contested)
        best = options[0] if options else None
        build.equipment.setdefault(act, {})[slot] = best[0].key if best else ""
        steps.append({"act": act, "item": items[contested].name, "keeper": party[keeper].name, "member": build.name,
                      "slot": SLOT_LABELS.get(slot, slot), "slotKey": slot, "replacement": best[0].name if best else "",
                      "replacementKey": best[0].key if best else "", "cost": round(gain - (best[1] if best else 0.0), 2),
                      "alternatives": [{"key": item.key, "item": item.name, "gain": round(g, 2)} for item, g in options[:4]]})
        return best is not None

    for act in ACT_KEYS:
        # A slot an earlier act's swap emptied gets the best item this act has for it
        for entry in list(vacated):
            ii, slot, contested, keeper = entry
            if not equipment_at(party[ii], act).get(slot) and options_for(party[ii], act, slot, contested):
                swap(act, ii, slot, contested, keeper, item_gain(with_slot(party[ii], act, slot, ""), act, slot, contested, enemy, rounds, items))
                vacated.remove(entry)
        for _ in range(40): # Each pass settles one item; the bound only guards against a loop
            shared = [c for c in party_conflicts(party, items, acts=[act]) if c.kind == "shared"]
            if not shared:
                break
            conflict = shared[0]
            holders = {}
            for ii, build in enumerate(party):
                slot = next((s for s, k in equipment_at(build, act).items() if k == conflict.item), None)
                if slot:
                    holders[ii] = (slot, item_gain(build, act, slot, conflict.item, enemy, rounds, items))
            keeper = max(holders, key=lambda ii: holders[ii][1])
            for ii, (slot, gain) in holders.items():
                if ii != keeper and not swap(act, ii, slot, conflict.item, keeper, gain):
                    vacated.append((ii, slot, conflict.item, keeper))
    return party, steps
