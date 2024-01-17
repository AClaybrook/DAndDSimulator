""" Numerical simulation of D&D combat
    Uses vectorized numpy operations for speed """
from dataclasses import asdict
import numpy as np
import pandas as pd

from models import calculate_attack_and_damage_context

# Set random seed for reproducibility
SEED = 1
np.random.seed(SEED)

def set_seed(seed=SEED):
    """ Set random seed for reproducibility"""
    np.random.seed(seed)

def roll(num_rolls, die_size=20, reroll_on=0):
    """ Roll a die num_rolls times and return the results
        Rerolls dice on an optional reroll value"""
    rolls = np.random.randint(1, die_size+1, size=num_rolls)
    if reroll_on > 0:
        rerolls_mask = rolls <= reroll_on
        rolls[rerolls_mask] = np.random.randint(1, die_size+1, size=np.sum(rerolls_mask))
    return rolls

def roll_adv_dis(num_rolls, advantage=False, disadvantage=False, **kwargs):
    """ Roll a die num_rolls times, optionally with advantage or disadvantage"""
    if advantage and not disadvantage:
        return roll(2 * num_rolls, **kwargs).reshape(-1, 2).max(axis=1)
    elif disadvantage and not advantage:
        return roll(2 * num_rolls, **kwargs).reshape(-1, 2).min(axis=1)
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
    hit_damage = np.zeros(num_rolls)
    hit_damage[hit] += modifier
    for nd, ds in zip(num_die, die_size):
        hit_damage[hit] += roll_adv_dis(np.sum(hit) *  nd, die_size=ds, **kwargs).reshape(-1, nd).sum(axis=1)
    hit_damage[hit] = np.floor(hit_damage[hit]*damage_multiplier)
    # Roll damage for misses/failed saving throws
    miss = ~hit
    miss_damage = np.zeros(num_rolls)
    miss_damage[miss] = miss_damage_modifier
    for nd, ds in zip(miss_num_die, miss_damage_die):
        miss_damage[miss] += roll_adv_dis(np.sum(miss) *  nd, die_size=ds, **kwargs).reshape(-1, nd).sum(axis=1)
    miss_damage[miss] = np.floor(miss_damage[miss]*failed_multiplier) # Usually 1/2 for saving throws
    miss_damage[miss] = np.floor(miss_damage[miss]*damage_multiplier)
    # Roll damage for crits (roll hit dice twice, traditionally there is no flat modifier for crits)
    crit_damage = np.zeros(num_rolls)
    for nd, ds in zip(num_die, die_size):
        crit_damage[crit] = roll_adv_dis(np.sum(crit) * nd, die_size=ds, **kwargs).reshape(-1, nd).sum(axis=1)
    # Bonus damage for crits, i.e. half-orc savage attacks, brutal critical, etc.
    crit_damage[crit] += crit_damage_modifier
    for nd, ds in zip(crit_num_die, crit_damage_die):
        crit_damage[crit] = roll_adv_dis(np.sum(crit) * nd, die_size=ds, **kwargs).reshape(-1, nd).sum(axis=1)
    crit_damage[crit] = np.floor(crit_damage[crit]*damage_multiplier)
    # Track total, hit, crit, and miss/fail damage
    total_damage = hit_damage + crit_damage + miss_damage
    return total_damage, hit_damage, crit_damage, miss_damage

def attack(num_rolls, attack_context, damage_context):
    """ Roll attack and damage rolls for num_rolls dice, using attack_context and damage_context"""
    attack_rolls, rolls, hit, crit = attack_roll(num_rolls, **attack_context)
    total_damage, hit_damage, crit_damage, miss_damage = damage_roll(hit, crit, **damage_context)
    return attack_rolls, rolls, hit, crit, total_damage, hit_damage, crit_damage, miss_damage

def simulate_rounds(attack_context, damage_context, num_rounds=10000):
    """ Simulate num_rounds rounds of combat, with num_attacks attacks per round, using attack_context and damage_context"""
    attack_rolls, rolls, hit, crit, damage, hit_damage, crit_damage, miss_damage = attack(num_rounds, attack_context, damage_context)
    rounds = np.arange(1, num_rounds + 1)
    results = np.column_stack([rounds, damage, hit_damage, crit_damage,miss_damage, attack_rolls, rolls, hit, hit != crit, crit])
    df = pd.DataFrame(results, columns=['Round', 'Damage', 'Damage (From Hit)', 'Damage (From Crit)', 'Damage (Miss/Fail)','Attack Roll', 'Attack Roll (Die)', 'Hit', 'Hit (Non-Crit)', 'Hit (Crit)'])
    return df

def simulate_character_rounds(characters, enemy, num_rounds=10000):
    """ Simulate rounds of combat for a list of characters against an enemy"""
    dfs = []
    df_by_rounds = []
    dfs_by_attack = []

    for c in characters:
        # Attack and Damage Contexts
        attack_contexts, damage_contexts = calculate_attack_and_damage_context(c, enemy)

        # Per Attack
        dfPerAttacks = []
        attack_names = [a.name for a in c.attacks]
        for ii, (a, d) in enumerate(zip(attack_contexts, damage_contexts)):
            dfPerAttack = simulate_rounds(asdict(a), asdict(d), num_rounds=num_rounds)
            dfPerAttack['Attack'] = attack_names[ii]
            dfPerAttacks.append(dfPerAttack)
        
        # All Attacks per Round
        df = pd.concat(dfPerAttacks)
        dfs.append(df)

        # Summary Stats grouped by attack, easier to do this now rather than tracking labels for each attack
        df_by_attack = df.drop('Round',axis=1).groupby('Attack').apply(lambda g: g.describe().drop(['count','std']))
        dfs_by_attack.append(df_by_attack)

        # Grouped by Round
        df_by_round = df.drop('Attack', axis=1).groupby('Round').sum()
        df_by_rounds.append(df_by_round)

    return dfs, df_by_rounds, dfs_by_attack

def simulate_character_rounds_for_multiple_armor_classes(characters, enemy, armor_classes=None, num_rounds=10000, by_round=True):
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
                        simulate_rounds(asdict(a), asdict(d), num_rounds=num_rounds)
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
                    dfPerAttack = simulate_rounds(asdict(a), asdict(d), num_rounds=num_rounds)
                    dfPerAttack['Character-Attack'] = f"{c.name}-{attack_names[ii]}"
                    dfPerAttack = dfPerAttack[["Damage","Character-Attack"]]
                    attack_list.append(dfPerAttack)
                    
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