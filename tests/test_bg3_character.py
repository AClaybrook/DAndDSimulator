""" BG3 character builder: compiled characters follow the Patch 8 rules, and match the prebuilt characters where they should """
import pytest

from bg3.abilities import point_buy_problems
from bg3.character import Bg3Character, caster_level, class_levels, compile_character, feat_opportunities
from computations.analytic import expected_damage_per_round
from computations.models import Enemy
from game_data.classes import build_character

ENEMY = Enemy(armor_class=15)
STR = {"strength": 15, "dexterity": 13, "constitution": 13, "intelligence": 8, "wisdom": 10, "charisma": 8}

def champion():
    return Bg3Character("Champion", scores=STR, bonus={"strength": 2, "constitution": 1}, classes=[["fighter", "Champion", 12]],
                        feats=["Great Weapon Master", "strength+2", "strength+2", "Savage Attacker"], fighting_styles=["Great Weapon Fighting"])

@pytest.mark.parametrize("level", [1, 3, 5, 8, 11, 12])
def test_champion_matches_the_preset(level):
    character, notes = compile_character(champion(), level)
    preset = build_character("fighter_gwm", level)
    assert not notes and not point_buy_problems(STR, {"strength": 2, "constitution": 1})
    assert expected_damage_per_round(character, ENEMY, 3) == pytest.approx(expected_damage_per_round(preset, ENEMY, 3))

def test_multiclass_levels_feats_and_spell_slots():
    sorcadin = Bg3Character(classes=[["paladin", "Oath of Vengeance", 6], ["sorcerer", "Draconic Bloodline", 6]])
    assert class_levels(sorcadin, 9) == {"paladin": 6, "sorcerer": 3}
    # Feats at class levels 4 (paladin) and 4 (sorcerer, character level 10)
    assert [lv for lv, _ in feat_opportunities(sorcadin)] == [4, 10]
    assert caster_level({"paladin": 5}, {}) == 3 and caster_level({"paladin": 6, "sorcerer": 6}, {}) == 9
    character, _ = compile_character(sorcadin, 12)
    assert character.once_per_turn_die_mod_list == ["5d8"] and character.advantage # Smite with 5th level slots, Vow of Enmity

def test_class_features():
    rogue = Bg3Character(scores={**STR, "dexterity": 15, "strength": 8}, classes=[["rogue", "Thief", 12]], routine="dual_wield")
    character, _ = compile_character(rogue, 5)
    assert character.once_per_turn_die_mod_list == ["3d6"]
    assert [a.offhand for a in character.attacks].count(True) == 2 # Fast Hands: a second off-hand attack
    assert not any(a.once_per_turn_eligible for a in character.attacks if a.offhand) # No Sneak Attack off hand in BG3
    monk, _ = compile_character(Bg3Character(classes=[["monk", "Way of the Open Hand", 12]], routine="unarmed"), 9)
    assert monk.attacks[0].damage == "1d8" and monk.attacks[0].extra_damage_list # Martial Arts d8 at 9, Manifestation of Body
    barbarian, _ = compile_character(Bg3Character(classes=[["barbarian", "Berserker", 2], ["fighter", "Champion", 10]]), 12)
    assert barbarian.raging and barbarian.rage_damage == 2 # Rage damage follows the barbarian level
    assert "Greatsword (Frenzy)" not in [a.name for a in barbarian.attacks] # Frenzy needs barbarian level 3

def test_cantrip_casters():
    sorlock = Bg3Character(scores={**STR, "charisma": 15, "strength": 8}, bonus={"charisma": 2, "constitution": 1},
                           classes=[["warlock", "The Fiend", 2], ["sorcerer", "Draconic Bloodline", 10]], routine="cantrip", cantrip="Eldritch Blast")
    character, notes = compile_character(sorlock, 10)
    assert character.agonizing_blast and [a.name for a in character.attacks].count("Eldritch Blast 3") == 1
    assert any(a.name.startswith("Quickened") for a in character.attacks) # Quickened Spell from sorcerer level 3
    # Elemental Affinity only for the ancestry's damage type, Eldritch Blast is force
    assert not any("3" in a.bonus_damage_die_mod_list for a in character.attacks)
    fire = Bg3Character(scores={**STR, "charisma": 15}, classes=[["sorcerer", "Draconic Bloodline", 12]], routine="cantrip", cantrip="Fire Bolt")
    assert compile_character(fire, 6)[0].attacks[0].bonus_damage_die_mod_list
    assert any("no damage features" in n for n in notes) # The Fiend

def test_round_trip():
    character = champion()
    assert Bg3Character.from_dict(character.to_dict()) == character
