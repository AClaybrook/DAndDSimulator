""" Numerical simulation of D&D combat
    Uses vectorized numpy operations for speed """
import numpy as np
import pandas as pd
from dataclasses import asdict
from models import AttackContext, DamageContext

np.random.seed(1) # Set random seed for reproducibility

def roll(num_rolls, die_size=20, reroll_on=None):
    """ Roll a die num_rolls times and return the results
        Rerolls dice on an optional reroll value"""
    rolls = np.random.randint(1, die_size+1, size=num_rolls)
    if reroll_on is not None:
        rerolls_mask = rolls <= reroll_on
        rolls[rerolls_mask] = np.random.randint(1, die_size+1, size=np.sum(rerolls_mask))
    return rolls

def roll_adv_dis(num_rolls, adv=False, dis=False, **kwargs):
    """ Roll a die num_rolls times, optionally with advantage or disadvantage"""
    if adv and not dis:
        return roll(2 * num_rolls, **kwargs).reshape(-1, 2).max(axis=1)
    elif dis and not adv:
        return roll(2 * num_rolls, **kwargs).reshape(-1, 2).min(axis=1)
    else:
        return roll(num_rolls, **kwargs).reshape(-1, 1).max(axis=1)

def attack_roll(num_rolls, attack_modifier=0, enemy_armor_class=15, crit_on=20, **kwargs):
    """ Roll an attack roll with num_rolls dice, adding attack_modifier to each roll, tracking hits and crits"""
    rolls = roll_adv_dis(num_rolls,**kwargs)
    attack_rolls = rolls + attack_modifier
    # Crit on crit_on or higher
    crit = np.logical_and(rolls >= crit_on, rolls != 1)
    # Normal hit and not a crit miss
    hit = np.logical_and(attack_rolls >= enemy_armor_class, rolls != 1)
    # Crits automatically hit
    hit[crit] = True
    return attack_rolls, rolls, hit, crit

def damage_roll(hit, crit, num_die=1, damage_die=6, damage_modifier=0, **kwargs):
    """ Roll damage for each hit and crit, adding damage_modifier to each roll"""
    # Roll damage for hits
    num_rolls = len(hit)
    hit_damage = np.zeros(num_rolls)
    hit_damage[hit] = roll(np.sum(hit) * num_die, die_size=damage_die, **kwargs).reshape(-1, num_die).sum(axis=1) + damage_modifier
    # Roll damage for crits
    crit_damage = np.zeros(num_rolls)
    crit_damage[crit] = roll(np.sum(crit) * num_die, die_size=damage_die, **kwargs).reshape(-1, num_die).sum(axis=1)
    # Track total, hit, and crit damage
    total_damage = hit_damage + crit_damage
    return total_damage, hit_damage, crit_damage

def attack(num_rolls, attack_context, damage_context):
    """ Roll attack and damage rolls for num_rolls dice, using attack_context and damage_context"""
    attack_rolls, rolls, hit, crit = attack_roll(num_rolls, **attack_context)
    total_damage, hit_damage, crit_damage = damage_roll(hit, crit, **damage_context)
    return attack_rolls, rolls, hit, crit, total_damage, hit_damage, crit_damage

def simulate_rounds(num_attacks, attack_context, damage_context, num_rounds=10000):
    """ Simulate num_rounds rounds of combat, with num_attacks attacks per round, using attack_context and damage_context"""
    num_rolls = num_rounds * num_attacks
    attack_rolls, rolls, hit, crit, damage, hit_damage, crit_damage = attack(num_rolls, attack_context, damage_context)
    rounds = np.repeat(np.arange(1, num_rounds + 1), num_attacks)
    results = np.column_stack([rounds, attack_rolls, rolls, hit, crit, damage, hit_damage, crit_damage])
    df = pd.DataFrame(results, columns=['round', 'attack roll', 'attack die', 'hit', 'crit', 'damage', 'hit damage', 'crit damage'])
    return df

def simulate_character_rounds(characters, enemy):
    """ Simulate rounds of combat for a list of characters against an enemy"""
    dfs = []
    df_by_rounds = []
    for c in characters:
        # Attack roll modifiers
        attack_context = AttackContext.from_character_and_enemy(c, enemy)

        # Damage roll modifiers
        damage_context = DamageContext.from_character_and_enemy(c, enemy)

        # Num Rounds
        df = simulate_rounds(c.num_attacks, asdict(attack_context), asdict(damage_context), num_rounds=100000)
        df_by_round = df.groupby('round').sum()
        dfs.append(df)
        df_by_rounds.append(df_by_round)
    return dfs, df_by_rounds