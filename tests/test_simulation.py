""" Validates the numerical simulation against exact analytic expectations """
from bg3.character import Bg3Character, compile_character
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
    "bg3_savage_attacker_per_die": Character(level=5, strength=18, savage_attacker=True, savage_attacker_per_die=True, GWF=True, attacks=[greatsword()] * 2),
    "raging_monk_unarmed": Character(level=5, strength=16, raging=True, tavern_brawler=True, attacks=[Attack(type="unarmed", damage="1d6", damage_type="bludgeoning")] * 3),
    "typed_extra_damage": Character(level=5, strength=18, advantage=True, attacks=[greatsword(extra_damage_list=["1d4 fire", "2 acid"])] * 2),
    "typed_extra_vs_immune_and_vulnerable": Character(level=5, strength=18, attacks=[greatsword(extra_damage_list=["1d6 poison", "1d4 radiant"])] * 2),
}

# Poison immune and radiant vulnerable, the main slashing damage is unaffected
RIDER_ENEMY = {"immunities": ["poison"], "vulnerabilities": ["radiant"]}

@pytest.mark.parametrize("name", CASES)
def test_simulation_matches_analytic(name):
    character = CASES[name]
    enemy = Enemy(armor_class=16, dexterity_save=2, **(RIDER_ENEMY if name == "typed_extra_vs_immune_and_vulnerable" else {}))
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

FIGHT_ROUNDS = 240_000 # Divisible by every rounds per fight used below, so every simulated fight is complete
FIGHT_CASES = {
    "action_surge": (3, Character(level=5, strength=18, attacks=[greatsword()] * 2 + [greatsword(uses_per_fight=0.75)] * 2)),
    "limited_smites": (4, Character(level=5, strength=18, once_per_turn_die_mod_list=["3d8"], once_per_turn_uses_per_fight=1.5, attacks=[greatsword()] * 2)),
    "crit_fishing_one_smite": (3, Character(level=11, strength=18, advantage=True, once_per_turn_die_mod_list=["4d8"], once_per_turn_crit_only=True,
                                            once_per_turn_uses_per_fight=1, attacks=[greatsword()] * 2)),
    "quickened_blasts": (3, Character(level=5, charisma=18, agonizing_blast=True,
                                      attacks=[Attack(type="spell", ability_stat="charisma", damage="1d10", bonus_damage_die_mod_list=["1d6"])] * 2
                                      + [Attack(name="Quickened", type="spell", ability_stat="charisma", damage="1d10", uses_per_fight=1.25)] * 2)),
    "limited_fireball_and_sneak": (5, Character(level=5, dexterity=18, intelligence=18, once_per_turn_die_mod_list=["3d6"], once_per_turn_uses_per_fight=2,
                                                attacks=[Attack(ability_stat="dexterity"), Attack(type="spell", ability_stat="intelligence", damage="8d6", saving_throw=True,
                                                                                                    saving_throw_success_multiplier=0.5, uses_per_fight=1)])),
    # BG3 builder: Heart of the Storm damage on hits and misses, Star Map Guiding Bolts falling back to a cantrip plus Luminous Arrow
    "storm_sorcerer_lightning_bolt": (4, compile_character(Bg3Character(classes=[["sorcerer", "Storm Sorcery", 12]], routine="cantrip",
                                                                         cantrip="Shocking Grasp", spell="Lightning Bolt"), 8)[0]),
    "circle_of_stars": (4, compile_character(Bg3Character(classes=[["druid", "Circle of Stars", 12]], routine="cantrip", cantrip="Produce Flame"), 5)[0]),
}

@pytest.mark.parametrize("name", FIGHT_CASES)
def test_fight_simulation_matches_analytic(name):
    rounds_per_fight, character = FIGHT_CASES[name]
    enemy = Enemy(armor_class=16, dexterity_save=2)
    expected = expected_damage_per_round(character, enemy, rounds_per_fight)
    _, df_by_rounds, _ = simulate_rounds_from_characters([character], enemy, num_rounds=FIGHT_ROUNDS, rng=set_seed(11), rounds_per_fight=rounds_per_fight)
    tolerance = 0.02 * expected + (0.3 if "fireball" in name or "lightning_bolt" in name else 0.05)
    assert df_by_rounds[0]["Damage"].mean() == pytest.approx(expected, abs=tolerance)
    # Limits only lower damage compared to unlimited resources
    assert expected <= expected_damage_per_round(character, enemy) + 1e-9

