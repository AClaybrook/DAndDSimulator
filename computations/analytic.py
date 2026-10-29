""" Analytic (exact) computations, used to validate the numerical simulation and to explain where damage comes from """
from dataclasses import asdict, replace
import numpy as np
import pandas as pd

from computations.models import calculate_attack_and_damage_context
from computations.numerical_simulation import has_fight_limits

# Analytic Values
def expected_value(die_size):
    """ Returns the expected value of a die roll, which is a uniform distribution"""
    return (1 + die_size)/2

def avg_damage(num_die, die_size):
    """Average damage of multiple dice rolls"""
    ev = expected_value(die_size)
    return num_die * ev

def die_pmf(die_size, reroll_on=0):
    """ Probability mass function of a single die (index 0 is a roll of 1), rerolling once on reroll_on or lower """
    pmf = np.full(die_size, 1/die_size)
    if reroll_on > 0:
        r = min(reroll_on, die_size)
        pmf = np.where(np.arange(1, die_size+1) <= r, 0, 1/die_size) + r/die_size * (1/die_size)
    return pmf

def adv_dis_pmf(pmf, advantage=False, disadvantage=False):
    """ Probability mass function of the higher (advantage) or lower (disadvantage) of two rolls """
    if advantage == disadvantage:
        return pmf
    cdf = np.cumsum(pmf)
    if advantage:
        new_cdf = cdf**2
    else:
        new_cdf = 1 - (1 - cdf)**2
    return np.diff(np.concatenate([[0], new_cdf]))

def dice_sum_pmf(num_die, die_size, reroll_on=0):
    """ Probability mass function of a sum of dice, index i is a total of i """
    pmf = np.array([1.0])
    for nd, ds in zip(num_die, die_size):
        single = np.concatenate([[0], die_pmf(ds, reroll_on)])
        for _ in range(nd):
            pmf = np.convolve(pmf, single)
    return pmf

def expected_dice(num_die, die_size, reroll_on=0, advantage=False, disadvantage=False):
    """ Expected total of a set of dice, optionally rolling the whole set twice and keeping the higher/lower total """
    pmf = adv_dis_pmf(dice_sum_pmf(num_die, die_size, reroll_on), advantage, disadvantage)
    return float(np.dot(np.arange(len(pmf)), pmf))

def hit_and_crit_chance(num_die=(), die_size=(), modifier=0, difficulty_class=15, crit_on=20, advantage=False, disadvantage=False,
                        reroll_on=0, saving_throw=False, always_hit=False, always_crit=False, **_):
    """ Exact probability to hit (including crits) and to crit for an attack roll or a saving throw (hit = failed save) """
    if always_crit:
        return 1.0, 1.0
    if always_hit:
        return 1.0, 0.0
    d20 = adv_dis_pmf(die_pmf(20, reroll_on), advantage, disadvantage)
    bonus = dice_sum_pmf(num_die, die_size)
    p_hit = 0.0
    p_crit = 0.0
    for face, p_face in enumerate(d20, start=1):
        # Probability the bonus dice push the roll over (or under for a save) the difficulty class
        needed = difficulty_class - face - modifier
        if saving_throw:
            p_success = bonus[:max(needed, 0)].sum() if needed > 0 else 0.0
            p_hit += p_face * p_success
            continue
        if face == 1:
            continue
        if face >= crit_on:
            p_hit += p_face
            p_crit += p_face
            continue
        p_hit += p_face * bonus[max(needed, 0):].sum()
    return float(p_hit), float(p_crit)

def expected_attack_damage(attack_context, damage_context, p_first_hit=None, auto_crit=False):
    """ Expected damage of a single attack (before damage reduction, resistances are applied linearly)
        p_first_hit is the probability that this attack is the first to hit this round, used for once per turn damage.
        With auto_crit every hit is a crit (i.e. Assassinate against a surprised enemy) """
    a = attack_context if isinstance(attack_context, dict) else asdict(attack_context)
    d = damage_context if isinstance(damage_context, dict) else asdict(damage_context)
    p_hit, p_crit = hit_and_crit_chance(**a)
    if auto_crit:
        p_crit = p_hit
    p_miss = 1 - p_hit

    base = expected_dice(d["num_die"], d["die_size"], d["reroll_on"], d["advantage"], d["disadvantage"]) + d["modifier"]
    crit_extra = expected_dice(d["num_die"], d["die_size"], d["reroll_on"], d["advantage"], d["disadvantage"]) \
        + expected_dice(d["crit_num_die"], d["crit_damage_die"], d["reroll_on"]) + d["crit_damage_modifier"]
    miss = expected_dice(d["miss_num_die"], d["miss_damage_die"]) + d["miss_damage_modifier"] + d["save_success_multiplier"] * base

    expected = p_hit * base + p_crit * crit_extra + p_miss * miss
    p_trigger = p_crit if d.get("once_crit_only") else p_hit
    if p_first_hit is not None and d.get("once_per_turn_eligible") and p_trigger > 0:
        once = expected_dice(d["once_num_die"], d["once_die_size"], d["reroll_on"])
        # Given that this is the first trigger, the chance it was a crit is p_crit/p_trigger
        expected += p_first_hit * (once + d["once_modifier"] + p_crit / p_trigger * once)
    expected *= d["damage_multiplier"]
    # Extra damage of other types on a hit, dice doubled on a crit
    for n, s, m, mult in zip(d.get("rider_num_die") or [], d.get("rider_die_size") or [], d.get("rider_modifier") or [], d.get("rider_multiplier") or []):
        dice = expected_dice(n, s)
        expected += (p_hit * (dice + m) + p_crit * dice) * mult
    return expected

