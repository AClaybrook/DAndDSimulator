""" Numerical simulation of D&D combat
    Uses vectorized numpy operations for speed """
from dataclasses import asdict
import numpy as np
import pandas as pd

from computations.models import calculate_attack_and_damage_context
from utilities.helper_functions import timeit

# Set random seed for reproducibility
SEED = 1
RNG = np.random.default_rng(SEED)

def set_seed(seed=SEED):
    """ Set random seed for reproducibility"""
    return np.random.default_rng(seed)

def roll(num_rolls, die_size=20, reroll_on=0, rng=RNG):
    """ Roll a die num_rolls times and return the results
        Rerolls dice on an optional reroll value"""
    rolls = rng.integers(1, high=die_size+1, size=num_rolls)
    if reroll_on > 0:
        rerolls_mask = rolls <= reroll_on
        rolls[rerolls_mask] = rng.integers(1, high=die_size+1, size=np.sum(rerolls_mask))
    return rolls

def roll_adv_dis(num_rolls, advantage=False, disadvantage=False, **kwargs):
    """ Roll a die num_rolls times, optionally with advantage or disadvantage"""
    if advantage and not disadvantage:
        return np.maximum(roll(num_rolls, **kwargs), roll(num_rolls, **kwargs))
    elif disadvantage and not advantage:
        return np.minimum(roll(num_rolls, **kwargs), roll(num_rolls, **kwargs))
    else:
        return roll(num_rolls, **kwargs)

def attack_roll(num_rolls, num_die = None, die_size=None, modifier=0, difficulty_class=15, crit_on=20,always_hit=False,always_crit=False, saving_throw=False,**kwargs):
    """ Roll an attack roll with num_rolls dice, adding attack_modifier to each roll, tracking hits and crits"""
    # Special cases
    ## Some attacks always hit, i.e. magic missile
    if always_hit:
        return np.ones(num_rolls)*20+modifier, np.ones(num_rolls)*20, np.ones(num_rolls, dtype=bool), np.zeros(num_rolls, dtype=bool)
    ## Some attacks always crit, i.e. melee attacks against paralyzed targets always crit
    if always_crit:
        return np.ones(num_rolls)*20+modifier, np.ones(num_rolls)*20, np.ones(num_rolls, dtype=bool), np.ones(num_rolls, dtype=bool)

    # Normal case
    rolls = roll_adv_dis(num_rolls,**kwargs)
    # Add modifiers
    attack_rolls = rolls + modifier
    num_die =  [] if num_die is None else num_die
    die_size = [] if die_size is None else die_size
    for nd, ds in zip(num_die, die_size):
        attack_rolls += roll_adv_dis(num_rolls * nd, die_size=ds, **kwargs).reshape(-1, nd).sum(axis=1)
    # Saving throw, a hit is if the roll is lower than the difficulty class, crits are ignored
    if saving_throw:
        hit = attack_rolls < difficulty_class
        return attack_rolls, rolls, hit, np.zeros(num_rolls, dtype=bool)
    # Normal hit and not a crit miss
    hit = np.logical_and(attack_rolls >= difficulty_class, rolls != 1)
    # Crit on crit_on or higher and crits automatically hit
    crit = np.logical_and(rolls >= crit_on, rolls != 1)
    hit[crit] = True
    return attack_rolls, rolls, hit, crit

def damage_roll(hit, crit, num_die=None, die_size=None, modifier=0, damage_multiplier=1, miss_num_die=None, miss_damage_die=None, miss_damage_modifier=0, failed_multiplier=1, crit_num_die=None, crit_damage_die=None, crit_damage_modifier=0, **kwargs):
    """ Roll damage for each hit and crit, adding damage_modifier to each roll"""
    # Defaults
    num_die =  [] if num_die is None else num_die
    die_size = [] if die_size is None else die_size
    miss_num_die = [] if miss_num_die is None else miss_num_die
    miss_damage_die = [] if miss_damage_die is None else miss_damage_die
    crit_num_die = [] if crit_num_die is None else crit_num_die
    crit_damage_die = [] if crit_damage_die is None else crit_damage_die

    num_rolls = len(hit)
    # Roll damage for hits
    hit_damage = np.zeros(num_rolls, dtype='int32')
    hits = hit_damage[hit]
    hits += modifier
    num_hits = len(hits)
    for nd, ds in zip(num_die, die_size):
        hits += np.array([roll_adv_dis(num_hits, die_size=ds, **kwargs) for _ in range(nd)]).sum(axis=0) # a list comp is faster than reshaping a numpy array

    hit_damage[hit] = np.multiply(hits, damage_multiplier)

    # Roll damage for misses/failed saving throws
    miss = ~hit
    miss_damage = np.zeros(num_rolls, dtype='int32')
    misses = miss_damage[miss]
    misses += miss_damage_modifier
    num_misses = len(misses)
    for nd, ds in zip(miss_num_die, miss_damage_die):
        misses += np.array([roll_adv_dis(num_misses, die_size=ds, **kwargs) for _ in range(nd)]).sum(axis=0)
    misses = np.multiply(misses, failed_multiplier)
    misses = np.multiply(misses, damage_multiplier)
    miss_damage[miss] = misses

    # Roll damage for crits (roll hit dice twice, traditionally there is no flat modifier for crits)
    crit_damage = np.zeros(num_rolls, dtype='int32')
    crits = crit_damage[crit]
    num_crits = len(crits)
    for nd, ds in zip(num_die, die_size):
        crits += np.array([roll_adv_dis(num_crits, die_size=ds, **kwargs) for _ in range(nd)]).sum(axis=0)
    # Bonus damage for crits, i.e. half-orc savage attacks, brutal critical, etc.
    crits += crit_damage_modifier
    for nd, ds in zip(crit_num_die, crit_damage_die):
        crits += np.array([roll_adv_dis(num_crits, die_size=ds, **kwargs) for _ in range(nd)]).sum(axis=0)
    crit_damage[crit] = np.multiply(crits, damage_multiplier)

    # Track total, hit, crit, and miss/fail damage
    total_damage = hit_damage + crit_damage + miss_damage
    return total_damage, hit_damage, crit_damage, miss_damage