def test_limited_resources_front_load_damage():
    from computations.numerical_simulation import fight_damage
    rounds_per_fight, character = FIGHT_CASES["action_surge"]
    by_round = fight_damage(character, Enemy(armor_class=15), 20_000, rounds_per_fight, rng=set_seed(3)).mean(axis=1)
    assert by_round[0] > 1.25 * by_round[1] and by_round[1] == pytest.approx(by_round[2], rel=0.05)

def test_rounds_to_kill_uses_fights_for_limited_resources():
    enemy = Enemy(armor_class=15, hit_points=40)
    burst = Character(name="Burst", strength=18, level=5, attacks=[greatsword()] * 2 + [greatsword(uses_per_fight=1)] * 6)
    df = simulate_rounds_to_kill([burst], enemy, num_rounds=5000, max_rounds=10)
    # Eight attacks in the first round usually kill a 40 hp enemy straight away
    assert (df["Burst"] == 1).mean() > 0.5

def test_damage_per_fight_outputs():
    from computations.numerical_simulation import simulate_fights
    from components.plots import fight_export, fight_summary, generate_fight_plot
    characters = [FIGHT_CASES["action_surge"][1], CASES["basic"]]
    characters[0] = Character(**{**characters[0].__dict__, "name": "Surge"})
    fights = simulate_fights(characters, Enemy(), num_fights=500, rounds_per_fight=4)
    assert {name: damage.shape for name, damage in fights.items()} == {"Surge": (4, 500), "Character": (4, 500)}
    assert len(generate_fight_plot(fights).data) == 2 and fight_summary(fights)
    export = fight_export(fights)
    assert len(export) == 1000 and list(export.columns[:3]) == ["Name", "Fight", "Total"]
    assert (export["Total"] == export[[f"Round {r}" for r in range(1, 5)]].sum(axis=1)).all()

FIRE_BOLT = Attack(name="Fire Bolt", type="spell", ability_stat="intelligence", damage="2d10", fallback_for="Fireball")
FIREBALL = Attack(name="Fireball", type="spell", ability_stat="intelligence", damage="8d6", saving_throw=True, saving_throw_success_multiplier=0.5, uses_per_fight=1.5)
FALLBACK_CASES = {
    "fireball_then_fire_bolt": (4, Character(level=5, intelligence=18, attacks=[FIREBALL, FIRE_BOLT])),
    "assassin": (3, Character(level=5, dexterity=18, once_per_turn_die_mod_list=["3d6"], first_round_advantage=True, first_round_auto_crit=True,
                              attacks=[Attack(ability_stat="dexterity"), Attack(ability_stat="dexterity", offhand=True)])),
    "dread_ambusher": (3, Character(level=5, dexterity=18, archery=True, first_round_advantage=True,
                                    attacks=[Attack(type="weapon (ranged)", ability_stat="dexterity", damage="1d8")] * 2
                                    + [Attack(name="Dread Ambusher", type="weapon (ranged)", ability_stat="dexterity", damage="1d8", bonus_damage_die_mod_list=["1d8"], uses_per_fight=1)])),
}

@pytest.mark.parametrize("name", FALLBACK_CASES)
def test_fallback_and_first_round_match_analytic(name):
    rounds_per_fight, character = FALLBACK_CASES[name]
    enemy = Enemy(armor_class=15, dexterity_save=2)
    expected = expected_damage_per_round(character, enemy, rounds_per_fight)
    _, df_by_rounds, _ = simulate_rounds_from_characters([character], enemy, num_rounds=FIGHT_ROUNDS, rng=set_seed(5), rounds_per_fight=rounds_per_fight)
    tolerance = 0.02 * expected + (0.3 if "fireball" in name or "lightning_bolt" in name else 0.05)
    assert df_by_rounds[0]["Damage"].mean() == pytest.approx(expected, abs=tolerance)

