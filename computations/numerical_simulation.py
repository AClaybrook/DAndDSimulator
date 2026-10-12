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
    total_damage = hit_damage + crit_damage + miss_damage
    if modifier < 0 or miss_damage_modifier < 0 or crit_damage_modifier < 0 or once_modifier < 0:
        np.maximum(total_damage, 0, out=total_damage)
    if damage_multiplier != 1:
        total_damage = np.floor(total_damage * damage_multiplier).astype('int32')
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

STAT_NAMES = ['mean', 'min', '25%', '50%', '75%', 'max']
PERCENTILES = np.array([0, 25, 50, 75, 100])

def _bincount(values):
    """ Counts of each integer value, returns (counts, lowest value) """
    try:
        return np.bincount(values), 0
    except ValueError: # Negative values
        low = int(values.min())
        return np.bincount(values - low), low

def column_stats(values):
    """ Mean and percentiles of a 1d array (or a list of 1d arrays treated as one).
        Integer results use counting (O(n), no copies or sorting) rather than a partition,
        giving identical results to np.percentile (linear interpolation) several times faster """
    parts = values if isinstance(values, (list, tuple)) else [values]
    n = sum(len(p) for p in parts)
    if n == 0:
        return [np.nan] * len(STAT_NAMES)
    if not all(np.issubdtype(p.dtype, np.integer) for p in parts):
        merged = np.concatenate(parts)
        return [merged.mean(), *np.percentile(merged, PERCENTILES)]
    binned = [_bincount(p) for p in parts if len(p)]
    low = min(lo for _, lo in binned)
    size = max(len(c) + lo - low for c, lo in binned)
    counts = np.zeros(size, dtype=np.int64)
    for c, lo in binned:
        counts[lo - low:lo - low + len(c)] += c
    cumulative = np.cumsum(counts)
    position = PERCENTILES / 100 * (n - 1)
    below, above = np.floor(position).astype(np.int64), np.ceil(position).astype(np.int64)
    v_below = np.searchsorted(cumulative, below, side='right') + low
    v_above = np.searchsorted(cumulative, above, side='right') + low
    mean = np.dot(np.arange(size, dtype=np.float64), counts) / n + low
    return [mean, *(v_below + (v_above - v_below) * (position - below))]

def describe_array(values, columns):
    """ describe() for a column-major 2d numpy array, i.e. values[ii] is the column named columns[ii].
        values can also be a list of such arrays which are treated as if they were concatenated """
    parts = values if isinstance(values, list) else [values]
    parts = [np.atleast_2d(p) for p in parts]
    return pd.DataFrame(np.array([column_stats([p[ii] for p in parts]) for ii in range(len(columns))]).T, index=STAT_NAMES, columns=columns)

def describe(g):
    """ Faster implementation of pandas describe """
    if isinstance(g, pd.Series):
        g = g.to_frame()
    return describe_array(g.to_numpy().T, g.columns)

RESULT_COLUMNS = ['Round', 'Damage', 'Damage (From Hit)', 'Damage (From Crit)', 'Damage (Miss/Fail)', 'Attack Roll', 'Attack Roll (Die)', 'Hit', 'Hit (Non-Crit)', 'Hit (Crit)']

def simulate_attacks(attack_contexts, damage_contexts, num_rounds=10000, rng=RNG, damage_only=False):
    """ Simulate every attack of a character for num_rounds rounds, returns a list of numpy arrays (one per attack)
        with shape (RESULT_COLUMNS, num_rounds), or only the damage when damage_only.
        Arrays are column-major so each column is contiguous in memory, which is much faster for large simulations
        Attack rolls are rolled first so once per turn damage can be applied to the first hit of each round """
    attack_contexts = [a if isinstance(a, dict) else asdict(a) for a in attack_contexts]
    damage_contexts = [d if isinstance(d, dict) else asdict(d) for d in damage_contexts]
    rolled = [attack_roll(num_rounds, **a, rng=rng) for a in attack_contexts]

    hit_already = np.zeros(num_rounds, dtype=bool)
    results = []
    for (attack_rolls, rolls, hit, crit), d in zip(rolled, damage_contexts):
        once_mask = None
        if d.get("once_per_turn_eligible") and (d.get("once_num_die") or d.get("once_modifier")):
            trigger = crit if d.get("once_crit_only") else hit
            once_mask = trigger & ~hit_already
            hit_already |= trigger
        damage, hit_damage, crit_damage, miss_damage = damage_roll(hit, crit, **d, once_mask=once_mask, rng=rng)
        if damage_only:
            results.append(damage)
            continue
        result = np.empty((len(RESULT_COLUMNS), num_rounds), dtype='int32')
        result[0] = np.arange(1, num_rounds + 1)
        for ii, col in enumerate((damage, hit_damage, crit_damage, miss_damage, attack_rolls, rolls, hit, hit & ~crit, crit), start=1):
            result[ii] = col
        results.append(result)
    return results

def simulate_rounds(attack_context, damage_context, num_rounds=10000, rng=RNG):
    """ Simulate rounds of combat for a given attack_context and damage_context"""
    results = simulate_attacks([attack_context], [damage_context], num_rounds=num_rounds, rng=rng)[0]
    return pd.DataFrame(results.T, columns=RESULT_COLUMNS)

def group_by_name(results, attack_names):
    """ Concatenates the results of attacks that share a name, keeping the first occurrence order """
    grouped = {}
    for result, name in zip(results, attack_names):
        grouped.setdefault(name, []).append(result)
    return {name: arrays[0] if len(arrays) == 1 else np.concatenate(arrays, axis=-1) for name, arrays in grouped.items()}