def _uses_realizations(averages):
    """ Every combination of integer uses for average uses per fight (None = unlimited), with its probability.
        i.e. an average of 1.5 is 1 or 2 uses with equal chance, like the simulation """
    combos = [(1.0, [])]
    for average in averages:
        if not average:
            options = [(1.0, None)]
        else:
            base = int(np.floor(average))
            options = [(1 - (average - base), base), (average - base, base + 1)]
        combos = [(p * q, uses + [u]) for p, uses in combos for q, u in options if q > 0]
    return combos

def expected_by_attack(character, enemy, rounds_per_fight=None):
    """ Exact expected damage of each attack, averaged per round.
        With rounds_per_fight, attacks and once per turn damage limited per fight are averaged over fights of that many rounds,
        otherwise resources are unlimited (every round is the same) """
    attack_contexts, damage_contexts = calculate_attack_and_damage_context(character, enemy)

    def profile(a, d, first_round):
        """ Expected damage without once per turn damage, chance to trigger it and its expected value when it does """
        a = asdict(a)
        if first_round and d.first_round_advantage:
            a["advantage"] = True
        auto_crit = first_round and d.first_round_auto_crit
        p_hit, p_crit = hit_and_crit_chance(**a)
        p_crit = p_hit if auto_crit else p_crit
        p = (p_crit if d.once_crit_only else p_hit) if d.once_per_turn_eligible and (d.once_num_die or d.once_modifier) else 0.0
        once = expected_dice(d.once_num_die, d.once_die_size, d.reroll_on)
        # Given that this attack used the once per turn damage, the chance it was a crit is p_crit/p
        once_value = (once + d.once_modifier + p_crit / p * once) * d.damage_multiplier if p > 0 else 0.0
        return expected_attack_damage(a, d, auto_crit=auto_crit), p, once_value

    later_rounds = [profile(a, d, False) for a, d in zip(attack_contexts, damage_contexts)]
    has_once = any(p for _, p, _ in later_rounds)
    limited = bool(rounds_per_fight) and has_fight_limits([asdict(d) for d in damage_contexts])
    first_round = [profile(a, d, True) for a, d in zip(attack_contexts, damage_contexts)] if limited else later_rounds
    num_rounds = rounds_per_fight if limited else 1
    averages = [d.uses_per_fight if limited else 0 for d in damage_contexts] + [damage_contexts[0].once_uses_per_fight if limited and has_once else 0]

    totals = np.zeros(len(attack_contexts))
    for probability, uses in _uses_realizations(averages):
        attack_uses, once_uses = uses[:-1], uses[-1]
        triggered_rounds = np.array([1.0]) # Distribution of the number of rounds once per turn damage was used so far
        for r in range(num_rounds):
            p_available = 1.0 if once_uses is None else triggered_rounds[:once_uses].sum()
            p_none_yet = 1.0
            for k, (u, d) in enumerate(zip(attack_uses, damage_contexts)):
                if d.fallback_index >= 0:
                    # Made once the limited attack it replaces is used up, never if that attack isn't limited
                    replaced_uses = attack_uses[d.fallback_index]
                    if replaced_uses is None or r < replaced_uses:
                        continue
                elif u is not None and r >= u:
                    continue # Used up
                base, p_trigger, once_value = (first_round if r == 0 else later_rounds)[k]
                totals[k] += probability * base
                if p_trigger:
                    totals[k] += probability * p_available * p_none_yet * p_trigger * once_value
                    p_none_yet *= 1 - p_trigger
            if once_uses is not None:
                q = 1 - p_none_yet
                triggered_rounds = np.concatenate([triggered_rounds * (1 - q), [0]]) + np.concatenate([[0], triggered_rounds * q])
    return totals / num_rounds

