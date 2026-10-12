""" Validates the numerical simulation against exact analytic expectations """
import numpy as np
import pytest

from computations.analytic import attack_breakdown, expected_damage_per_round, hit_and_crit_chance
from computations.models import Attack, Character, Enemy
from computations.numerical_simulation import (rounds_to_kill, set_seed, simulate_rounds_from_characters,
                                               simulate_rounds_from_characters_multi_acs, simulate_rounds_to_kill)

NUM_ROUNDS = 200_000

def simulated_mean(character, enemy):
    _, df_by_rounds, _ = simulate_rounds_from_characters([character], enemy, num_rounds=NUM_ROUNDS, rng=set_seed(7))
    return df_by_rounds[0]["Damage"].mean()

def greatsword(**kwargs):
    return Attack(name="Greatsword", damage="2d6", two_handed=True, **kwargs)

CASES = {
    "basic": Character(level=5, strength=18, attacks=[greatsword(), greatsword()]),
    "gwm_gwf_adv_crit19": Character(level=12, strength=20, GWM=True, GWF=True, advantage=True, crit_on=19, attacks=[greatsword()] * 3),
    "bless_savage_halfling": Character(level=5, strength=16, savage_attacker=True, attack_reroll_on=1, bonus_attack_die_mod_list=["1d4"], attacks=[greatsword()] * 2),
    "barbarian": Character(level=9, strength=18, raging=True, brutal_critical=True, savage_attacks_half_orc=True, advantage=True, attacks=[Attack(damage="1d12", two_handed=True)] * 2),
    "sneak_attack": Character(level=5, dexterity=18, once_per_turn_die_mod_list=["3d6"], attacks=[Attack(ability_stat="dexterity"), Attack(ability_stat="dexterity", offhand=True)]),
    "magic_missile": Character(attacks=[Attack(type="spell", damage="1d4+1", always_hit=True)] * 3),
    "fireball": Character(level=5, intelligence=18, attacks=[Attack(type="spell", ability_stat="intelligence", damage="8d6", saving_throw=True, saving_throw_success_multiplier=0.5)]),
    "sacred_flame": Character(level=5, wisdom=18, attacks=[Attack(type="spell", ability_stat="wisdom", damage="2d8", saving_throw=True, saving_throw_success_multiplier=0)]),
    "miss_damage": Character(strength=16, bonus_miss_die_mod_list=["1d4", 1], attacks=[greatsword()]),
    "smite_crit_fishing": Character(level=11, strength=18, advantage=True, crit_on=19, once_per_turn_die_mod_list=["4d8"], once_per_turn_crit_only=True, attacks=[greatsword(), greatsword()]),
    "sneak_attack_ranged_only": Character(level=5, dexterity=18, once_per_turn_die_mod_list=["3d6"],
                                          attacks=[Attack(ability_stat="dexterity", once_per_turn_eligible=False), Attack(type="weapon (ranged)", ability_stat="dexterity", damage="1d8")]),
    "disadvantage": Character(strength=16, disadvantage=True, bonus_crit_die_mod_list=["1d8"], attacks=[greatsword()]),
}

@pytest.mark.parametrize("name", CASES)
def test_simulation_matches_analytic(name):
    character = CASES[name]
    enemy = Enemy(armor_class=16, dexterity_save=2)
    expected = expected_damage_per_round(character, enemy)
    # Half damage on a save rounds down in the simulation
    tolerance = 0.02 * expected + (0.3 if name == "fireball" else 0.05)
    assert simulated_mean(character, enemy) == pytest.approx(expected, abs=tolerance)

def test_hit_chances():
    assert hit_and_crit_chance(modifier=5, difficulty_class=15) == pytest.approx((0.55, 0.05))
    # A natural 1 always misses, a natural 20 always hits
    assert hit_and_crit_chance(modifier=30, difficulty_class=15) == pytest.approx((0.95, 0.05))
    assert hit_and_crit_chance(modifier=-30, difficulty_class=15) == pytest.approx((0.05, 0.05))
    p_adv, c_adv = hit_and_crit_chance(modifier=5, difficulty_class=15, advantage=True, crit_on=19)
    assert p_adv == pytest.approx(1 - 0.45**2)
    assert c_adv == pytest.approx(1 - 0.9**2)
    # Saving throws: enemy +2 vs DC 15 fails on 12 or lower
    assert hit_and_crit_chance(modifier=2, difficulty_class=15, saving_throw=True) == pytest.approx((0.6, 0))

