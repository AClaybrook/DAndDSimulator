""" Analytic Computations """
import pandas as pd
from computations.models import calculate_attack_and_damage_context

# Analytic Values
def expected_value(die_size, die_min=1):
    """ Returns the expected value of a die roll, which is a uniform distribution"""
    return (die_min + die_size)/2

def avg_damage(num_die, die_size, reroll_on=0):
    """ Average damage of multiple dice rolls, rerolling on a given value"""
    die_min = reroll_on + 1
    reroll_prob = reroll_on/die_size
    regular_damage = (1-reroll_prob) * expected_value(die_size, die_min=die_min) * num_die # Chance to not reroll
    reroll_damage = reroll_prob * expected_value(die_size, die_min=1) * num_die # Reroll can be any damage
    return reroll_damage + regular_damage

def hit_chance(die, mod=0, ac=15, advantage=False, disadvantage=False, crit_on=20):
    """ Returns the chance to hit a target with a given armor class."""
    roll_needed = ac - mod
    hit_prob = (die-roll_needed +1)/die
    # Crit chance, always crit on 20, somtimes this can be lower, such as 19, 18, 17, etc.
    crit_chance = (die-crit_on+1)/die # pylint: disable=unused-variable
    crit_miss = 1-crit_chance
    # Critical miss chance, always miss on 1
    critical_miss_chance = 1/die
    min_hit_chance = critical_miss_chance

    if disadvantage:
        min_hit_chance = (1 - critical_miss_chance)**2
        crit_chance = crit_chance**2 # Roll crit_on (usually 20) twice
        hit_prob = hit_prob**2
    elif advantage:
        min_hit_chance = critical_miss_chance**2 # Roll 1 twice
        crit_chance = 1 - crit_miss**2 # Roll less than crit_on (usually 20) twice
        hit_prob = 1 - (1-hit_prob)**2
    else:
        min_hit_chance = critical_miss_chance
    return max(min_hit_chance, hit_prob), crit_chance

# Simple crit chance calculator: https://bg3.wiki/wiki/Guide:Book%27s_Guide_to_Crits
def crit_chart():
    """ Simple crit chance DataFrame """
    crit_data = []
    for crit_on in range(20,12, -1):
        crit_chance = (20-crit_on+1)/20
        crit_miss = 1-crit_chance
        crit_miss_w_adv = crit_miss * crit_miss
        crit_w_adv = 1-crit_miss_w_adv
        crit_data.append([crit_on, crit_chance, crit_w_adv])
    return pd.DataFrame(crit_data, columns=['crit_on', 'crit_chance', 'crit_w_adv'])

def approx_analytic_dpa(attack_context, damage_context):
    """ Approximate analtic damage per attack.
    Note, the statistical effects of rolling die is not simply the same as adding the mean values.
    So this is not exact"""
    attack_mod = attack_context.modifier + (sum((avg_damage(n, s) for n, s in zip(attack_context.num_die, attack_context.die_size))))
    hit_prob, crit_prob = hit_chance(20, mod=attack_mod, ac=attack_context.difficulty_class, advantage=attack_context.advantage, disadvantage=attack_context.disadvantage, crit_on=attack_context.crit_on)
    damage_on_hit = (damage_context.modifier + sum((avg_damage(n, s, reroll_on=damage_context.reroll_on) for n, s in zip(damage_context.num_die, damage_context.die_size)))) * damage_context.damage_multiplier
    damage_from_crit = (sum((avg_damage(n, s, reroll_on=damage_context.reroll_on) for n, s in zip(damage_context.num_die, damage_context.die_size)))) * damage_context.damage_multiplier
    additional_damage_from_crit = (damage_context.crit_damage_modifier + sum((avg_damage(n, s, reroll_on=damage_context.reroll_on) for n, s in zip(damage_context.crit_num_die, damage_context.crit_damage_die)))) * damage_context.damage_multiplier
    damage_miss = (damage_context.miss_damage_modifier + sum((avg_damage(n, s) for n, s in zip(damage_context.miss_num_die, damage_context.miss_damage_die)))) * damage_context.failed_multiplier

    hit_damage = hit_prob*damage_on_hit
    crit_damage = crit_prob*(damage_from_crit + additional_damage_from_crit)
    miss_damage = (1-hit_prob)*damage_miss
    total_damage = hit_damage + crit_damage + miss_damage

    ndigits = 4
    return round(total_damage,ndigits), round(hit_damage,ndigits), round(crit_damage,ndigits), round(miss_damage,ndigits)

def approx_analytic_dpr(characters, enemy, verbose=False):
    """ Analytic DPR for a character"""
    c_dpr = {}
    for c in characters:
        c_dpr[c.name] = {'total':0, 'hit':0, 'crit':0, 'miss':0}

        attack_contexts, damage_contexts = calculate_attack_and_damage_context(c, enemy)
        for attack_context, damage_context in zip(attack_contexts, damage_contexts):
            t,h,c_,m = approx_analytic_dpa(attack_context, damage_context)
            if verbose:
                print(f'{c.name} t: {t}, h: {h}, c: {c_}, m: {m}')
            c_dpr[c.name]['total'] += t
            c_dpr[c.name]['hit'] += h
            c_dpr[c.name]['crit'] += c_
            c_dpr[c.name]['miss'] += m
        for k,v in c_dpr[c.name].items():
            c_dpr[c.name][k] = round(v,3)

    return c_dpr
