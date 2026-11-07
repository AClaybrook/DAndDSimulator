""" The exact damage distribution against the expected value and the simulation """
import numpy as np
import pytest

from computations.analytic import expected_damage_per_round
from computations.exact import Dist, binned, damage_per_round
from computations.models import Attack, Character, Enemy
from computations.numerical_simulation import simulate_rounds_from_characters

def check(character, enemy, rounds_per_fight=None, same_mean=True):
    """ same_mean: the expected value applies resistances without rounding, the simulation and the exact distribution round down """
    probs = damage_per_round(character, enemy, rounds_per_fight)
    assert probs.sum() == pytest.approx(1)
    if same_mean:
        assert np.arange(len(probs)) @ probs == pytest.approx(expected_damage_per_round(character, enemy, rounds_per_fight), abs=0.05)
    _, dfs, _ = simulate_rounds_from_characters([character], enemy, num_rounds=100_000, rng=np.random.default_rng(5), rounds_per_fight=rounds_per_fight)
    sim = np.bincount(dfs[0]["Damage"].to_numpy().astype(int), minlength=len(probs)) / len(dfs[0])
    size = max(len(probs), len(sim))
    gap = np.abs(np.pad(probs, (0, size - len(probs))) - np.pad(sim, (0, size - len(sim))))
    assert gap.max() < 0.006 and gap.sum() / 2 < 0.03 # Sampling noise of 100k rounds
    return probs

def test_single_attack_is_the_dice():
    probs = damage_per_round(Character(attacks=[Attack(damage="1d6", always_hit=True)], strength=10), Enemy())
    assert np.allclose(probs[1:7], 1 / 6) and probs[0] == 0

def test_matches_the_simulation():
    fighter = Character(name="Fighter", level=12, strength=20, attacks=[Attack(name="Greatsword", two_handed=True, ability_stat="strength", damage="2d6",
                                                                            type="weapon (melee)") for _ in range(3)])
    check(fighter, Enemy())
    from dataclasses import replace
    check(replace(fighter, GWM=True, advantage=True, GWF=True), Enemy(resistances=["slashing"]), same_mean=False)

def test_limited_resources_and_once_per_turn():
    from bg3.build import compile_build
    from bg3.presets import PRESETS
    for name in ["Paladin (Smite)", "Astarion (Assassin, dual wield)", "Gale (Evoker)"]:
        check(compile_build(PRESETS[name], "2"), Enemy(armor_class=16), 3)

def test_helpers():
    d = Dist([0.5, 0.5], 2) + Dist([0.5, 0.5])
    assert d.offset == 2 and np.allclose(d.probs, [0.25, 0.5, 0.25])
    assert d.mapped(lambda v: v // 2).offset == 1 and np.allclose(d.mapped(lambda v: v // 2).probs, [0.75, 0.25]) # 2 and 3 -> 1, 4 -> 2
    assert np.allclose(binned(np.array([0.1, 0.2, 0.3, 0.4]), 0, 2, 2), [0.3, 0.7])
