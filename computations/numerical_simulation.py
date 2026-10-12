""" Numerical simulation of D&D combat
    Uses vectorized numpy operations for speed """
from dataclasses import asdict, replace
import numpy as np
import pandas as pd

from computations.models import calculate_attack_and_damage_context
from utilities.helper_functions import timeit

# Set random seed for reproducibility
SEED = 1
RNG = np.random.default_rng(SEED)

def set_seed(seed=SEED):
    """ Returns a random generator, seeded for reproducibility. Pass seed=None for a random seed"""
    return np.random.default_rng(seed)

def roll(num_rolls, die_size=20, reroll_on=0, rng=RNG):
    """ Roll a die num_rolls times and return the results
        Rerolls dice on an optional reroll value"""
    rolls = rng.integers(1, high=die_size+1, size=num_rolls, dtype='int32')
    if reroll_on > 0:
        rerolls_mask = rolls <= reroll_on
        rolls[rerolls_mask] = rng.integers(1, high=die_size+1, size=np.sum(rerolls_mask), dtype='int32')
    return rolls

def roll_adv_dis(num_rolls, advantage=False, disadvantage=False, **kwargs):
    """ Roll a die num_rolls times, optionally with advantage or disadvantage"""
    if advantage and not disadvantage:
        return np.maximum(roll(num_rolls, **kwargs), roll(num_rolls, **kwargs))
    elif disadvantage and not advantage:
        return np.minimum(roll(num_rolls, **kwargs), roll(num_rolls, **kwargs))
    else:
        return roll(num_rolls, **kwargs)

def roll_dice(num_rolls, num_die, die_size, reroll_on=0, rng=RNG):
    """ Sum of several groups of dice, i.e. num_die=[2,1], die_size=[6,8] is 2d6+1d8 """
    total = np.zeros(num_rolls, dtype='int32')
    for nd, ds in zip(num_die, die_size):
        for _ in range(nd): # Summing in place is faster and uses less memory than reshaping a numpy array
            total += roll(num_rolls, die_size=ds, reroll_on=reroll_on, rng=rng)
    return total

def roll_damage_dice(num_rolls, num_die, die_size, advantage=False, disadvantage=False, reroll_on=0, rng=RNG):
    """ Roll a set of damage dice, optionally rolling the whole set twice and keeping the higher (savage attacker) or lower total """
    total = roll_dice(num_rolls, num_die, die_size, reroll_on=reroll_on, rng=rng)
    if advantage != disadvantage:
        second = roll_dice(num_rolls, num_die, die_size, reroll_on=reroll_on, rng=rng)
        total = np.maximum(total, second) if advantage else np.minimum(total, second)
    return total

def attack_roll(num_rolls, num_die=None, die_size=None, modifier=0, difficulty_class=15, crit_on=20, always_hit=False, always_crit=False,
                saving_throw=False, advantage=False, disadvantage=False, reroll_on=0, rng=RNG):
    """ Roll an attack roll with num_rolls dice, adding attack_modifier to each roll, tracking hits and crits"""
    # Special cases
    ## Some attacks always hit, i.e. magic missile
    if always_hit:
        return np.full(num_rolls, 20+modifier), np.full(num_rolls, 20), np.ones(num_rolls, dtype=bool), np.zeros(num_rolls, dtype=bool)
    ## Some attacks always crit, i.e. melee attacks against paralyzed targets always crit
    if always_crit:
        return np.full(num_rolls, 20+modifier), np.full(num_rolls, 20), np.ones(num_rolls, dtype=bool), np.ones(num_rolls, dtype=bool)

    # Normal case
    rolls = roll_adv_dis(num_rolls, advantage=advantage, disadvantage=disadvantage, reroll_on=reroll_on, rng=rng)
    # Add modifiers, bonus dice such as bless are rolled normally
    attack_rolls = rolls + modifier + roll_dice(num_rolls, num_die or [], die_size or [], rng=rng)
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

