""" Parameter sweeps: simulate every character for each value of one parameter, used by the DPR/DPA Sweep graphs and exports """
from collections import Counter
from dataclasses import replace

from computations.models import STATS
from computations.numerical_simulation import simulate_sweep
from game_data import RULESETS
from game_data.classes import character_at_level
from utilities.helper_functions import timeit

def primary_stat(character):
    """ The ability score most of the character's attacks use """
    stats = Counter(a.ability_stat for a in character.attacks)
    return stats.most_common(1)[0][0] if stats else "strength"

def _armor_class(characters, enemy, value):
    return characters, replace(enemy, armor_class=value)

def _level(characters, enemy, value):
    return [character_at_level(c, value) for c in characters], enemy

def _enemy_save_bonus(characters, enemy, value):
    return characters, replace(enemy, **{f"{stat}_save": value for stat in STATS})

def _attack_ability_score(characters, enemy, value):
    return [replace(c, **{primary_stat(c): value}) for c in characters], enemy

# Parameter name: (values for a ruleset, function returning the characters and enemy for a value, description)
SWEEP_PARAMETERS = {
    "Armor Class": (lambda ruleset: range(10, 26), _armor_class,
                    "Enemy armor class 10-25"),
    "Level": (lambda ruleset: range(1, RULESETS[ruleset]["max_level"] + 1), _level,
              "Every level of the selected ruleset. Preset characters are rebuilt at each level (keeping your edits), other characters only change their level"),
    "Enemy Save Bonus": (lambda ruleset: range(-2, 15), _enemy_save_bonus,
                         "The enemy's saving throw modifier for every ability, -2 to +14, only affects saving throw attacks"),
    "Attack Ability Score": (lambda ruleset: range(8, 21), _attack_ability_score,
                             "The ability score most of each character's attacks use, 8-20"),
}

@timeit
def run_sweep(characters, enemy, parameter, by_round=True, ruleset="bg3", num_rounds=10000, rounds_per_fight=None, **kwargs):
    """ Simulates a sweep over one of the SWEEP_PARAMETERS """
    values_for, apply, _ = SWEEP_PARAMETERS[parameter]
    cases = ((value, *apply(characters, enemy, value)) for value in values_for(ruleset or "bg3"))
    return simulate_sweep(cases, parameter, num_rounds=num_rounds, by_round=by_round, rounds_per_fight=rounds_per_fight, **kwargs)
