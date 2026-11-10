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

def halberd(**kwargs):
    return Attack(name="Halberd", two_handed=True, ability_stat="strength", damage="1d10", extra_damage_list=["1d4 force"], **kwargs)

def test_several_once_per_turn_pools():
    """ Sneak Attack (unlimited, the weapon's type) next to limited radiant smites: each pool keeps its own uses and damage type """
    rapier = Attack(name="Rapier", ability_stat="dexterity", damage="1d8", damage_type="piercing")
    character = Character(name="Rogue Paladin", level=8, dexterity=18, attacks=[rapier, rapier], once_per_turn_die_mod_list=["2d6"],
                          once_per_turn_extra=[{"name": "Divine Smite", "dice": ["3d8"], "uses_per_fight": 1.5, "damage_type": "radiant"}])
    enemy = Enemy(armor_class=16)
    check(character, enemy, 3)
    check(character, Enemy(armor_class=16, vulnerabilities=["radiant"]), 3)
    # Unlimited rounds: both pools go on the first hit
    both = expected_damage_per_round(character, enemy)
    from dataclasses import replace
    sneak_only = expected_damage_per_round(replace(character, once_per_turn_extra=[]), enemy)
    smite_only = expected_damage_per_round(replace(character, once_per_turn_die_mod_list=[]), enemy)
    plain = expected_damage_per_round(replace(character, once_per_turn_die_mod_list=[], once_per_turn_extra=[]), enemy)
    assert both - plain == pytest.approx((sneak_only - plain) + (smite_only - plain))
    # The smite is limited, the Sneak Attack isn't
    limited = expected_damage_per_round(character, enemy, 3)
    assert sneak_only < limited < both
    # Two limited pools: remaining uses treated as independent, still close to the simulation
    two = replace(character, once_per_turn_uses_per_fight=2)
    check(two, enemy, 4)

def test_savage_attacker_and_rerolls_reach_the_riders():
    """ BG3: Savage Attacker keeps the higher of two rolls on rider and once per turn dice of melee attacks too (bg3.wiki: 1d10 + 1d4 gains
        1.65 + 0.625), and Great Weapon Fighting rerolls them """
    enemy = Enemy(armor_class=1) # Always hits, except a 1
    base = Character(level=1, strength=10, attacks=[halberd(always_hit=True)])
    from dataclasses import replace
    savage = replace(base, savage_attacker=True, savage_attacker_per_die=True)
    assert expected_damage_per_round(savage, enemy) - expected_damage_per_round(base, enemy) == pytest.approx(1.65 + 0.625)
    # 5e Savage Attacker (the whole weapon roll twice) leaves the rider alone
    old = replace(base, savage_attacker=True)
    assert expected_damage_per_round(old, enemy) - expected_damage_per_round(base, enemy) == pytest.approx(1.65)
    gwf = replace(base, GWF=True)
    assert expected_damage_per_round(gwf, enemy) - expected_damage_per_round(base, enemy) == pytest.approx(0.8 + 0.5) # 1s and 2s rerolled on the d10 and the d4
    sneaky = Character(level=5, strength=18, savage_attacker=True, savage_attacker_per_die=True, GWF=True, once_per_turn_die_mod_list=["2d6"],
                       attacks=[halberd(), halberd()])
    check(sneaky, Enemy(armor_class=15))
    check(sneaky, Enemy(armor_class=15, resistances=["force"]), same_mean=False)
    # Thrown weapons: the weapon's own dice, not the riders
    javelin = Character(level=1, strength=10, savage_attacker=True, savage_attacker_per_die=True,
                        attacks=[Attack(type="thrown", damage="1d6", extra_damage_list=["1d4 force"], always_hit=True)])
    assert expected_damage_per_round(javelin, enemy) == pytest.approx(3.5 + 0.972 + 2.5, abs=0.001)

def test_lifedrinker_is_necrotic():
    blade = Attack(name="Shadow Blade", ability_stat="charisma", damage="2d8", damage_type="psychic", always_hit=True)
    warlock = Character(level=12, charisma=20, lifedrinker=True, attacks=[blade])
    plain, stone = Enemy(), Enemy(vulnerabilities=["psychic"])
    assert expected_damage_per_round(warlock, plain) == pytest.approx(9 + 5 + 5)
    assert expected_damage_per_round(warlock, stone) == pytest.approx(2 * (9 + 5) + 5) # The stone doubles the blade, not Lifedrinker
    assert expected_damage_per_round(warlock, Enemy(immunities=["necrotic"])) == pytest.approx(9 + 5)
    check(warlock, stone)

def test_a_fallback_can_have_its_own_uses():
    """ A quickened cantrip once the spell slots run out, for as long as the sorcery points last """
    spell = Attack(name="Fireball", type="spell", ability_stat="charisma", damage="8d6", always_hit=True, uses_per_fight=1)
    bolt = Attack(name="Fire Bolt", type="spell", ability_stat="charisma", damage="2d10", always_hit=True, fallback_for="Fireball")
    quick = Attack(name="Quickened Fire Bolt", type="spell", ability_stat="charisma", damage="2d10", always_hit=True, fallback_for="Fireball", uses_per_fight=1)
    character = Character(level=5, charisma=10, attacks=[spell, bolt, quick])
    # 4 rounds: Fireball, then Fire Bolt three times, quickened once
    assert expected_damage_per_round(character, Enemy(), 4) == pytest.approx((28 + 3 * 11 + 11) / 4)
    check(character, Enemy(), 4)
