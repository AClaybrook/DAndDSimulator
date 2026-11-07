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
from computations.numerical_simulation import has_fight_limits, has_once_damage

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

def damage_dice(d):
    """ The attack's damage dice with damage advantage (whole set or per die, BG3 Savage Attacker) and rerolls """
    if not d["num_die"]:
        return ZERO
    if d.get("per_die_advantage"):
        return Dist(dice_sum_pmf(d["num_die"], d["die_size"], d["reroll_on"], d["advantage"], d["disadvantage"]))
    return Dist(adv_dis_pmf(dice_sum_pmf(d["num_die"], d["die_size"], d["reroll_on"]), d["advantage"], d["disadvantage"]))

def _floor_times(multiplier):
    return lambda v: int(np.floor(v * multiplier))

def outcome_damage(d, outcome, once=False):
    """ Damage of one attack given its outcome ('hit', 'crit' or 'miss'), with once per turn damage when once """
    base = damage_dice(d) + d["modifier"]
    if outcome == "miss":
        main = dice(d["miss_num_die"], d["miss_damage_die"]) + d["miss_damage_modifier"]
        if d["save_success_multiplier"]:
            main = main + base.mapped(_floor_times(d["save_success_multiplier"]))
    else:
        main = base
        if once:
            main = main + dice(d["once_num_die"], d["once_die_size"], d["reroll_on"]) + d["once_modifier"]
        if outcome == "crit":
            main = main + damage_dice(d) + dice(d["crit_num_die"], d["crit_damage_die"], d["reroll_on"]) + d["crit_damage_modifier"]
            if once:
                main = main + dice(d["once_num_die"], d["once_die_size"], d["reroll_on"])
    if d["modifier"] < 0 or d["miss_damage_modifier"] < 0 or d["crit_damage_modifier"] < 0 or d["once_modifier"] < 0:
        main = main.mapped(lambda v: max(v, 0))
    if d["damage_multiplier"] != 1:
        main = main.mapped(_floor_times(d["damage_multiplier"]))
    if outcome != "miss":
        for n, s, m, mult in zip(d.get("rider_num_die") or [], d.get("rider_die_size") or [], d.get("rider_modifier") or [],
                                 d.get("rider_multiplier") or []):
            rider = (dice(n, s) + m).mapped(lambda v: max(v, 0))
            if outcome == "crit":
                rider = rider + dice(n, s)
            if mult != 1:
                rider = rider.mapped(_floor_times(mult))
            main = main + rider
    if d["damage_reduction"]:
        main = main.mapped(lambda v, dr=d["damage_reduction"]: max(v - dr, 0))
    return main

def _round(contexts, active, once_available):
    """ (damage distribution of one round, chance once per turn damage triggered) for the attacks made this round.
        contexts: [(attack dict, damage dict, auto crit)], active: which are made """
    ready = ZERO.scaled(1.0 if once_available else 0.0) # Once per turn damage not used yet this round
    spent = ZERO.scaled(0.0 if once_available else 1.0) # Already used, or not available
    for (a, d, auto_crit), made in zip(contexts, active):
        if not made:
            continue
        p_hit, p_crit = hit_and_crit_chance(**a)
        if auto_crit:
            p_crit = p_hit
        outcomes = {"crit": p_crit, "hit": p_hit - p_crit, "miss": 1 - p_hit}
        plain = {o: outcome_damage(d, o) for o, p in outcomes.items() if p > 0}
        attack_plain = None
        for o, p in outcomes.items():
            if p > 0:
                part = plain[o].scaled(p)
                attack_plain = part if attack_plain is None else attack_plain.mix(part)
        if not has_once_damage(d):
            ready, spent = ready + attack_plain, spent + attack_plain
            continue
        triggers = ("crit",) if d.get("once_crit_only") else ("crit", "hit")
        new_ready, new_spent = None, spent + attack_plain
        for o, p in outcomes.items():
            if p <= 0:
                continue
            if o in triggers:
                part = ready + outcome_damage(d, o, once=True).scaled(p)
                new_spent = new_spent.mix(part)
            else:
                part = ready + plain[o].scaled(p)
                new_ready = part if new_ready is None else new_ready.mix(part)
        ready = new_ready if new_ready is not None else ZERO.scaled(0.0)
        spent = new_spent
    triggered = 1.0 - ready.total() if once_available else 0.0
    return ready.mix(spent), triggered

def damage_per_round(character, enemy, rounds_per_fight=None):
    """ The exact distribution of a character's damage per round against an enemy, as an array indexed by damage """
    attack_contexts, damage_contexts = calculate_attack_and_damage_context(character, enemy)
    attacks = [asdict(a) for a in attack_contexts]
    damages = [asdict(d) for d in damage_contexts]
    limited = bool(rounds_per_fight) and has_fight_limits(damages)
    plain_contexts = [(a, d, False) for a, d in zip(attacks, damages)]
    if not limited:
        # Every round the same: limited attacks every round, their fallbacks never
        dist, _ = _round(plain_contexts, [d.get("fallback_index", -1) < 0 for d in damages], True)
        return dist.as_array()
    first_contexts = [({**a, "advantage": True} if d.get("first_round_advantage") else a, d, bool(d.get("first_round_auto_crit")))
                      for a, d in zip(attacks, damages)]
    once_average = next((d.get("once_uses_per_fight") for d in damages if has_once_damage(d)), 0)
    averages = [d.get("uses_per_fight") or 0 for d in damages] + [once_average]
    total = None
    for probability, uses in _uses_realizations(averages):
        attack_uses, once_uses = uses[:-1], uses[-1]
        used = np.array([1.0]) # Distribution of once per turn uses spent so far in the fight
        for r in range(rounds_per_fight):
            active = []
            for u, d in zip(attack_uses, damages):
                if d.get("fallback_index", -1) >= 0:
                    replaced = attack_uses[d["fallback_index"]]
                    active.append(replaced is not None and r >= replaced)
                else:
                    active.append(u is None or r < u)
            contexts = first_contexts if r == 0 else plain_contexts
            p_available = 1.0 if once_uses is None else float(used[:once_uses].sum())
            with_once, q = _round(contexts, active, True)
            without, _ = _round(contexts, active, False)
            round_dist = with_once.scaled(p_available).mix(without.scaled(1 - p_available)) if p_available < 1 else with_once
            part = round_dist.scaled(probability / rounds_per_fight)
            total = part if total is None else total.mix(part)
            if once_uses is not None:
                # Only rounds where it was available can spend a use
                can = np.arange(len(used)) < once_uses
                step = np.where(can, used * q, 0)
                used = np.concatenate([used - step, [0]]) + np.concatenate([[0], step])
    return total.as_array()

def binned(probs, low, width, bins):
    """ Probability of each histogram bin [low + width * i, low + width * (i + 1)) """
    out = np.zeros(bins)
    values = np.arange(len(probs))
    index = (values - low) // width
    keep = (index >= 0) & (index < bins)
    np.add.at(out, index[keep], probs[keep])
    return out
