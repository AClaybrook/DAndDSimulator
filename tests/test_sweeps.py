""" Tests for the parameter sweeps """
import pytest

from components.sweeps import SWEEP_PARAMETERS, primary_stat, run_sweep
from computations.models import Attack, Character, Enemy
from game_data import RULESETS
from game_data.classes import build_character

FIGHTER = Character(name="Fighter", strength=16, attacks=[Attack(name="Greatsword", damage="2d6", two_handed=True)] * 2)
WIZARD = Character(name="Wizard", intelligence=16, attacks=[Attack(name="Fireball", type="spell", ability_stat="intelligence", damage="8d6",
                                                                  saving_throw=True, saving_throw_success_multiplier=0.5)])

def means(df, parameter, name):
    return df[df["Character"] == name].set_index(parameter)["mean"]

@pytest.mark.parametrize("parameter", SWEEP_PARAMETERS)
@pytest.mark.parametrize("by_round", [True, False])
def test_every_sweep_runs(parameter, by_round):
    df = run_sweep([FIGHTER, WIZARD, build_character("rogue_dual_wield", 3)], Enemy(), parameter, by_round=by_round, num_rounds=300)
    values, _, _ = SWEEP_PARAMETERS[parameter]
    assert set(df[parameter]) == set(values("bg3"))

def test_enemy_save_bonus_only_affects_saving_throws():
    df = run_sweep([FIGHTER, WIZARD], Enemy(), "Enemy Save Bonus", num_rounds=5000)
    wizard = means(df, "Enemy Save Bonus", "Wizard")
    assert wizard[-2] > wizard[14]
    fighter = means(df, "Enemy Save Bonus", "Fighter")
    assert fighter.max() - fighter.min() < 1.5 # Only noise

def test_attack_ability_score_sweep():
    assert primary_stat(WIZARD) == "intelligence" and primary_stat(Character()) == "strength"
    df = run_sweep([FIGHTER, WIZARD], Enemy(), "Attack Ability Score", num_rounds=5000)
    assert means(df, "Attack Ability Score", "Fighter")[20] > means(df, "Attack Ability Score", "Fighter")[8] + 3
    # A higher casting stat raises the spell save DC
    assert means(df, "Attack Ability Score", "Wizard")[20] > means(df, "Attack Ability Score", "Wizard")[8]

def test_level_sweep_uses_ruleset_cap():
    df = run_sweep([build_character("warlock_eb", 1, "5e")], Enemy(), "Level", ruleset="5e", num_rounds=200)
    assert df["Level"].max() == RULESETS["5e"]["max_level"]
