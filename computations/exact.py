""" The exact distribution of damage per round, the curve the simulated histogram is a sample of.

    Every damage value's probability, from the same rules as the simulation (computations.numerical_simulation.damage_roll): hits, crits
    (dice doubled, extra crit dice), misses and half damage on a saved spell, damage advantage (Savage Attacker), rerolls (Great Weapon
    Fighting), resistances rounded down per attack and per typed rider, damage reduction, once per turn damage on the first hit of the round,
    and with rounds_per_fight, limited attacks, their fallbacks, first round advantage or crits and limited once per turn damage spread over
    fights like the simulation does. Distributions are numpy arrays where index i is the probability of exactly i damage """
from dataclasses import asdict

import numpy as np

from computations.analytic import _uses_realizations, adv_dis_pmf, dice_sum_pmf, hit_and_crit_chance
from computations.models import calculate_attack_and_damage_context
from computations.numerical_simulation import has_fight_limits

class Dist:
    """ A distribution over integers: probs[i] is the probability of offset + i """
    def __init__(self, probs, offset=0):
        self.probs, self.offset = np.asarray(probs, dtype=float), int(offset)

    @staticmethod
    def point(value=0):
        return Dist([1.0], value)

    def __add__(self, other):
        if isinstance(other, (int, np.integer)):
            return Dist(self.probs, self.offset + int(other))
        return Dist(np.convolve(self.probs, other.probs), self.offset + other.offset)

    def scaled(self, weight):
        return Dist(self.probs * weight, self.offset)

    def mapped(self, function):
        """ The distribution of function(value), for integer valued functions like rounding down a resisted total """
        values = self.offset + np.arange(len(self.probs))
        mapped = np.array([function(int(v)) for v in values], dtype=np.int64)
        low = mapped.min()
        out = np.zeros(mapped.max() - low + 1)
        np.add.at(out, mapped - low, self.probs)
        return Dist(out, low)

    def mix(self, other):
        """ Sum of two partial distributions (weights already applied) """
        low = min(self.offset, other.offset)
        high = max(self.offset + len(self.probs), other.offset + len(other.probs))
        out = np.zeros(high - low)
        out[self.offset - low:self.offset - low + len(self.probs)] += self.probs
        out[other.offset - low:other.offset - low + len(other.probs)] += other.probs
        return Dist(out, low)

    def total(self):
        return float(self.probs.sum())

    def as_array(self):
        """ Probabilities indexed by damage from 0 (negative values can't happen after clipping) """
        clipped = self.mapped(lambda v: max(v, 0))
        return np.concatenate([np.zeros(clipped.offset), clipped.probs])

    def mean(self):
        return float(np.dot(self.offset + np.arange(len(self.probs)), self.probs) / self.total())

ZERO = Dist.point(0)

def dice(num_die, die_size, reroll_on=0):
    if not num_die:
        return ZERO
    return Dist(dice_sum_pmf(num_die, die_size, reroll_on))

def extra_dice(d, num_die, die_size):
    """ Rider or once per turn dice: rerolled like the weapon's, and with BG3 Savage Attacker the higher of two rolls per die """
    if not num_die:
        return ZERO
    return Dist(dice_sum_pmf(num_die, die_size, d["reroll_on"], advantage=bool(d.get("rider_advantage"))))

def damage_dice(d):
    """ The attack's damage dice with damage advantage (whole set or per die, BG3 Savage Attacker) and rerolls """
    if not d["num_die"]:
        return ZERO
    if d.get("per_die_advantage"):
        return Dist(dice_sum_pmf(d["num_die"], d["die_size"], d["reroll_on"], d["advantage"], d["disadvantage"]))
    return Dist(adv_dis_pmf(dice_sum_pmf(d["num_die"], d["die_size"], d["reroll_on"]), d["advantage"], d["disadvantage"]))

def _floor_times(multiplier):
    return lambda v: int(np.floor(v * multiplier))

def outcome_damage(d, outcome, pools=()):
    """ Damage of one attack given its outcome ('hit', 'crit' or 'miss'), with the once per turn pools that go on it """
    base = damage_dice(d) + d["modifier"]
    pools = [] if outcome == "miss" else list(pools)
    if outcome == "miss":
        main = dice(d["miss_num_die"], d["miss_damage_die"]) + d["miss_damage_modifier"]
        if d["save_success_multiplier"]:
            main = main + base.mapped(_floor_times(d["save_success_multiplier"]))
    else:
        main = base
        if outcome == "crit":
            main = main + damage_dice(d) + dice(d["crit_num_die"], d["crit_damage_die"], d["reroll_on"]) + d["crit_damage_modifier"]
        for pool in pools:
            if pool["multiplier"] is None: # The attack's own damage type
                main = main + extra_dice(d, pool["num_die"], pool["die_size"]) + pool["modifier"]
                if outcome == "crit":
                    main = main + extra_dice(d, pool["num_die"], pool["die_size"])
    if d["modifier"] < 0 or d["miss_damage_modifier"] < 0 or d["crit_damage_modifier"] < 0 or any(pool["modifier"] < 0 for pool in pools):
        main = main.mapped(lambda v: max(v, 0))
    if d["damage_multiplier"] != 1:
        main = main.mapped(_floor_times(d["damage_multiplier"]))
    for pool in pools:
        if pool["multiplier"] is not None: # Its own damage type: added after the attack's multiplier
            extra = extra_dice(d, pool["num_die"], pool["die_size"]) + pool["modifier"]
            if outcome == "crit":
                extra = extra + extra_dice(d, pool["num_die"], pool["die_size"])
            main = main + extra.mapped(lambda v, mult=pool["multiplier"]: int(np.floor(max(v, 0) * mult)))
    if outcome != "miss":
        for n, s, m, mult in zip(d.get("rider_num_die") or [], d.get("rider_die_size") or [], d.get("rider_modifier") or [],
                                 d.get("rider_multiplier") or []):
            rider = (extra_dice(d, n, s) + m).mapped(lambda v: max(v, 0))
            if outcome == "crit":
                rider = rider + extra_dice(d, n, s)
            if mult != 1:
                rider = rider.mapped(_floor_times(mult))
            main = main + rider
    if d["damage_reduction"]:
        main = main.mapped(lambda v, dr=d["damage_reduction"]: max(v - dr, 0))
    return main

