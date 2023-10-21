import pandas as pd

# Analytic Values
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

# Simple crit chance calculator
# https://bg3.wiki/wiki/Guide:Book%27s_Guide_to_Crits
def crit_chart():
    crit_data = []
    for crit_on in range(20,12, -1):
        crit_chance = (20-crit_on+1)/20
        crit_miss = 1-crit_chance
        crit_miss_w_adv = crit_miss * crit_miss
        crit_w_adv = 1-crit_miss_w_adv
        crit_data.append([crit_on, crit_chance, crit_w_adv])
    return pd.DataFrame(crit_data, columns=['crit_on', 'crit_chance', 'crit_w_adv'])