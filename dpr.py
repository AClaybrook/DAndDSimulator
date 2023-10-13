# %%
# import plotly.express as px
import random
import pandas as pd
import plotly.figure_factory as ff
import numpy as np
# from IPython.display import display

# Expected values
def expected_value(die_size):
    """ Returns the expected value of a die roll, which is a uniform distribution"""
    return (1 + die_size)/2

def avg_damage(num_die, die_size):
    """Average damage of multiple dice rolls"""
    ev = expected_value(die_size)
    return num_die * ev

def hit_chance(die, mod=0, ac=15, adv=False, dis=False, crit_on=20):
    roll_needed = ac - mod
    # Crit chance, always crit on 20, somtimes this can be lower, such as 19, 18, 17, etc.
    crit_chance = (die-crit_on+1)/die
    # Crit miss chance, always miss on 1
    crit_miss_chance = 1/die
    if dis:
        min_hit_chance = (1 - crit_miss_chance)**2
    elif adv:
        min_hit_chance = crit_miss_chance * crit_miss_chance
    return min(min_hit_chance, (die-roll_needed +1)/die)


# adv = [advantage(d1,d2) for d1 in rolls for d2 in rolls]
# dis = [disadvantage(d1,d2) for d1 in rolls for d2 in rolls]

# %%

# Numerical Simulation

# # Defaults
# rng = random.Random()
# rng.seed(1)

default_attack_context = {
    'attack_modifier': 0,
    'enemy_armor_class': 15,
    'adv': False,
    'dis': False,
    'crit_on': 20,
    'attack_reroll_on': None
}

default_damage_context = {
    'num_die': 1,
    'damage_die': 6,
    'damage_modifier': 0,
    'damage_reroll_on': None
}

def roll(die_size=20, reroll_on=None):
    rerolled = False
    res = rng.randint(1,die_size)
    if reroll_on is not None and res <= reroll_on:
        res = rng.randint(1,die_size)
        rerolled = True
    return res

def advantage(d1, d2):
    return max(d1, d2)

def disadvantage(d1, d2):
    return min(d1, d2)

def roll_adv_dis(adv=False, dis=False,  **kwargs):
    if adv and not dis:
        res = advantage(roll(**kwargs), roll(**kwargs))
    elif dis and not adv:
        res = disadvantage(roll(**kwargs), roll(**kwargs))
    else:
        res = roll(**kwargs)
    return res

def attack_roll(attack_modifier=0, enemy_armor_class=15, crit_on=20, attack_reroll_on=None, **kwargs):
    """ Returns total attack roll, whether it hits, whether it crits and the roll value"""
    roll_val = roll_adv_dis(reroll_on=attack_reroll_on, **kwargs)
    attack_roll_val = roll_val + attack_modifier
    # Crit miss
    if roll_val == 1:
        hit, crit = False, False
    # Crit hit
    elif roll_val >= crit_on:
        hit, crit = True, True
    # Normal hit
    elif attack_roll_val >= enemy_armor_class:
        hit, crit = True, False
    # Normal miss
    else:
        hit, crit = False, False

    return attack_roll_val, roll_val, hit, crit

def damage_roll(num_die=1, damage_die=6, damage_modifier=0, damage_reroll_on=None, crit=False, **kwargs):
    
    hit_damage = sum([roll(die_size=damage_die, reroll_on=damage_reroll_on, **kwargs) for _ in range(num_die)]) + damage_modifier
    
    crit_damage = 0
    if crit:
        crit_damage = sum([roll(die_size=damage_die, reroll_on=damage_reroll_on, **kwargs) for _ in range(num_die)])

    total_damage = hit_damage + crit_damage

    return total_damage, hit_damage, crit_damage

def attack(attack_context, damage_context):
    total_damage, hit_damage, crit_damage = 0, 0, 0
    attack_roll_val, roll_val, hit, crit = attack_roll(**attack_context)
    if hit:
        total_damage, hit_damage, crit_damage = damage_roll(crit=crit, **damage_context)
    return attack_roll_val, roll_val, hit, crit, total_damage, hit_damage, crit_damage

# Utility functions
def die_from_str(die_str):
    """Returns the number of dice and die size from a string of the form '2d6'"""
    die_str = die_str.lower()
    num_die, die_size = die_str.split('d')
    return int(num_die), int(die_size)


# %%
# Example 1

# Defaults
rng = random.Random()
rng.seed(1)

# Character stats
proficiency_bonus =  4 # Level 9-12
ability_modifier = 5 # 20-21
num_attacks = 3
GWM = False

## Attack

# Attack roll modifiers
attack_context = {
    **default_attack_context,
    'attack_modifier': ability_modifier + proficiency_bonus,
    'adv': False,
    'crit_on': 20,
    }

# Damage roll modifiers
num_die, die_size = die_from_str('2d6') # Weapon damage
damage_context = {
    **default_damage_context,
    'num_die': num_die,
    'damage_die': die_size,
    'damage_modifier': ability_modifier,
}

# Calcs
if GWM:
    attack_context['attack_modifier'] -= 5
    damage_context['damage_modifier'] += 10

# Num Rounds
num_rounds = 10000

results = np.zeros((num_rounds*num_attacks, 8), dtype=int)
row = 0
for round_ in range(num_rounds):
    # Damage per round
    dpr = 0
    for _ in range(num_attacks):
        attack_roll_val, roll_val, hit, crit, damage, hit_damage, crit_damage = attack(attack_context, damage_context)
        dpr += damage
        results[row] = np.array([round_+1, attack_roll_val, roll_val, hit, crit, damage, hit_damage, crit_damage])
        row += 1
        dpr += damage

df = pd.DataFrame(results, columns=['round', 'attack_roll', 'attack_die_roll', 'hit', 'crit', 'damage', 'hit_damage', 'crit_damage'])
display(df.describe())
df_by_round = df.groupby('round').sum()
display(df_by_round.describe())
#%%


# df.hist(column="damage", bins=25)
# df.plot.kde()
# df.describe()
# # %%

# hist_data = [damages]
# group_labels = ['distplot'] # name of the dataset

# fig = ff.create_distplot(hist_data, group_labels)
# fig.show()
# # %%

# %%