def test_fallback_attacks():
    from computations.analytic import attacks_per_round
    rounds_per_fight, character = FALLBACK_CASES["fireball_then_fire_bolt"]
    # One attack per round: Fireball while it lasts, then Fire Bolt
    assert attacks_per_round(character, rounds_per_fight) == pytest.approx(1.0)
    # Without fights the limited attack is made every round, so the fallback never is
    dfs, _, _ = simulate_rounds_from_characters([character], Enemy(), num_rounds=1000)
    assert dfs[0].groupby("Attack", observed=True)["Damage"].sum()["Fire Bolt"] == 0
    assert attacks_per_round(character) == 1.0
    # A fallback for an unlimited attack is never made
    unlimited = Character(attacks=[Attack(name="Sword"), Attack(name="Backup", fallback_for="Sword")])
    assert expected_damage_per_round(unlimited, Enemy(), 3) == pytest.approx(expected_damage_per_round(Character(attacks=[Attack(name="Sword")]), Enemy(), 3))

def test_first_round_conditions_front_load():
    from computations.numerical_simulation import fight_damage
    rounds_per_fight, character = FALLBACK_CASES["assassin"]
    by_round = fight_damage(character, Enemy(armor_class=15), 20_000, rounds_per_fight, rng=set_seed(2)).mean(axis=1)
    assert by_round[0] > 1.5 * by_round[1]

def test_typed_extra_damage_resistance_is_separate():
    """ Fire resistance halves only the fire part of a flaming greatsword """
    character = Character(strength=16, attacks=[greatsword(extra_damage_list=["1d6 fire"])])
    plain = expected_damage_per_round(Character(strength=16, attacks=[greatsword()]), Enemy(armor_class=10))
    fire = expected_damage_per_round(character, Enemy(armor_class=10)) - plain
    resistant = expected_damage_per_round(character, Enemy(armor_class=10, resistances=["fire"]))
    assert resistant == pytest.approx(plain + fire / 2)
    assert simulated_mean(character, Enemy(armor_class=10, resistances=["fire"])) == pytest.approx(resistant, abs=0.35) # fire rounds down

def test_per_attack_damage_reroll_matches_great_weapon_fighting():
    """ A weapon that rerolls 1s and 2s (BG3 items) is the same as Great Weapon Fighting on that weapon """
    gwf = Character(strength=16, GWF=True, attacks=[greatsword()])
    item = Character(strength=16, attacks=[greatsword(damage_reroll_on=2)])
    enemy = Enemy(armor_class=12)
    assert expected_damage_per_round(item, enemy) == pytest.approx(expected_damage_per_round(gwf, enemy))
    assert simulated_mean(item, enemy) == pytest.approx(expected_damage_per_round(item, enemy), abs=0.1)

def test_per_die_savage_attacker_beats_whole_set():
    """ Keeping the higher of each die is better than the higher total of the set (2d6: 8.94 vs 8.37) """
    from computations.analytic import expected_dice
    assert expected_dice([2], [6], advantage=True, per_die=True) == pytest.approx(2 * 161 / 36)
    assert expected_dice([2], [6], advantage=True, per_die=True) > expected_dice([2], [6], advantage=True)

def test_hits_crit_matches_analytic():
    """ Melee attacks against a paralysed target: advantage and every hit is a crit """
    character = Character(level=5, strength=18, attacks=[Attack(damage="2d6", advantage=True, hits_crit=True)] * 2)
    enemy = Enemy(armor_class=16)
    expected = expected_damage_per_round(character, enemy)
    _, df_by_rounds, _ = simulate_rounds_from_characters([character], enemy, num_rounds=200_000, rng=set_seed(5))
    assert df_by_rounds[0]["Damage"].mean() == pytest.approx(expected, rel=0.02)
    plain = Character(level=5, strength=18, attacks=[Attack(damage="2d6", advantage=True)] * 2)
    assert expected > expected_damage_per_round(plain, enemy) * 1.4