def attack_breakdown(character, enemy, rounds_per_fight=None):
    """ Per attack table of to hit chance, crit chance and expected damage for a character against an enemy """
    attack_contexts, damage_contexts = calculate_attack_and_damage_context(character, enemy)
    expected = expected_by_attack(character, enemy, rounds_per_fight)
    any_limited = any(a.uses_per_fight or a.fallback_for for a in character.attacks)
    rows = []
    for attack, a, d, e in zip(character.attacks, attack_contexts, damage_contexts, expected):
        p_hit, p_crit = hit_and_crit_chance(**asdict(a))
        if a.saving_throw:
            to_hit = f"DC {a.difficulty_class} vs {a.modifier:+d}"
        else:
            bonus_dice = " + ".join(f"{n}d{s}" for n, s in zip(a.num_die, a.die_size))
            to_hit = f"{a.modifier:+d}" + (f" + {bonus_dice}" if bonus_dice else "")
        dice = " + ".join(f"{n}d{s}" for n, s in zip(d.num_die, d.die_size))
        damage = dice + (f" {d.modifier:+d}" if d.modifier else "")
        row = {
            "Attack": attack.name,
            "To Hit": to_hit,
            "Damage": damage or "0",
            "Hit %": round(100 * p_hit, 1),
            "Crit %": round(100 * p_crit, 1),
        }
        if any_limited:
            row["Uses/Fight"] = f"after {attack.fallback_for}" if attack.fallback_for else f"{attack.uses_per_fight:g}" if attack.uses_per_fight else "all"
        row["Expected"] = round(float(e), 2)
        rows.append(row)
    columns = ["Attack", "To Hit", "Damage", "Hit %", "Crit %"] + (["Uses/Fight"] if any_limited else []) + ["Expected"]
    return pd.DataFrame(rows, columns=columns)

def attacks_per_round(character, rounds_per_fight=None):
    """ Average number of attacks made per round, attacks limited per fight are only made in some rounds """
    def made(uses):
        if not uses or not rounds_per_fight:
            return 1.0
        base = int(np.floor(uses))
        frac = uses - base
        return ((1 - frac) * min(base, rounds_per_fight) + frac * min(base + 1, rounds_per_fight)) / rounds_per_fight
    limited_uses = {a.name: a.uses_per_fight for a in reversed(character.attacks)} # First attack with a name wins
    total = 0.0
    for a in character.attacks:
        if a.fallback_for and a.fallback_for != a.name and a.fallback_for in limited_uses:
            # Made in the rounds after the attack it replaces is used up
            replaced = limited_uses[a.fallback_for]
            total += 1.0 - made(replaced) if replaced and rounds_per_fight else 0.0
        else:
            total += made(a.uses_per_fight)
    return float(total)

def expected_damage_per_round(character, enemy, rounds_per_fight=None):
    """ Expected (mean) damage per round, ignoring damage reduction and rounding """
    return float(expected_by_attack(character, enemy, rounds_per_fight).sum())

POWER_ATTACK_FEATS = {"GWM": ("Great Weapon Master", lambda a: a.type == "weapon (melee)" and a.heavy),
                      "sharpshooter": ("Sharpshooter", lambda a: a.type == "weapon (ranged)")}

def power_attack_insights(character, enemy, armor_classes, rounds_per_fight=None):
    """ For each power attack feat (-5 to hit, +10 damage) a character has turned on, finds the armor classes where it is worth using.
        Uses the exact expected damage, so it is instant """
    insights = []
    for flag, (label, applies) in POWER_ATTACK_FEATS.items():
        if not getattr(character, flag) or not any(applies(a) for a in character.attacks):
            continue
        without = replace(character, **{flag: False})
        def gain_vs(e, without=without):
            return expected_damage_per_round(character, e, rounds_per_fight) - expected_damage_per_round(without, e, rounds_per_fight)
        gains = {ac: gain_vs(replace(enemy, armor_class=ac)) for ac in armor_classes}
        worth_it = [ac for ac, g in gains.items() if g > 0]
        if not worth_it:
            advice = "Turn it off at every armor class"
        elif len(worth_it) == len(gains):
            advice = f"Keep it on at every armor class ({min(gains)}-{max(gains)})"
        else:
            advice = f"Keep it on up to AC {max(worth_it)}, turn it off from AC {max(worth_it) + 1}"
        gain_now = gains.get(enemy.armor_class)
        if gain_now is None:
            gain_now = gain_vs(enemy)
        insights.append({
            "Character": character.name,
            "Feat": label,
            "Advice": advice,
            f"DPR Gain vs Current Enemy (AC {enemy.armor_class})": round(gain_now, 2),
        })
    return insights

def hit_chance(die=20, mod=0, ac=15, advantage=False, disadvantage=False, crit_on=20):
    """ Returns the chance to hit a target with a given armor class """
    p_hit, _ = hit_and_crit_chance(modifier=mod, difficulty_class=ac, advantage=advantage, disadvantage=disadvantage, crit_on=crit_on) if die == 20 else (None, None)
    return p_hit

# Simple crit chance calculator: https://bg3.wiki/wiki/Guide:Book%27s_Guide_to_Crits
def crit_chart():
    """ Simple crit chance DataFrame """
    crit_data = []
    for crit_on in range(20, 12, -1):
        crit_chance = (20-crit_on+1)/20
        crit_miss = 1-crit_chance
        crit_miss_w_adv = crit_miss * crit_miss
        crit_w_adv = 1-crit_miss_w_adv
        crit_data.append([crit_on, crit_chance, crit_w_adv])
    return pd.DataFrame(crit_data, columns=['crit_on', 'crit_chance', 'crit_w_adv'])