def damage_roll(hit, crit, num_die=None, die_size=None, modifier=0, damage_multiplier=1, damage_reduction=0,
                advantage=False, disadvantage=False, reroll_on=0,
                miss_num_die=None, miss_damage_die=None, miss_damage_modifier=0, save_success_multiplier=0,
                crit_num_die=None, crit_damage_die=None, crit_damage_modifier=0,
                once_num_die=None, once_die_size=None, once_modifier=0, once_mask=None, rng=RNG, **_):
    """ Roll damage for each hit, crit and miss.
        Resistances/vulnerabilities and damage reduction are applied to the total damage of the attack (rounded down)"""
    num_die = num_die or []
    die_size = die_size or []
    dice_kwargs = {"advantage": advantage, "disadvantage": disadvantage, "reroll_on": reroll_on, "rng": rng}

    num_rolls = len(hit)
    miss = ~hit
    num_hits = int(hit.sum())
    num_crits = int(crit.sum())
    num_misses = num_rolls - num_hits

    # Roll damage for hits
    hit_damage = np.zeros(num_rolls, dtype='int32')
    hit_damage[hit] = roll_damage_dice(num_hits, num_die, die_size, **dice_kwargs) + modifier

    # Roll damage for crits (roll hit dice twice, traditionally there is no flat modifier for crits)
    # Bonus damage for crits, i.e. half-orc savage attacks, brutal critical, etc.
    crit_damage = np.zeros(num_rolls, dtype='int32')
    crit_damage[crit] = (roll_damage_dice(num_crits, num_die, die_size, **dice_kwargs)
                         + roll_dice(num_crits, crit_num_die or [], crit_damage_die or [], reroll_on=reroll_on, rng=rng)
                         + crit_damage_modifier)

    # Once per turn damage on the first hit of the round, i.e. sneak attack, dice are doubled on a crit
    if once_mask is not None and once_mask.any() and (once_num_die or once_modifier):
        once_hits = once_mask & hit
        once_crits = once_mask & crit
        hit_damage[once_hits] += roll_dice(int(once_hits.sum()), once_num_die or [], once_die_size or [], reroll_on=reroll_on, rng=rng) + once_modifier
        crit_damage[once_crits] += roll_dice(int(once_crits.sum()), once_num_die or [], once_die_size or [], reroll_on=reroll_on, rng=rng)

    # Roll damage for misses/successful saving throws
    miss_damage = np.zeros(num_rolls, dtype='int32')
    misses = roll_dice(num_misses, miss_num_die or [], miss_damage_die or [], rng=rng) + miss_damage_modifier
    if save_success_multiplier:
        # i.e. half damage on a successful save
        saved = roll_damage_dice(num_misses, num_die, die_size, **dice_kwargs) + modifier
        misses = misses + np.floor(saved * save_success_multiplier).astype('int32')
    miss_damage[miss] = misses

    # Track total, hit, crit, and miss/fail damage
    raw_total = hit_damage + crit_damage + miss_damage
    total_damage = np.floor(np.maximum(raw_total, 0) * damage_multiplier).astype('int32')
    if damage_reduction:
        total_damage = np.maximum(total_damage - damage_reduction, 0)
    if damage_multiplier != 1:
        hit_damage = np.floor(hit_damage * damage_multiplier).astype('int32')
        crit_damage = np.floor(crit_damage * damage_multiplier).astype('int32')
        miss_damage = np.floor(miss_damage * damage_multiplier).astype('int32')
    return total_damage, hit_damage, crit_damage, miss_damage

def attack(num_rolls, attack_context, damage_context, rng=RNG, once_mask=None):
    """ Roll attack and damage rolls for num_rolls dice, using attack_context and damage_context"""
    attack_rolls, rolls, hit, crit = attack_roll(num_rolls, **attack_context, rng=rng)
    total_damage, hit_damage, crit_damage, miss_damage = damage_roll(hit, crit, **damage_context, once_mask=once_mask, rng=rng)
    return attack_rolls, rolls, hit, crit, total_damage, hit_damage, crit_damage, miss_damage

def describe(g):
    """ Faster implementation of pandas describe """
    desc = pd.concat([g.agg(["mean"]), g.agg(np.percentile, q=[0, 25, 50, 75, 100])])
    desc.index = ['mean', 'min', '25%', '50%', '75%', 'max']
    return desc