def simulate_rounds_from_contexts(attack_contexts, damage_contexts, attack_names, by_round=True, cols=None, num_rounds=10000, rng=RNG):
    """ Simulate rounds of combat from a list of attacks and damage contexts
        Returns a dict of dataframes per attack name and a dataframe of the totals per round """
    damage_only = cols == 'Damage'
    columns = ['Damage'] if damage_only else RESULT_COLUMNS
    results = simulate_attacks(attack_contexts, damage_contexts, num_rounds=num_rounds, rng=rng, damage_only=damage_only)
    keep = [columns.index(c) for c in ([cols] if isinstance(cols, str) else cols)] if cols else list(range(len(columns)))
    out_columns = [columns[ii] for ii in keep]

    attack_df_dict = {
        name: pd.DataFrame(np.atleast_2d(values)[keep].T, columns=out_columns)
        for name, values in group_by_name(results, attack_names).items()
    }

    df_by_round = None
    if by_round:
        total = np.zeros((len(columns), num_rounds), dtype='int32')
        for result in results:
            total += result
        df_by_round = pd.DataFrame(total[keep].T, columns=out_columns, index=pd.RangeIndex(1, num_rounds + 1, name='Round'))
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
        attack_names = [a.name for a in c.attacks]
        results = simulate_attacks(attack_contexts, damage_contexts, num_rounds=num_rounds, rng=rng)
        grouped = {}
        for result, name in zip(results, attack_names):
            grouped.setdefault(name, []).append(result)
        names = list(grouped)
        ordered = [r for arrays in grouped.values() for r in arrays]

        # All Attacks per Round, built with numpy and categorical codes which is much faster than concatenating dataframes
        codes = np.repeat(np.arange(len(names), dtype='int16'), [len(arrays) * num_rounds for arrays in grouped.values()])
        attack_col = pd.Categorical.from_codes(codes, categories=names) if names else pd.Categorical([])
        if save_memory:
            damage = np.concatenate([r[1] for r in ordered]) if ordered else np.zeros(0, dtype='int32')
            df = pd.DataFrame({"Damage": damage, "Attack": attack_col})
        else:
            all_attacks = np.concatenate(ordered, axis=1) if ordered else np.zeros((len(RESULT_COLUMNS), 0), dtype='int32')
            df = pd.DataFrame(all_attacks.T, columns=RESULT_COLUMNS)
            df.insert(0, "Attack", attack_col)
        dfs.append(df)

        # Summary Stats grouped by attack, easier to do this now rather than tracking labels for each attack
        if grouped:
            df_by_attack = pd.concat({n: describe_array([r[1:] for r in arrays], RESULT_COLUMNS[1:]) for n, arrays in grouped.items()})
        else:
            df_by_attack = pd.DataFrame()
        dfs_by_attack.append(df_by_attack)

        # Grouped by Round
        total = np.zeros((len(RESULT_COLUMNS), num_rounds), dtype='int32')
        for result in results:
            total += result
        df_by_rounds.append(pd.DataFrame(total[1:].T, columns=RESULT_COLUMNS[1:], index=pd.RangeIndex(1, num_rounds + 1, name='Round')))
    return dfs, df_by_rounds, dfs_by_attack

def simulate_sweep(cases, label, num_rounds=10000, by_round=True, rng=RNG):
    """ Simulate a parameter sweep. cases is an iterable of (value, characters, enemy), characters are grouped by name across values.
        Only the damage is simulated, which keeps sweeps fast. Returns one row of summary stats per value and character (or attack) """
    rows = []
    for value, characters, enemy in cases:
        for c in characters:
            # Attack and Damage Contexts
            attack_contexts, damage_contexts = calculate_attack_and_damage_context(c, enemy)
            damages = simulate_attacks(attack_contexts, damage_contexts, num_rounds=num_rounds, rng=rng, damage_only=True)
            if by_round:
                # Summary Stats for each value
                total = np.sum(damages, axis=0) if damages else np.zeros(num_rounds, dtype='int32')
                rows.append([*column_stats(total), c.name, value])
            else:
                # Regroup by attacks with the same name, Summary Stats for each attack for each value
                grouped = {}
                for values, name in zip(damages, [a.name for a in c.attacks]):
                    grouped.setdefault(name, []).append(values)
                for name, values in grouped.items():
                    rows.append([*column_stats(values), f"{c.name}-{name}", c.name, value])

    columns = STAT_NAMES + (['Character'] if by_round else ['Character-Attack', 'Character']) + [label]
    return pd.DataFrame(rows, columns=columns, index=['Damage'] * len(rows))

@timeit
def simulate_rounds_from_characters_multi_acs(characters, enemy, armor_classes=None, num_rounds=10000, by_round=True, rng=RNG):
    """ Simulate rounds of combat for a list of characters against multiple armor classes"""
    armor_classes = armor_classes or range(10, 26)
    cases = ((ac, characters, replace(enemy, armor_class=ac)) for ac in armor_classes)
    return simulate_sweep(cases, 'Armor Class', num_rounds=num_rounds, by_round=by_round, rng=rng)

@timeit
def simulate_rounds_from_characters_by_level(characters, enemy, levels, character_at_level, num_rounds=10000, by_round=True, rng=RNG):
    """ Simulate rounds of combat for a list of characters at each level, character_at_level(character, level) builds each variant """
    cases = ((level, [character_at_level(c, level) for c in characters], enemy) for level in levels)
    return simulate_sweep(cases, 'Level', num_rounds=num_rounds, by_round=by_round, rng=rng)

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