def _round(contexts, active, available):
    """ (damage distribution of one round, {pool id: chance it was used}) for the attacks made this round.
        contexts: [(attack dict, damage dict, auto crit)], active: which are made, available: ids of the once per turn pools that can be
        used this round. The state is the set of pools already used this round, each with its partial damage distribution """
    states = {frozenset(): ZERO}
    for (a, d, auto_crit), made in zip(contexts, active):
        if not made:
            continue
        p_hit, p_crit = hit_and_crit_chance(**a)
        if auto_crit:
            p_crit = p_hit
        outcomes = {o: p for o, p in {"crit": p_crit, "hit": p_hit - p_crit, "miss": 1 - p_hit}.items() if p > 0}
        pools = [pool for pool in d.get("once_pools") or () if pool["id"] in available]
        cache, new_states = {}, {}
        for spent, dist in states.items():
            for o, p in outcomes.items():
                triggers = () if o == "miss" else tuple(pool["id"] for pool in pools if pool["id"] not in spent and (o == "crit" or not pool["crit_only"]))
                if (o, triggers) not in cache:
                    cache[o, triggers] = outcome_damage(d, o, [pool for pool in pools if pool["id"] in triggers]).scaled(p)
                part = dist + cache[o, triggers]
                key = spent | frozenset(triggers)
                new_states[key] = part if key not in new_states else new_states[key].mix(part)
        states = new_states
    total, used = None, {pool_id: 0.0 for pool_id in available}
    for spent, dist in states.items():
        total = dist if total is None else total.mix(dist)
        for pool_id in spent:
            used[pool_id] += dist.total()
    return total, used

def damage_per_round(character, enemy, rounds_per_fight=None):
    """ The exact distribution of a character's damage per round against an enemy, as an array indexed by damage.
        Exact with any number of once per turn pools when at most one of them is limited per fight; with several limited pools their
        remaining uses are treated as independent of each other """
    attack_contexts, damage_contexts = calculate_attack_and_damage_context(character, enemy)
    attacks = [asdict(a) for a in attack_contexts]
    damages = [asdict(d) for d in damage_contexts]
    limited = bool(rounds_per_fight) and has_fight_limits(damages)
    plain_contexts = [(a, d, False) for a, d in zip(attacks, damages)]
    pool_uses = {pool["id"]: pool["uses"] for d in damages for pool in d.get("once_pools") or ()}
    if not limited:
        # Every round the same: limited attacks every round, their fallbacks never
        dist, _ = _round(plain_contexts, [d.get("fallback_index", -1) < 0 for d in damages], set(pool_uses))
        return dist.as_array()
    first_contexts = [({**a, "advantage": True} if d.get("first_round_advantage") else a, d, bool(d.get("first_round_auto_crit")))
                      for a, d in zip(attacks, damages)]
    pool_ids = sorted(pool_uses)
    averages = [d.get("uses_per_fight") or 0 for d in damages] + [pool_uses[p] for p in pool_ids]
    total = None
    for probability, uses in _uses_realizations(averages):
        attack_uses = uses[:len(damages)]
        once_uses = dict(zip(pool_ids, uses[len(damages):]))
        limited_ids = [p for p in pool_ids if once_uses[p] is not None]
        unlimited = {p for p in pool_ids if once_uses[p] is None}
        used = {p: np.array([1.0]) for p in limited_ids} # Distribution of each limited pool's uses spent so far in the fight
        for r in range(rounds_per_fight):
            active = []
            for u, d in zip(attack_uses, damages):
                if d.get("fallback_index", -1) >= 0:
                    replaced = attack_uses[d["fallback_index"]]
                    active.append(replaced is not None and r >= replaced and (u is None or r < replaced + u))
                else:
                    active.append(u is None or r < u)
            contexts = first_contexts if r == 0 else plain_contexts
            p_available = {p: float(used[p][:once_uses[p]].sum()) for p in limited_ids}
            spent_chance = {p: 0.0 for p in limited_ids}
            # Every combination of limited pools that still have a use this round
            combos = [(1.0, frozenset())]
            for p in limited_ids:
                combos = [(w * q, have | extra) for w, have in combos for q, extra in ((p_available[p], frozenset([p])), (1 - p_available[p], frozenset())) if q > 0]
            for weight, have in combos:
                dist, chance = _round(contexts, active, unlimited | have)
                part = dist.scaled(weight * probability / rounds_per_fight)
                total = part if total is None else total.mix(part)
                for p in have:
                    spent_chance[p] += weight * chance[p] / p_available[p]
            for p in limited_ids:
                # Only rounds where it was available can spend a use; spent_chance is the chance given that it was
                can = np.arange(len(used[p])) < once_uses[p]
                step = np.where(can, used[p] * spent_chance[p], 0)
                used[p] = np.concatenate([used[p] - step, [0]]) + np.concatenate([[0], step])
    return total.as_array()

def binned(probs, low, width, bins):
    """ Probability of each histogram bin [low + width * i, low + width * (i + 1)) """
    out = np.zeros(bins)
    values = np.arange(len(probs))
    index = (values - low) // width
    keep = (index >= 0) & (index < bins)
    np.add.at(out, index[keep], probs[keep])
    return out