RESULT_COLUMNS = ['Round', 'Damage', 'Damage (From Hit)', 'Damage (From Crit)', 'Damage (Miss/Fail)', 'Attack Roll', 'Attack Roll (Die)', 'Hit', 'Hit (Non-Crit)', 'Hit (Crit)']

def simulate_attacks(attack_contexts, damage_contexts, num_rounds=10000, rng=RNG):
    """ Simulate every attack of a character for num_rounds rounds, returns a list of numpy arrays (one per attack)
        Attack rolls are rolled first so once per turn damage can be applied to the first hit of each round """
    attack_contexts = [a if isinstance(a, dict) else asdict(a) for a in attack_contexts]
    damage_contexts = [d if isinstance(d, dict) else asdict(d) for d in damage_contexts]
    rolled = [attack_roll(num_rounds, **a, rng=rng) for a in attack_contexts]

    hit_already = np.zeros(num_rounds, dtype=bool)
    rounds = np.arange(1, num_rounds + 1, dtype='int32')
    results = []
    for (attack_rolls, rolls, hit, crit), d in zip(rolled, damage_contexts):
        once_mask = None
        if d.get("once_per_turn_eligible"):
            once_mask = hit & ~hit_already
            hit_already |= hit
        damage, hit_damage, crit_damage, miss_damage = damage_roll(hit, crit, **d, once_mask=once_mask, rng=rng)
        results.append(np.array((rounds, damage, hit_damage, crit_damage, miss_damage, attack_rolls, rolls, hit, hit != crit, crit), dtype='int32').T)
    return results

def simulate_rounds(attack_context, damage_context, num_rounds=10000, rng=RNG):
    """ Simulate rounds of combat for a given attack_context and damage_context"""
    results = simulate_attacks([attack_context], [damage_context], num_rounds=num_rounds, rng=rng)[0]
    return pd.DataFrame(results, columns=RESULT_COLUMNS)

def simulate_rounds_from_contexts(attack_contexts, damage_contexts, attack_names, by_round=True, cols=None, num_rounds=10000, rng=RNG):
    """ Simulate rounds of combat from a list of attacks and damage contexts """
    attack_df_dict = {}
    df_by_round = None
    results = simulate_attacks(attack_contexts, damage_contexts, num_rounds=num_rounds, rng=rng)
    for result, attack_name in zip(results, attack_names):
        df_per_attack = pd.DataFrame(result, columns=RESULT_COLUMNS)
        if cols:
            df_per_attack = df_per_attack[cols]
            if isinstance(df_per_attack, pd.Series):
                df_per_attack = pd.DataFrame(df_per_attack)
        if attack_name in attack_df_dict:
            attack_df_dict[attack_name] = pd.concat([attack_df_dict[attack_name], df_per_attack], ignore_index=True)
        else:
            attack_df_dict[attack_name] = df_per_attack
        if by_round:
            if df_by_round is None:
                df_by_round = df_per_attack.copy()
            else:
                df_by_round = df_by_round.add(df_per_attack, fill_value=0)

    if by_round:
        if df_by_round is None:
            # A character without attacks deals no damage
            df_by_round = pd.DataFrame(0, index=range(num_rounds), columns=[cols] if isinstance(cols, str) else (cols or RESULT_COLUMNS))
        df_by_round.index = df_by_round.index+1
        df_by_round.index.name = 'Round'
        if 'Round' in df_by_round.columns:
            df_by_round = df_by_round.drop('Round', axis=1)

    return attack_df_dict, df_by_round


