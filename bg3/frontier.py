""" A gear solver: for a build at an act, the gear and elixir combinations that trade damage against armour class, and the Pareto frontier
    of them (no other combination has both more damage and at least the AC, or more AC and at least the damage).

    The whole space is far too big to try (tens of options in each of eight slots, times the elixirs), so:
    1. Each slot's options are tried one at a time on the planned gear; only the ones not beaten on both damage and AC by another option
       of that slot are kept (equal results keep one, the worn item first), plus the best few for damage
    2. A beam search fills the slots in turn from those, keeping the frontier of what it has found (thinned evenly along it)
    Items that only pay off together (Broodmother's Revenge with a Ring of Regeneration) are tried as a pair. Weapons stay as planned
    (they decide how the build fights) """
from copy import deepcopy

from bg3.build import buffs_at, compile_build, equipment_at
from bg3.buffs import BUFFS
from bg3.defence import armour_class
from bg3.items import catalog
from bg3.optimize import candidates
from computations.analytic import expected_damage_vs_enemies

# Slot order: rings before the amulet, so a pair that sets both comes last
ORDER = ["armour", "gloves", "helmet", "cloak", "boots", "ring_1", "ring_2", "amulet", "elixir"]
# Items worth trying only together: (slot, item) pairs
COMBOS = [(("amulet", "bg3:broodmother_s_revenge"), ("ring_1", "bg3:ring_of_regeneration"))]
# Costs the damage and AC don't show, listed with each point that has the item
DRAWBACKS = {"bg3:risky_ring": "Disadvantage on saving throws", "elixir:elixir_of_bloodlust": "Its extra action needs a kill on your turn"}
KEEP_PER_SLOT = 6
TOP_DAMAGE = 3
BEAM = 10

def _elixirs(act):
    return [key for key, b in BUFFS.items() if b.exclusive and int(b.act or 1) <= int(act)]

def apply(build, act, choice):
    """ The build wearing a choice ({slot: item key, 'elixir': buff key or ''}) at the act """
    out = deepcopy(build)
    act = str(act)
    gear = {s: k for s, k in choice.items() if s != "elixir"}
    out.equipment[act] = {**out.equipment.get(act, {}), **gear}
    if "elixir" in choice:
        current = out.buffs.get(act, [])
        out.buffs[act] = [b for b in current if not (b in BUFFS and BUFFS[b].exclusive)] + ([choice["elixir"]] if choice["elixir"] else [])
    return out

def _pareto(points):
    """ The points no other point beats on both damage and AC (ties keep the first) """
    out = []
    for p in sorted(points, key=lambda p: (-p["damage"], -p["ac"])):
        if not any(q["ac"] >= p["ac"] and q["damage"] >= p["damage"] - 1e-9 for q in out):
            out.append(p)
    return out

def _thin(points, n):
    """ n points spread evenly along a frontier sorted by AC, its ends included """
    if len(points) <= n:
        return points
    points = sorted(points, key=lambda p: p["ac"])
    picks = {round(i * (len(points) - 1) / (n - 1)) for i in range(n)}
    return [points[i] for i in sorted(picks)]

def solve(build, act, enemy, rounds_per_fight, enemies=1, exclude=(), elixirs=True):
    """ {"current": point, "points": [every combination tried], "frontier": [the Pareto frontier]}. A point: damage per round, AC,
        the choice and its changes from the planned gear ([(slot, item key or '')]) """
    act = str(act)
    items = catalog()
    base = {s: equipment_at(build, act).get(s, "") for s in ORDER if s != "elixir"}
    worn_elixir = next((b.key for b in buffs_at(build, act) if b.exclusive), "")
    if elixirs:
        base["elixir"] = worn_elixir
    seen = {}

    def evaluate(choice):
        k = tuple(sorted(choice.items()))
        if k not in seen:
            b = apply(build, act, choice)
            c = compile_build(b, act)
            changes = [(s, v) for s, v in choice.items() if v != base.get(s, "")]
            seen[k] = {"choice": dict(choice), "changes": changes, "damage": expected_damage_vs_enemies(c, enemy, rounds_per_fight, enemies),
                       "ac": armour_class(b, act, c)[0], "drawbacks": [DRAWBACKS[v] for v in choice.values() if v in DRAWBACKS]}
        return seen[k]

    current = evaluate(base)
    # 1. Each slot's options on the planned gear
    options = {}
    for slot in [s for s in ORDER if s in base]:
        if slot == "elixir":
            keys = [""] + _elixirs(act)
        else:
            keys = [""] + [i.key for i in candidates(build, act, slot, items)
                           if not (i.unique and i.key in exclude)]
        tried = [{slot: k} for k in dict.fromkeys([base[slot], *keys])]
        tried += [dict(pair) for pair in COMBOS if pair[0][0] == slot and all(k not in exclude for _, k in pair)]
        other = {"ring_1": "ring_2", "ring_2": "ring_1"}.get(slot)
        tried = [t for t in tried if not (other and t.get(slot) and t[slot] == base.get(other))] # A ring isn't worn twice
        points = [(t, evaluate({**base, **t})) for t in tried]
        kept = {id(p) for p in _pareto([p for _, p in points])}
        kept |= {id(p) for _, p in sorted(points, key=lambda tp: -tp[1]["damage"])[:TOP_DAMAGE]}
        options[slot] = [t for t, p in points if id(p) in kept][:KEEP_PER_SLOT] or [{slot: base[slot]}]
    # 2. Beam search over the slots
    beam = [current]
    for slot in [s for s in ORDER if s in base]:
        grown = []
        for state in beam:
            for option in options[slot]:
                choice = {**state["choice"], **option}
                if choice.get("ring_1") and choice.get("ring_1") == choice.get("ring_2"):
                    continue
                grown.append(evaluate(choice))
        beam = _thin(_pareto(grown + beam), BEAM)
    # 3. Polish: the beam drops a state once something beats it, though a later slot might have suited it better (a helmet for +2 to hit
    # pushed out the plain gear that a ring granting advantage needed), so each frontier point tries every kept option again
    for _ in range(3):
        before = {id(p) for p in _pareto(list(seen.values()))}
        for state in _pareto(list(seen.values())):
            for slot in options:
                for option in [*options[slot], {slot: base[slot]}]:
                    choice = {**state["choice"], **option}
                    if not (choice.get("ring_1") and choice.get("ring_1") == choice.get("ring_2")):
                        evaluate(choice)
        if {id(p) for p in _pareto(list(seen.values()))} == before:
            break
    points = list(seen.values())
    return {"current": current, "points": points, "frontier": sorted(_pareto(points), key=lambda p: p["ac"])}
