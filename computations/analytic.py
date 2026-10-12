""" Analytic (exact) computations, used to validate the numerical simulation and to explain where damage comes from """
from dataclasses import asdict, replace
import numpy as np
import pandas as pd

from computations.models import calculate_attack_and_damage_context

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

def expected_attack_damage(attack_context, damage_context, p_first_hit=None):
    """ Expected damage of a single attack (before damage reduction, resistances are applied linearly)
        p_first_hit is the probability that this attack is the first to hit this round, used for once per turn damage """
    a = attack_context if isinstance(attack_context, dict) else asdict(attack_context)
    d = damage_context if isinstance(damage_context, dict) else asdict(damage_context)
    p_hit, p_crit = hit_and_crit_chance(**a)
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
    return expected * d["damage_multiplier"]

def attack_breakdown(character, enemy):
    """ Per attack table of to hit chance, crit chance and expected damage for a character against an enemy """
    attack_contexts, damage_contexts = calculate_attack_and_damage_context(character, enemy)
    rows = []
    p_no_hit_yet = 1.0
    for attack, a, d in zip(character.attacks, attack_contexts, damage_contexts):
        p_hit, p_crit = hit_and_crit_chance(**asdict(a))
        p_first_hit = None
        if d.once_per_turn_eligible and (d.once_num_die or d.once_modifier):
            p_trigger = p_crit if d.once_crit_only else p_hit
            p_first_hit = p_no_hit_yet * p_trigger
            p_no_hit_yet *= 1 - p_trigger
        if a.saving_throw:
            to_hit = f"DC {a.difficulty_class} vs {a.modifier:+d}"
        else:
            bonus_dice = " + ".join(f"{n}d{s}" for n, s in zip(a.num_die, a.die_size))
            to_hit = f"{a.modifier:+d}" + (f" + {bonus_dice}" if bonus_dice else "")
        dice = " + ".join(f"{n}d{s}" for n, s in zip(d.num_die, d.die_size))
        damage = dice + (f" {d.modifier:+d}" if d.modifier else "")
        rows.append({
            "Attack": attack.name,
            "To Hit": to_hit,
            "Damage": damage or "0",
            "Hit %": round(100 * p_hit, 1),
            "Crit %": round(100 * p_crit, 1),
            "Expected": round(expected_attack_damage(a, d, p_first_hit), 2),
        })
    return pd.DataFrame(rows, columns=["Attack", "To Hit", "Damage", "Hit %", "Crit %", "Expected"])

def expected_damage_per_round(character, enemy):
    """ Expected (mean) damage per round, ignoring damage reduction and rounding """
    return float(attack_breakdown(character, enemy)["Expected"].sum())

POWER_ATTACK_FEATS = {"GWM": ("Great Weapon Master", lambda a: a.type == "weapon (melee)" and a.heavy),
                      "sharpshooter": ("Sharpshooter", lambda a: a.type == "weapon (ranged)")}

def power_attack_insights(character, enemy, armor_classes):
    """ For each power attack feat (-5 to hit, +10 damage) a character has turned on, finds the armor classes where it is worth using.
        Uses the exact expected damage, so it is instant """
    insights = []
    for flag, (label, applies) in POWER_ATTACK_FEATS.items():
        if not getattr(character, flag) or not any(applies(a) for a in character.attacks):
            continue
        without = replace(character, **{flag: False})
        gains = {ac: expected_damage_per_round(character, replace(enemy, armor_class=ac)) - expected_damage_per_round(without, replace(enemy, armor_class=ac))
                 for ac in armor_classes}
        worth_it = [ac for ac, gain in gains.items() if gain > 0]
        if not worth_it:
            advice = "Turn it off at every armor class"
        elif len(worth_it) == len(gains):
            advice = f"Keep it on at every armor class ({min(gains)}-{max(gains)})"
        else:
            advice = f"Keep it on up to AC {max(worth_it)}, turn it off from AC {max(worth_it) + 1}"
        gain_now = gains.get(enemy.armor_class)
        if gain_now is None:
            gain_now = expected_damage_per_round(character, enemy) - expected_damage_per_round(without, enemy)
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