@timeit
def simulate_rounds_from_characters(characters, enemy, num_rounds=10000, save_memory=False, rng=RNG):
    """ Simulate rounds of combat for a list of characters against an enemy"""
    dfs = []
    df_by_rounds = []
    dfs_by_attack = []

    for c in characters:
        # Attack and Damage Contexts
        attack_contexts, damage_contexts = calculate_attack_and_damage_context(c, enemy)

        # Per Attack
        attack_names = [a.name for a in c.attacks]
        attack_df_dict, df_by_round = simulate_rounds_from_contexts(attack_contexts, damage_contexts, attack_names, by_round=True, num_rounds=num_rounds, rng=rng)

        # All Attacks per Round
        if attack_df_dict:
            df = pd.concat(attack_df_dict).reset_index().drop('level_1', axis=1).rename({'level_0': 'Attack'}, axis=1)
        else:
            df = pd.DataFrame(columns=['Attack'] + RESULT_COLUMNS)
        df['Attack'] = df['Attack'].astype('category')
        if save_memory:
            dfs.append(df[["Damage", "Attack"]])
        else:
            dfs.append(df)

        # Summary Stats grouped by attack, easier to do this now rather than tracking labels for each attack
        # Using a dictionaries for grouping is much faster than using pandas groupby, apply, and describe
        if attack_df_dict:
            df_by_attack = pd.concat({n: describe(g.drop('Round', axis=1)) for n, g in attack_df_dict.items()})
        else:
            df_by_attack = pd.DataFrame()
        dfs_by_attack.append(df_by_attack)

        # Grouped by Round
        df_by_rounds.append(df_by_round)
    return dfs, df_by_rounds, dfs_by_attack

@timeit
def simulate_rounds_from_characters_multi_acs(characters, enemy, armor_classes=None, num_rounds=10000, by_round=True, rng=RNG):
    """ Simulate rounds of combat for a list of characters against multiple armor classes"""

    if not armor_classes:
        armor_classes = range(10, 26)

    df_multi_ac = []

    for ac in armor_classes:
        enemy_ac = replace(enemy, armor_class=ac)
        for c in characters:
            # Attack and Damage Contexts
            attack_contexts, damage_contexts = calculate_attack_and_damage_context(c, enemy_ac)
            attack_names = [a.name for a in c.attacks]
            # Simulate all attacks
            if by_round:
                _, df_by_round = simulate_rounds_from_contexts(attack_contexts, damage_contexts, attack_names, cols='Damage', by_round=by_round, num_rounds=num_rounds, rng=rng)

                # Summary Stats for each AC
                df_ac = describe(df_by_round).T
                df_ac['Character'] = c.name
                df_ac['Armor Class'] = ac
                df_multi_ac.append(df_ac)

            else:
                attack_df_dict, _ = simulate_rounds_from_contexts(attack_contexts, damage_contexts, attack_names, cols='Damage', by_round=by_round, num_rounds=num_rounds, rng=rng)

                # Regroup by attacks with the same name
                for name, g in attack_df_dict.items():
                    # Summary Stats for each attack for each AC
                    df_ac = describe(g).T
                    df_ac['Character-Attack'] = f"{c.name}-{name}"
                    df_ac['Character'] = c.name
                    df_ac['Armor Class'] = ac
                    df_multi_ac.append(df_ac)

    return pd.concat(df_multi_ac)

def rounds_to_kill(damage_per_round, hit_points, max_rounds=30, num_fights=None, rng=RNG):
    """ Number of rounds needed to deal hit_points damage, for num_fights simulated fights.
        Rounds are independent, so fights are built by resampling the simulated rounds.
        Fights that last longer than max_rounds are reported as max_rounds + 1 """
    damage_per_round = np.asarray(damage_per_round)
    num_fights = num_fights or len(damage_per_round)
    hit_points = max(int(hit_points), 1)
    alive = np.ones(num_fights, dtype=bool)
    total = np.zeros(num_fights)
    result = np.full(num_fights, max_rounds + 1, dtype='int32')
    for r in range(1, max_rounds + 1):
        total[alive] += damage_per_round[rng.integers(0, len(damage_per_round), size=int(alive.sum()))]
        killed = alive & (total >= hit_points)
        result[killed] = r
        alive &= ~killed
        if not alive.any():
            break
    return result

@timeit
def simulate_rounds_to_kill(characters, enemy, num_rounds=10000, max_rounds=30, rng=RNG):
    """ Distribution of the number of rounds each character needs to kill the enemy """
    _, df_by_rounds, _ = simulate_rounds_from_characters(characters, enemy, num_rounds=num_rounds, save_memory=True, rng=rng)
    return pd.DataFrame({
        c.name: rounds_to_kill(df["Damage"].to_numpy(), enemy.hit_points, max_rounds=max_rounds, rng=rng)
        for c, df in zip(characters, df_by_rounds)
    })