def attack(num_rolls, attack_context, damage_context, **kwargs):
    """ Roll attack and damage rolls for num_rolls dice, using attack_context and damage_context"""
    attack_rolls, rolls, hit, crit = attack_roll(num_rolls, **attack_context, **kwargs)
    total_damage, hit_damage, crit_damage, miss_damage = damage_roll(hit, crit, **damage_context, **kwargs)
    return attack_rolls, rolls, hit, crit, total_damage, hit_damage, crit_damage, miss_damage

def simulate_rounds(attack_context, damage_context, num_rounds=10000, **kwargs):
    """ Simulate num_rounds rounds of combat, with num_attacks attacks per round, using attack_context and damage_context"""
    attack_rolls, rolls, hit, crit, damage, hit_damage, crit_damage, miss_damage = attack(num_rounds, attack_context, damage_context, **kwargs)
    rounds = np.arange(1, num_rounds + 1)
    results = np.array((rounds, damage, hit_damage, crit_damage,miss_damage, attack_rolls, rolls, hit, hit != crit, crit),dtype='int32').T
    df = pd.DataFrame(results, columns=['Round', 'Damage', 'Damage (From Hit)', 'Damage (From Crit)', 'Damage (Miss/Fail)','Attack Roll', 'Attack Roll (Die)', 'Hit', 'Hit (Non-Crit)', 'Hit (Crit)'])
    return df

@timeit
def simulate_character_rounds(characters, enemy, num_rounds=10000, save_memory=False, **kwargs):
    """ Simulate rounds of combat for a list of characters against an enemy"""
    dfs = []
    df_by_rounds = []
    dfs_by_attack = []

    for c in characters:
        # Attack and Damage Contexts
        attack_contexts, damage_contexts = calculate_attack_and_damage_context(c, enemy)

        # Per Attack
        df_per_attacks = []
        attack_names = [a.name for a in c.attacks]
        for ii, (a, d) in enumerate(zip(attack_contexts, damage_contexts)):
            df_per_attack = simulate_rounds(asdict(a), asdict(d), num_rounds=num_rounds, **kwargs)
            df_per_attack['Attack'] = attack_names[ii]
            df_per_attack['Attack'] = df_per_attack['Attack'].astype('category')
            df_per_attacks.append(df_per_attack)

        # All Attacks per Round
        df = pd.concat(df_per_attacks)
        df['Attack'] = df['Attack'].astype('category')
        if save_memory:
            dfs.append(df[["Damage","Attack"]])
        else:
            dfs.append(df)

        # Summary Stats grouped by attack, easier to do this now rather than tracking labels for each attack
        df_by_attack = df.drop('Round',axis=1).groupby('Attack',observed=False).apply(lambda g: g.describe().drop(['count','std']))
        dfs_by_attack.append(df_by_attack)

        # Grouped by Round
        df_by_round = df.drop('Attack', axis=1).groupby('Round').sum()
        df_by_rounds.append(df_by_round)

    return dfs, df_by_rounds, dfs_by_attack

@timeit
def simulate_character_rounds_for_multiple_armor_classes(characters, enemy, armor_classes=None, num_rounds=10000, by_round=True, **kwargs):
    """ Simulate rounds of combat for a list of characters against multiple armor classes"""

    if not armor_classes:
        armor_classes = range(10, 26)

    df_multi_ac = []

    for ac in armor_classes:
        enemy.armor_class = ac
        for c in characters:
            # Attack and Damage Contexts
            attack_contexts, damage_contexts = calculate_attack_and_damage_context(c, enemy)

            # Simulate all attacks
            if by_round:
                df_grouped = pd.concat(
                    [
                        simulate_rounds(asdict(a), asdict(d), num_rounds=num_rounds,**kwargs)
                        for a, d in zip(attack_contexts, damage_contexts)
                    ]
                    ).groupby('Round').sum()['Damage']

                # Summary Stats for each AC
                df_ac = df_grouped.describe().drop(['count','std'])
                df_ac['Character'] = c.name
                df_ac['Armor Class'] = ac
                df_multi_ac.append(df_ac)

            else:
                attack_names = [a.name for a in c.attacks]
                attack_list = []
                for ii, (a, d) in enumerate(zip(attack_contexts, damage_contexts)):
                    df_per_attack = simulate_rounds(asdict(a), asdict(d), num_rounds=num_rounds,**kwargs)
                    df_per_attack['Character-Attack'] = f"{c.name}-{attack_names[ii]}"
                    df_per_attack = df_per_attack[["Damage","Character-Attack"]]
                    attack_list.append(df_per_attack)

                # Regroup by attacks with the same name
                for name, g in pd.concat(attack_list).groupby('Character-Attack'):
                    # Summary Stats for each attack for each AC
                    df_ac = g.describe().drop(['count','std']).T
                    df_ac['Character-Attack'] = name
                    df_ac['Character'] = c.name
                    df_ac['Armor Class'] = ac
                    df_multi_ac.append(df_ac)

    if by_round:
        return pd.concat(df_multi_ac, axis=1).T
    else:
        return pd.concat(df_multi_ac)