def test_resistance_halves_damage():
    character = Character(strength=16, attacks=[greatsword()])
    normal = simulated_mean(character, Enemy(armor_class=10))
    resistant = simulated_mean(character, Enemy(armor_class=10, resistances=["slashing"]))
    assert resistant == pytest.approx(normal / 2, abs=0.35) # rounding down

def test_damage_reduction():
    character = Character(strength=16, attacks=[Attack(damage="1d4", always_hit=True)])
    _, df_by_rounds, _ = simulate_rounds_from_characters([character], Enemy(damage_reduction=5), num_rounds=1000)
    assert df_by_rounds[0]["Damage"].between(0, 2).all()

def test_single_attack_character_and_no_attacks():
    dfs, df_by_rounds, df_by_attacks = simulate_rounds_from_characters([Character(attacks=[greatsword()]), Character(name="Empty")], Enemy(), num_rounds=100)
    assert len(df_by_rounds[0]) == 100
    assert (df_by_rounds[1]["Damage"] == 0).all()

def test_seed_is_repeatable():
    character = CASES["basic"]
    a = simulate_rounds_from_characters([character], Enemy(), num_rounds=1000, rng=set_seed())[1][0]
    b = simulate_rounds_from_characters([character], Enemy(), num_rounds=1000, rng=set_seed())[1][0]
    assert a.equals(b)

def test_multi_ac_does_not_modify_enemy():
    enemy = Enemy(armor_class=17)
    df = simulate_rounds_from_characters_multi_acs([CASES["basic"]], enemy, armor_classes=[10, 20], num_rounds=1000)
    assert enemy.armor_class == 17
    assert df.loc[df["Armor Class"] == 10, "mean"].iloc[0] > df.loc[df["Armor Class"] == 20, "mean"].iloc[0]

def test_rounds_to_kill():
    assert (rounds_to_kill(np.full(100, 10), 25) == 3).all()
    assert (rounds_to_kill(np.zeros(100), 25, max_rounds=5) == 6).all()
    df = simulate_rounds_to_kill([CASES["basic"]], Enemy(hit_points=50), num_rounds=2000)
    assert df.iloc[:, 0].between(1, 31).all()

def test_attack_breakdown_columns():
    df = attack_breakdown(CASES["sneak_attack"], Enemy())
    assert list(df["Attack"]) == ["Attack", "Attack"]
    assert df["Expected"].iloc[0] > df["Expected"].iloc[1]

def test_column_stats_match_numpy():
    from computations.numerical_simulation import column_stats, describe
    rng = np.random.default_rng(0)
    for values in (rng.integers(-5, 60, size=1001, dtype='int32'), rng.integers(0, 3, size=10, dtype='int32'), np.array([7], dtype='int32')):
        expected = [values.mean(), *np.percentile(values, [0, 25, 50, 75, 100])]
        assert column_stats(values) == pytest.approx(expected)
        # A list of arrays is treated as one concatenated array
        assert column_stats([values[:3], values[3:]]) == pytest.approx(expected)
    floats = rng.random(100)
    assert column_stats(floats) == pytest.approx([floats.mean(), *np.percentile(floats, [0, 25, 50, 75, 100])])
    import pandas as pd
    df = pd.DataFrame({"a": rng.integers(0, 20, 500)})
    assert describe(df)["a"].tolist() == pytest.approx(df["a"].describe()[["mean", "min", "25%", "50%", "75%", "max"]].tolist())

def test_once_per_turn_options():
    enemy = Enemy(armor_class=15)
    base = dict(level=5, strength=18, once_per_turn_die_mod_list=["10d6"], attacks=[greatsword(), greatsword()])
    always = expected_damage_per_round(Character(**base), enemy)
    crit_only = expected_damage_per_round(Character(**base, once_per_turn_crit_only=True), enemy)
    never = expected_damage_per_round(Character(**{**base, "once_per_turn_die_mod_list": []}), enemy)
    assert never < crit_only < always
    ineligible = Character(**{**base, "attacks": [greatsword(once_per_turn_eligible=False)] * 2})
    assert expected_damage_per_round(ineligible, enemy) == pytest.approx(never)
