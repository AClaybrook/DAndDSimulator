""" Tests for parsing and the attack/damage context calculations """
from dataclasses import replace
import pytest

from computations.models import (Attack, Character, Enemy, calculate_attack_and_damage_context, die_from_str,
                                 multiple_die_and_mod_from_list)

@pytest.mark.parametrize("die_str, expected", [
    ("2d6", (2, 6, 0)),
    ("2d6+3", (2, 6, 3)),
    ("1d4-1", (1, 4, -1)),
    ("d8", (1, 8, 0)),
    (" 1D10 ", (1, 10, 0)),
])
def test_die_from_str(die_str, expected):
    assert die_from_str(die_str) == expected

def test_multiple_die_and_mod_from_list():
    assert multiple_die_and_mod_from_list(["2d6+3", -1, "1d4", ""]) == ([2, 1], [6, 4], 2)
    # Placeholder dice from the UI are removed, even when next to each other
    assert multiple_die_and_mod_from_list(["0d4", "0d6", "1d8", "0"]) == ([1], [8], 0)
    assert multiple_die_and_mod_from_list("1d4,2") == ([1], [4], 2)

def test_replace_does_not_accumulate_bonuses():
    c = Character(bonus_attack_die_mod_list=["1d4", 1])
    c2 = replace(c, name="copy")
    assert c.attack_modifier("strength") == c2.attack_modifier("strength") == 0 + 2 + 1

def contexts(character, enemy=None):
    a, d = calculate_attack_and_damage_context(character, enemy or Enemy(armor_class=15))
    return a[0], d[0]

def test_melee_weapon_modifiers():
    c = Character(level=5, strength=18, GWM=True, GWF=True, attacks=[Attack(damage="2d6", two_handed=True, weapon_enhancement=1)])
    a, d = contexts(c)
    assert a.modifier == 4 + 3 - 5 + 1
    assert d.modifier == 4 + 10 + 1
    assert d.reroll_on == 2

def test_gwm_requires_heavy_weapon():
    c = Character(strength=16, GWM=True, attacks=[Attack(damage="1d10", two_handed=True, heavy=False)])
    a, d = contexts(c)
    assert a.modifier == 3 + 2
    assert d.modifier == 3

def test_sharpshooter_and_archery():
    c = Character(dexterity=16, sharpshooter=True, archery=True, attacks=[Attack(type="weapon (ranged)", ability_stat="dexterity", damage="1d8", weapon_enhancement=2)])
    a, d = contexts(c)
    assert a.modifier == 3 + 2 + 2 - 5 + 2
    assert d.modifier == 3 + 10 + 2

@pytest.mark.parametrize("attack_type", ["weapon (melee)", "weapon (ranged)"])
def test_offhand_attacks(attack_type):
    attack = Attack(type=attack_type, ability_stat="dexterity", offhand=True)
    _, d = contexts(Character(dexterity=16, attacks=[attack]))
    assert d.modifier == 0
    _, d = contexts(Character(dexterity=16, TWF=True, attacks=[attack]))
    assert d.modifier == 3

def test_rage_and_brutal_critical_scale_with_level():
    attack = Attack(damage="1d12", two_handed=True)
    _, d = contexts(Character(level=8, raging=True, brutal_critical=True, attacks=[attack]))
    assert d.modifier == 2
    assert d.crit_num_die == [1] and d.crit_damage_die == [12]
    _, d = contexts(Character(level=17, raging=True, brutal_critical=True, attacks=[attack]))
    assert d.modifier == 4
    assert d.crit_num_die == [3]

def test_spell_save_uses_enemy_save_modifier():
    c = Character(level=5, intelligence=18, attacks=[Attack(type="spell", ability_stat="intelligence", damage="8d6", saving_throw=True,
                                                             saving_throw_stat="dexterity")], bonus_attack_die_mod_list=["1d4"], advantage=True)
    enemy = Enemy(dexterity=14, dexterity_save=7)
    a, d = contexts(c, enemy)
    assert a.saving_throw
    assert a.difficulty_class == 8 + 3 + 4
    assert a.modifier == 7
    # Bless and advantage help attack rolls, not the enemy's saving throw
    assert a.num_die == [] and not a.advantage
    assert d.save_success_multiplier == 0.5

def test_enemy_saving_throw_defaults_to_ability_and_proficiency():
    enemy = Enemy(wisdom=14, challenge_rating=9, saving_throw_proficient=True)
    assert enemy.proficiency_bonus == 4
    assert enemy.saving_throw_modifier("wisdom") == 2 + 4
    assert Enemy(strength=8).saving_throw_modifier("strength") == -1

def test_resistance_vulnerability_and_immunity():
    sword = Attack(damage_type="slashing")
    magic_sword = Attack(damage_type="slashing", weapon_enhancement=1)
    fire_bolt = Attack(type="spell", damage_type="fire")
    enemy = Enemy(resistances=["slashing (nonmagical)"], vulnerabilities=["fire"], immunities=["poison"])
    assert enemy.damage_multiplier(sword) == 0.5
    assert enemy.damage_multiplier(magic_sword) == 1
    assert enemy.damage_multiplier(fire_bolt) == 2
    assert enemy.damage_multiplier(Attack(damage_type="poison")) == 0
    assert Enemy(resistance=True).damage_multiplier(fire_bolt) == 0.5

def test_class_feature_spell_bonuses():
    c = Character(charisma=18, intelligence=16, agonizing_blast=True, elemental_affinity=True, empowered_evocation=True,
                  attacks=[Attack(type="spell", ability_stat="charisma", damage="1d10")])
    _, d = contexts(c)
    assert d.modifier == 4 + 4 + 3

def test_from_dict_ignores_unknown_keys():
    c = Character.from_dict({"name": "Old", "strength": 18, "damage_on_miss": 0, "attacks": [{"name": "Axe", "damage": "1d12", "two_handed": True}]})
    assert c.strength == 18
    assert c.attacks[0].heavy # Older files without 'heavy' fall back to two_handed

def test_renamed_fields_still_load():
    """ Json files saved before 'proficent' was renamed to 'proficient' """
    character = Character.from_dict({"name": "Old", "attacks": [{"name": "Old", "proficent": False}]})
    enemy = Enemy.from_dict({"saving_throw_proficent": True})
    assert not character.attacks[0].proficient and enemy.saving_throw_proficient
